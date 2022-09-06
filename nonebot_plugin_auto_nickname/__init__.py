from random import choice
from services.log import logger
import time
from utils.utils import scheduler, get_bot


__zx_plugin_name__ = "时间群昵称"
__plugin_version__ = 0.1
__plugin_author__ = "YiJiuChow"

lz_list = ["绿头鸡", "鸡脖哥", "鸡脖王", "鸡脖哥哥"]

@scheduler.scheduled_job(
    "interval",
    minutes=1
)
async def _():
    try:
        bot = get_bot()
        gl = await bot.call_api("get_group_list")
        gl = [g["group_id"] for g in gl]
        timestr = time.strftime("%a %b %d %H:%M %Y CST", time.localtime())
        for g in gl:
            await bot.set_group_card(group_id=g, user_id=bot.self_id, card=f"大头 {timestr}")
        await bot.set_group_card(group_id=774331907, user_id=1626303708, card=choice(lz_list)) 
    except Exception as e:
        logger.error(f"error: {e}")

@scheduler.scheduled_job(
    "cron",
    hour=6,
    minute=0,
)
async def _():
    try:
        bot = get_bot()
        timestr = time.strftime("%a %b %d %Y CST", time.localtime())
        await bot.call_api("set_qq_profile", nickname=f"大头 {timestr}")
    except Exception as e:
        logger.error(f"set_qq_profile error: {e}")