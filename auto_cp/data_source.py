from actions.wiseLoginService import wiseLoginService
from actions.autoSign import AutoSign
from actions.collection import Collection
from actions.workLog import workLog
from actions.pushKit import pushKit
from actions.utils import Utils
from time import sleep
import traceback, os


def main():
    Utils.log("自动化任务开始执行")
    config = Utils.getYmlConfig()
    push = pushKit(config['notifyOption'])
    httpProxy = config['httpProxy'] if 'httpProxy' in config else ''
    for user in config['users']:
        # Utils.log(f"10s后开始执行用户{user['user'].get('username','默认用户')}的任务")
        # sleep(10)

        # 执行任务
        try:
            msg = working(user, httpProxy)
            ret = True
        except Exception as e:
            msg = f'[{e}]\n{traceback.format_exc()}'
            ret = False

        # 根据任务执行情况(ret和msg)进行推送和记录
        ntm = Utils.getTimeStr()
        with open(f"success.info", 'w') as f:
            if 'SUCCESS' in msg:
                f.write("SUCCESS")
            else:
                f.write("FAILED")
        if ret == True:
            # 此处需要注意就算提示成功也不一定是真的成功，以实际为准
            Utils.log(msg)
            if 'SUCCESS' in msg:
                msg = push.sendMsg(
                    '今日校园签到成功通知',
                    '服务器(V%s)于%s尝试签到成功!' % (config['Version'], ntm),
                    user['user'])
            else:
                msg = push.sendMsg(
                    '今日校园签到异常通知', '服务器(V%s)于%s尝试签到异常!\n异常信息:%s' %
                    (config['Version'], ntm, msg), user['user'])
        else:
            Utils.log("Error:" + msg)
            msg = push.sendMsg(
                '今日校园签到失败通知', '服务器(V%s)于%s尝试签到失败!\n错误信息:%s' %
                (config['Version'], ntm, msg), user['user'])
        Utils.log(msg)
    Utils.log("自动化任务执行完毕")


def working(user, httpProxy):
    Utils.log('正在获取登录地址')
    wise = wiseLoginService(user['user'], httpProxy)
    Utils.log('开始尝试登录账号')
    wise.login()
    sleep(1)
    # 登陆成功，通过type判断当前属于 信息收集、签到、查寝
    # 信息收集
    # elif user['user']['type'] in [1, 2, 3]:
    # 以下代码是签到的代码
    Utils.log('开始执行签到任务')
    sign = AutoSign(wise, user['user'])
    sign.getUnSignTask()
    sleep(1)
    sign.getDetailTask()
    sign.fillForm()
    sleep(1)
    msg = sign.submitForm()
    return msg

main()