import time
from MyLang.myinterpreter import interprete, execute
from MyLang.metadata import get_current_expr, RunEnvironment
import threading

DEBUG = False


# 脚本运行线程类
class ScriptThread(threading.Thread):
    # 是否有脚本策略正在运行
    script_running = False

    def __init__(self, engine, code):
        super(ScriptThread, self).__init__()
        self.engine = engine
        self.code = code
        self.contract = self.engine.current_contract
        self.is_stop = False

    def run(self):
        # 修改脚本运行状态
        self.__class__.script_running = True
        # 假如无合约信息
        if not self.contract:
            self.engine.write_log("运行失败：当前无合约信息！", show_line=False)
            self.__class__.script_running = False
            return

        self.engine.write_log("开始运行策略......", show_line=False)
        # 策略环境准备
        # 定时器自动更新running_bar
        self.engine.unlock_getNew_all()
        # 每次启动清空trade_full_order
        self.engine.trade_full_order = []
        # 清空行号对应的订单id
        self.engine.line_oder_id = {}
        # 每次启动初始化挂单的函数表库
        self.engine.unsuccessful_oder_init()
        # 初始化trade_agian 的 交易运行次数, 判断是否存在trade_again函数
        if RunEnvironment.is_limit_trade_again:
            self.engine.trade_again_init_in_restart_strategy()
        else:
            self.engine.trade_again_time_list = []
        # 调用画图函数绘制信号

        self.engine.draw_sig()
        try:
            # 调用解释器
            interprete(self.engine, self.code)
        except Exception as e:
            self.engine.write_log('语法错误: {}'.format(str(e)), show_line=False)
            self.__class__.script_running = False
            return

        # 循环执行脚本
        while not self.is_stop:
            try:
                # 从运行环境中执行脚本策略
                execute()
                # 暂时设定为一秒执行一次
                time.sleep(1)
            except Exception as e:
                if DEBUG:
                    # 停止线程运行
                    self.stop()
                    # 修改脚本运行状态
                    self.__class__.script_running = False
                    raise e
                if get_current_expr():
                    self.engine.write_log("{}运行错误,错误行数:{}, 错误原因如下:".format(
                        str(get_current_expr()), get_current_expr().lineno), show_line=False)
                else:
                    self.engine.write_log("运行错误，错误原因如下:", show_line=False)
                self.engine.write_log(str(e), show_line=False)
                break
        # 停止线程运行
        self.stop()
        # 修改脚本运行状态
        self.__class__.script_running = False
        return

    def stop(self):
        self.is_stop = True
