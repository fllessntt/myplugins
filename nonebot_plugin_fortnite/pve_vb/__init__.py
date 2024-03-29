import asyncio

from nonebot.plugin import on_command
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent

from utils.utils import scheduler, get_bot
from services.log import logger
from configs.path_config import IMAGE_PATH
from utils.message_builder import image
from utils.manager import group_manager

from .data_source import update_daily_vb

__zx_plugin_name__ = "vb图"
__plugin_usage__ = """
usage：
    堡垒之夜PVE
    指令：
        vb图, v币图 不区分字母大小写
""".strip()
__plugin_type__ = ("堡批专属",)
__plugin_cmd__ = ["vb图"]
__plugin_des__ = "STW(PVE) 每日VB图"
__plugin_task__ = {"pve":"堡垒之夜PVE推送"}


pve = on_command("vb图", aliases={"VB图", "V币图", "v币图"}, block=True)
@pve.handle()
async def _():
    await pve.finish(message=image(IMAGE_PATH / "fn_stw.png"))

update_pve = on_command("更新vb图", block=True, permission=SUPERUSER)

@update_pve.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    img_name = await update_daily_vb()
    await update_pve.finish(message="手动更新 STW(PVE) vb图成功" + image(IMAGE_PATH / img_name))

@scheduler.scheduled_job(
    "cron",
    hour=8,
    minute=5,
)
async def _():
    # msg = None
    while True:
        try:
            img_name = await update_daily_vb()
            msg = image(IMAGE_PATH / img_name)
            break
        except Exception as e:
            logger.error(f"PVE vb图更新错误 {e}")
            # ssl错误, 重新更新vb图
            await asyncio.sleep(10)
            continue
    bot = get_bot()
    gl = await bot.get_group_list()
    gl = [g["group_id"] for g in gl]
    for g in gl:
        if group_manager.check_group_task_status(g, 'pve'):
            await bot.send_group_msg(group_id=g, message=msg)
        