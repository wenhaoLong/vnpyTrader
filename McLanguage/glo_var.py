"""
liuzhu
设计一些需要用到的全局变量
"""

# -*- coding: utf-8 -*-

str_replace_trade_again = """
    if self.editor_engine.iteration_count == 1:
        self.editor_engine.trade_again_times["trade_again_{}"] = {}
        self.editor_engine.trade_again_times["trade_again_{}"] = 1
    self.editor_engine.trade_again_times["trade_again_{}"] -= 1
if self.editor_engine.trade_again_times["trade_again_{}"] >= 1:
    pass
"""

def _init():  # 初始化
    global _global_dict
    _global_dict = {}
    _global_dict["trade_again_round"] = 0
    _global_dict["trade_again_str"] = str_replace_trade_again

def set_value(key, value):
    """ 定义一个全局变量 """
    _global_dict[key] = value


def get_value(key, defValue=None):
    """ 获得一个全局变量,不存在则返回默认值 """

    try:
        return _global_dict[key]
    except KeyError:
        pass
