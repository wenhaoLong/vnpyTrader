# coding:utf-8

script_template = """
import time
import threading
from queue import Queue
from vnpy.app.editor_manager import EditorEngine

class ScriptThread(threading.Thread):

    def __init__(self, engine: EditorEngine, tick_queue: Queue):
        super(ScriptThread, self).__init__()
        self.editor_engine = engine
        self.tick_queue = tick_queue
        self.contract = self.editor_engine.current_contract
        # 获取线程运行了多少个循环 liuzhu
        self.editor_engine.iteration_count = 0

    def run(self):
        if not self.contract:
            msg = "没有当前合约，请连接CTP，并点击选择合约！"
            self.editor_engine.write_log(msg)
       
        while self.editor_engine.strategy_active: 
            # if self.tick_queue.full():
            #     tick = self.tick_queue.get()
            #     msg = f"最新行情, {tick}"
            #     self.editor_engine.write_log(msg)
                self.editor_engine.iteration_count = self.editor_engine.iteration_count + 1
                if self.editor_engine.iteration_count == 100:
                    self.editor_engine.iteration_count = 2
                if self.editor_engine.trade_again_times["trade_again_1"] >= 1:
                # 麦语言脚本插入位置
"""