from typing import List
from nonebot.params import CommandArg
from nonebot.plugin import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message

from utils.message_builder import image
from utils.image_utils import pic2b64
from utils.utils import is_number, scheduler
from utils.data_utils import _init_rank_graph
from configs.path_config import FONT_PATH
from services.log import logger

from fortnite_api import StatsImageType, FortniteAPI, TimeWindow, BrPlayerStats
from PIL import Image, ImageFont, ImageDraw
from io import BytesIO

import httpx, re, json, asyncio

__zx_plugin_name__ = "战绩"
__plugin_usage__ = """
usage：
    堡垒之夜战绩查询
    指令：
        战绩 id
        生涯战绩 id
        群昵称(名片)设置为
        ["id:", "id：", "id "]三选一(别带引号), 不区分大小写 + 你的游戏昵称
        发送 战绩或生涯战绩 可快速查询战绩
""".strip()
__plugin_type__ = ("堡批专属",)
__plugin_cmd__ = ["战绩"]
__plugin_des__ = "堡垒之夜战绩查询"


api = FortniteAPI(api_key = "f3f4e682-346e-45b1-8323-fe77aaea2a68", run_async = True)
bpr = {} # dict
file_path = "bpr.json"

with open(file_path, mode='r') as jr:
    # battle_pass_top # dict
    bpr = json.load(jr) 

season_stat = on_command("战绩", block=True)
@season_stat.handle()
async def _(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    nickname = args.extract_plain_text()
    if nickname is None or nickname == '':
        card = event.sender.card 
        if card is not None and card[0:3].casefold() in ["id:", "id：", "id ",]:
            nickname = card[3:len(card)] # 昵称替换为群名片id
        else:
            await season_stat.finish(message=
            "群昵称(名片)设置为\n['id:', 'id：', 'id '](三选一, 不区分大小写和中英文冒号)\n加上你的游戏昵称, 发送 战绩 可快速查询当前赛季战绩")
    try:
        playerstats = await api.stats.fetch_by_name(nickname, time_window=TimeWindow.SEASON, image=StatsImageType.ALL)
        await update_level(playerstats, nickname)
        url = playerstats.image_url
        result = None
        # 匹配带中文昵称
        if re.search(r'[\u2E80-\u9FFF]', nickname, flags=0):
            result = write_chinese_nickname(url=url, nickname=nickname)
    except Exception as e:
        result = str(e)
        if "public" in result:
            result = "战绩未公开"
        elif "exist" in result:
            result = "用户不存在"
        elif "match" in result:
            result = "该玩家当前赛季没有进行过任何对局"
        elif "timed out" in result:
            result = "请求超时, 请稍后再试"
        await season_stat.finish(message=result)
    logger.info("战绩查询成功")
    if result is not None:
        result = image(b64=pic2b64(result))
    else:
        result = image(url)
    await season_stat.finish(message=result)

lifetime_stat = on_command("生涯战绩", block=True)
@lifetime_stat.handle()
async def _(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    nickname = args.extract_plain_text()
    if nickname is None or nickname == '':
        card = event.sender.card 
        if card is not None and card[0:3].casefold() in ["id:", "id：", "id ",]:
            nickname = card[3:len(card)] # 昵称替换为群名片id
        else:
            await lifetime_stat.finish(message=
            "群昵称(名片)设置为\n['id:', 'id：', 'id '](三选一, 不区分大小写和中英文冒号)\n加上你的游戏昵称, 发送 生涯战绩 可快速查询生涯战绩")
    try:
        playerstats = await api.stats.fetch_by_name(nickname, image=StatsImageType.ALL)
        await update_level(playerstats, nickname)
        url = playerstats.image_url
        result = None
        # 匹配带中文昵称
        if re.search(r'[\u2E80-\u9FFF]', nickname, flags=0):
            result = write_chinese_nickname(url=url, nickname=nickname)
    except Exception as e:
        result = str(e)
        if "public" in result:
            result = "战绩未公开"
        elif "exist" in result:
            result = "用户不存在"
        elif "match" in result:
            result = "该玩家没有进行过任何对局"
        elif "timed out" in result:
            result = "请求超时, 请稍后再试"
        await lifetime_stat.finish(message=result)
    logger.info("战绩查询成功")
    if result is not None:
        result = image(b64=pic2b64(result))
    else:
        result = image(url)
    await lifetime_stat.finish(message=result)


battle_pass_ranking = on_command("bpr", aliases={"季卡排行", "季卡等级排行", "卷王排行"}, block=True)
@battle_pass_ranking.handle()
async def _(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    msg = args.extract_plain_text().strip()
    top_num = 10 # 排行数, 默认为10
    if is_number(msg) and (int(msg) >= 3 or int(msg) <= 50):
        top_num = int(msg)
    # 排序, 按照等级(value)排序, reverse 倒序, 返回一个List[tuple]
    sorted_bpr = sorted(bpr.items(), key = lambda item:item[1])
    if top_num > len(sorted_bpr):
        top_num = len(sorted_bpr)
    # 取出top_num个数据
    sorted_bpr = sorted_bpr[len(sorted_bpr)-top_num: len(sorted_bpr)]
    # bpr_str = "\n".join(f"top{sorted_bpr.index(i)+1} id:{i[0]} level:{i[1]}" for i in sorted_bpr)
    nn_list = [i[0] for i in sorted_bpr]
    level_list = [i[1] for i in sorted_bpr]
    im = await asyncio.get_event_loop().run_in_executor(
        None, _init_rank_graph, "季卡排行(查询战绩可收录id)", nn_list, level_list
    )
    await battle_pass_ranking.finish(message=image(b64=im.pic2bs4()))

del_ranking = on_command("dr", block=True)
@del_ranking.handle()
async def _(args: Message = CommandArg()):
    regex_str = args.extract_plain_text().strip()
    for nickname in bpr:
        if regex_str in nickname:
            del bpr[nickname]
            await del_ranking.finish(message=f"成功将 {nickname} 移出排行")
    await del_ranking.finish(message="没有匹配到任何id")


def write_chinese_nickname(url: str, nickname: str):
    response = httpx.get(url)
    im = Image.open(BytesIO(response.content))
    draw = ImageDraw.Draw(im) 
    # 覆盖
    draw.rectangle(xy=(30, 90, 420, 230), fill="#012e57")
    # 填充昵称
    cn_len = (len(nickname.encode("utf-8")) - len(nickname.encode("GBK")))
    nickname_len = (len(nickname) - cn_len + 0.0) / 2 + cn_len
    font_size = 30
    X = max((225 - nickname_len * font_size / 2), 0)
    font = "HWXingKai.ttf"
    ttfont = ImageFont.truetype(str(FONT_PATH / font), font_size)
    draw.text((X, 150), f'{nickname}', fill = "#fafafa", font=ttfont)
    return im

# 更新季卡等级
async def update_level(stat: BrPlayerStats, nickname: str):
    cache_level = bpr.get(nickname)
    if cache_level is None or cache_level != stat.battle_pass.level:
        bpr[nickname] = stat.battle_pass.level


# 定时更新季卡等级, 每2小时更新一次
@scheduler.scheduled_job('interval', hours=2)
async def _():
    for nickname in bpr:
        try:
            stat = await api.stats.fetch_by_name(nickname, image=StatsImageType.ALL)
            await update_level(stat, nickname)  
        except Exception as e:
            if "timed out" in str(e):
                continue
            del bpr[nickname]       
    with open(file_path, mode='w+') as jw:
        jw.write(json.dumps(bpr, indent=4, ensure_ascii=False))
        logger.info("季卡等级更新完毕")


