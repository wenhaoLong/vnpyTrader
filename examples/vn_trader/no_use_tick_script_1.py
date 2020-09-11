from time import sleep
from vnpy.app.script_trader import ScriptEngine


def run(engine: ScriptEngine):
    """
    脚本策略的主函数说明：
    1. 唯一入参是脚本引擎ScriptEngine对象，通用它来完成查询和请求操作
    2. 该函数会通过一个独立的线程来启动运行，区别于其他策略模块的事件驱动
    3. while循环的维护，请通过engine.strategy_active状态来判断，实现可控退出

    脚本策略的应用举例：
    1. 自定义篮子委托执行执行算法
    2. 股指期货和一篮子股票之间的对冲策略
    3. 国内外商品、数字货币跨交易所的套利
    4. 自定义组合指数行情监控以及消息通知
    5. 股票市场扫描选股类交易策略（龙一、龙二）
    6. 等等~~~
    """
    # 持续运行，使用strategy_active来判断是否要退出程序
    while engine.strategy_active:
        # 轮询获取行情

        current_contract = engine.get_current_contract()
        if not current_contract:
            print("没有合约信息，请连接CTP！")
            break

        current_tick = engine.get_tick(current_contract.symbol)
        tick_list = engine.get_current_tick_list()
        if current_tick:
            if tick_list:
                top_tick = tick_list[len(tick_list)-1]
                msg = f"最新行情, {engine.get_new_tick_flag()}"
                engine.write_log(msg)
            else:
                msg = f"最新行情, {top_tick}"
                engine.write_log(msg)
        else:
            msg = f"最新行情, {current_tick}"
            engine.write_log(msg)
            break
        # 等待3秒进入下一轮
        sleep(0.001)
