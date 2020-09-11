import threading
from queue import Queue
from vnpy.app.script_trader import ScriptEngine


class ScriptThread(threading.Thread):
    def __init__(self, engine: ScriptEngine, tick_queue: Queue):
        super(ScriptThread, self).__init__()
        self.engine = engine
        self.tick_queue = tick_queue
        self.contract = self.engine.current_contract

    def run(self):
        if not self.contract:
            msg = "没有当前合约，请连接CTP！"
            self.engine.write_log(msg)

        while self.engine.strategy_active:
            if self.tick_queue.full():
                pass
               # 这里放你的python转化的脚本
