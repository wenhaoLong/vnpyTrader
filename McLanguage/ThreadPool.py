from concurrent.futures import ThreadPoolExecutor
import time


class MyThreadPool(object):
    def __init__(self, thread_num=5):
        self.excutor = ThreadPoolExecutor(max_workers=thread_num)

    # 执行脚本
    def execute_script(self, func_, args):
        task = self.excutor.submit(func_, args)
        return task
