from MyLang.metadata import RunEnvironment
from MyLang.myparser import parse


def interprete(engine, code):
    # 设置运行引擎
    RunEnvironment.run_engine = engine
    # 设置当前运行代码
    RunEnvironment.run_code = code
    # 清空变量表、运行栈、历史栈
    RunEnvironment.run_vars.clear()
    RunEnvironment.run_stack.clear()
    RunEnvironment.run_history.clear()
    # 清空运行运行环境中的交易信号
    RunEnvironment.run_trade.clear()
    # 将环境中的标志位复位
    RunEnvironment.is_limit_trade_again = False
    # 清空运行时的日志值
    RunEnvironment.run_log_value.clear()
    # 解析代码,得到运行语法树
    RunEnvironment.run_ast = parse(code)


def execute():
    # 从运行环境中开始执行
    RunEnvironment.run_ast.exec()