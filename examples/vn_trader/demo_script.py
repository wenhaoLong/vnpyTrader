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
                tick = self.tick_queue.get()
                msg = f"最新行情, {tick}"
                self.engine.write_log(msg)
                # bar_list = self.engine.get_bars(self.contract.symbol, "20190901", "20190930", "d")
                # print(bar_list)
                # tick_list = self.engine.get_tick_list()
                # print(tick_list)
