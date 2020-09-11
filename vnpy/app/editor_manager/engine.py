""""""
import sys
import os
import re
import importlib
from pathlib import Path
# from jqdatasdk import *
from typing import List, Any
from queue import Queue
from datetime import datetime, timedelta
import time
from vnpy.trader.utility import get_folder_path

import numpy as np
from pandas import DataFrame

from MyLang.metadata import get_current_expr

# @ liuzhu
# @ 20191002
# 使用apschedule模块进行时间调度，按时间撤销order
# from apscheduler.schedulers.blocking import BlockingScheduler
# import uuid
# trader_sched = BlockingScheduler()
# trader_sched.start()

# @ liuzhu
# @ 20191003
# apschedule函数雕塑时间出现问题，改用Qtimer

import traceback

from PyQt5.QtCore import QTimer

from vnpy.event import Event, EventEngine
from vnpy.trader.event import (
    EVENT_TICK,
    EVENT_ORDER,
    EVENT_TRADE,
    EVENT_POSITION,
    EVENT_ACCOUNT,
    EVENT_CONTRACT,
    EVENT_CURRENT_CONTRACT,
    EVENT_CURRENT_SYMBOL,
    EVENT_CURRENT_TICK,
    EVENT_SCATTER,
    EVENT_MA,
    EVENT_LOG,
    EVENT_INFO,
    EVENT_NEW_K,

)
from vnpy.trader.engine import BaseEngine, MainEngine
from vnpy.trader.constant import Direction, Offset, OrderType, Interval, Status, Exchange
from vnpy.trader.object import (
    OrderRequest,
    TickData,
    OrderData,
    TradeData,
    PositionData,
    AccountData,
    ContractData,
    LogData,
    HistoryRequest,
    CancelRequest,
    BarData,
    MaData
)

# 2019/9/29 LongWenHao

from vnpy.trader.database.initialize import init
from vnpy.trader.setting import get_settings
from vnpy.trader.utility import ArrayManager

# from jqdatasdk import *

APP_NAME = "EditorManager"

EVENT_EDITOR_LOG = "eEditorLog"

from vnpy.app.editor_manager.ui.param_dialog import ParamDialog
from MyLang.metadata import RunEnvironment, get_current_expr
from MyLang.metadata import Expr, Variable, Number
from McLanguage.ScriptThread import ScriptThread
import numpy as np
import talib
import datetime as dt
from datetime import datetime
from vnpy.trader.jqdata import jqdata_client

class EditorEngine(BaseEngine):
    """"""

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        """"""
        super().__init__(main_engine, event_engine, APP_NAME)

        self.strategy_active = False
        self.strategy_thread = None
        self.tick_queue = Queue(1)
        self.current_bars = self.main_engine.get_current_bars()
        self.current_contract: ContractData = None
        self.start_time = None
        # 设置启动定时器
        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.start()
        self.timer.timeout.connect(self.onTimerOut)
        # 用来记录交易函数需要运行的次数
        self.trade_count = {'BK': 0, 'SK': 0, 'SP': 0, 'BP': 0}
        # 记录线程循环次数
        self.iteration_count = 0
        # 用来存储bk的订单信息
        self.bk_list = []
        # liuzhu 存放执行了交易函数后的订单，以及成功交易的订单
        self.trade_oder = []
        self.trade_successful_oder = []
        # 存储所有的委托号
        self.trade_full_order = []
        # 用来存储trade_again运行次数
        self.trade_again_times = {'trade_again_1': 1}
        self.dt_ix_map = {}
        self.isNew = False
        self.running_bar = None
        self.draw = False
        # 是否获得新的最后一根k线
        self.getNew_mutex_list = [1]
        self.ix = -1

        # 记录trade_again 出现次数
        self.trade_again_time_list = []
        self.trade_count_list = []
        self.trade_again_init = []

        # 用来记录编辑器的使用版本
        self.editor_version = '2.0'

        # 记录时回测环境还是实盘环境
        self.env = "real"  # "real" 实盘环境  "backtest" 回测环境
        self.backtest_order_record = []
        # current_bars = self.main_engine.get_current_bars()
        # for ix, bar in enumerate(current_bars):
        #     self.dt_ix_map[bar.datetime] = ix

        # 处理未成交的订单
        self.unsuccessful_oder = {'BK': {}, 'SK': {}, 'SP': {}, 'BP': {}}

        # 记录每一行的信号状态
        self.line_oder_id = {}

        # @author hengxincheung
        # @date 2019-10-15
        # @note 增加指向自身的引用 self.editor_engine = self
        self.editor_engine = self
        self.editor_box = None

        self.tick = None
        self.crossMap = {}

        self.register_event()

    def lock_getNew(self):
        """
        对定时器更新k线进行上锁,允许多重上锁，多重上锁之后必须所有锁全开才能使用
        :return:
        """
        self.getNew_mutex_list.append(1)

    def unlock_getNew(self):
        """
        对定时器更新k线进行解锁,允许多重上锁，多重上锁之后必须所有锁全开才能使用
        :return:
        """
        if len(self.getNew_mutex_list):
            self.getNew_mutex_list.pop()

    def unlock_getNew_all(self):
        """
        对getNew的所有锁进行清空，一般不要使用
        :return:
        """
        self.getNew_mutex_list.clear()

    def is_mutex_getNew(self):
        """
        判断是否getNew是否上锁，是否可以定时器更新k线，False可以更新，True不能更新
        :return:
        """
        if len(self.getNew_mutex_list):
            return True
        else:
            return False

    def onTimerOut(self):
        if self.draw == True:
            settings = get_settings("database.")
            database_manager: "BaseDatabaseManager" = init(settings=settings)
            current_contract = self.get_current_contract(use_df=False)
            trades = database_manager.load_trades_by_symbol(current_contract.symbol)
            # current_contract = self.get_current_position(use_df=False)

            positions = self.get_all_positions(use_df=False)

            # 乘数
            unit = self.unit()

        #     current_contract = self.get_current_contract(use_df=False)
        #     current_bars = self.main_engine.get_current_bars()
        #     for ix, bar in enumerate(current_bars):
        #         self.dt_ix_map[bar.datetime] = ix
        #     try:
        #         settings = get_settings("database.")
        #         database_manager: "BaseDatabaseManager" = init(settings=settings)
        #         current_contract = self.get_current_contract(use_df=False)
        #         trades = database_manager.load_trades_by_symbol(current_contract.symbol)
        #         scatter = {}
        #
        #         # print(self.dt_ix_map)
        #         # for bar in current_bars:
        #         if len(trades) > 0:
        #             num = 1
        #             for trade in trades:
        #                 Time = trade.datetime[0:4] + "-" + trade.datetime[4:6] + "-" + trade.datetime[
        #                                                                                6:8] + trade.datetime[
        #                                                                                       8:11] + \
        #                        trade.datetime[11:14] + ":00"
        #                 if trade.datetime >= self.strategy_start_time\
        #                         and trade.symbol == current_contract.symbol \
        #                         and datetime.strptime(Time, "%Y-%m-%d %H:%M:%S") in self.dt_ix_map:
        #                     print(trade)
        #                     if int(self.dt_ix_map[datetime.strptime(
        #                         Time, "%Y-%m-%d %H:%M:%S")]) in scatter:
        #                         num += 1
        #                     else:
        #                         num = 1
        #                     scatter[int(self.dt_ix_map[datetime.strptime(
        #                         Time, "%Y-%m-%d %H:%M:%S")])] = {"price": trade.price, "offset": trade.offset,
        #                                                          "direction": trade.direction,"num":num}
        #
        #         event = Event(EVENT_SCATTER, scatter)
        #         self.event_engine.put(event)
        #     except:
        #         pass
        # 使用定时器对k线进行定时更新
        self.k_line_update_timeout()
        # 交易函数cancel_oder ，判断是否撤单
        self.bk_timeout()
        # 给交易函数添加交易成功的记录
        self.oder_check_ok_timeout()

    def process_new_kLine(self, event):

        self.isNew = True

    def draw_sig(self):
        # 针对撤单函数，刚开始记录一次启动时间
        self.time = time.strftime('%H:%M:%S', time.localtime(time.time()))
        # 保持与trade.datetime格式一致，因为需要比较
        self.strategy_start_time = time.strftime('%Y%m%d %H:%M:%S', time.localtime(time.time()))

        self.draw = True

    def stop_draw(self):
        self.draw = False

    def k_line_update_timeout(self):
        # 首次获得最后一根k线
        if self.running_bar == None and self.is_mutex_getNew() == False:
            if len(self.main_engine.get_current_bars()) > 0:
                self.running_bar = self.main_engine.get_current_bars()[-1]
        if self.is_mutex_getNew() == False:
            current_bars = self.main_engine.get_current_bars()
            if len(current_bars):
                new_bar = current_bars[-1]
                if self.running_bar != new_bar:
                    self.running_bar = new_bar

    def oder_check_ok_timeout(self):
        """
        定时器检查交易成功的记录
        :return:
        """
        try:

            if len(self.trade_oder):
                del_list = []
                for index, oder_id in enumerate(self.trade_oder):
                    if index > len(self.trade_oder):
                        break
                    oder = self.get_order(oder_id)
                    if oder is None:
                        continue
                    if oder.status == Status.ALLTRADED:
                        del_list.append(index)
                        self.trade_successful_oder.append(oder)
                        # 如果有策略正在运行则加入到运行策略列表中
                        if ScriptThread.script_running:
                            RunEnvironment.run_trade.append(oder)
                        # 获取行数
                        line_num = None
                        for key in self.line_oder_id.keys():
                            value = self.line_oder_id[key]
                            print("key: ")
                            print("value")
                            print("oder_id")
                            if value == oder_id:
                                line_num = key
                                break
                        self.write_log("成功委托<合约号:{},价格:{:.2f},手数:{},信号:({})({})>".format(
                            oder.symbol, oder.price, oder.volume, oder.offset.value, oder.direction.value),
                            line_num=line_num)
                    else:
                        pass
                if len(del_list) and len(self.trade_oder):
                    for i in del_list:
                        if i > len(self.trade_oder) - 1:
                            continue
                        self.trade_oder.pop(i)
        except Exception:
            traceback.print_exc()

    def bk_timeout(self):
        try:
            # print('timeout_test')
            if len(self.bk_list):
                del_list = []
                for index, oder in enumerate(self.bk_list):
                    if index > len(self.bk_list):
                        break
                    oder_id = oder['oder_id']
                    oder_time_out = oder['timeout']
                    order = self.get_order(oder_id)
                    if order is None:
                        return
                    if order.status == Status.ALLTRADED:
                        del_list.append(index)
                        # bk_list.pop(index)
                    elif oder_time_out > datetime.now():
                        pass
                    elif oder_time_out <= datetime.now():
                        self.cancel_order(oder_id)
                        del_list.append(index)
                    else:
                        pass
                for i in del_list:
                    self.bk_list.pop(i)
        except:
            traceback.print_exc()

    def register_event(self):
        """"""
        self.event_engine.register(EVENT_CURRENT_TICK, self.process_current_tick_event)
        self.event_engine.register(EVENT_CURRENT_CONTRACT, self.process_current_contract_event)
        # self.event_engine.register(EVENT_CURRENT_SYMBOL, self.process)
        self.event_engine.register(EVENT_NEW_K, self.process_new_kLine)

    def process_current_tick_event(self, event: Event):
        tick = event.data
        # print(tick)
        if self.tick_queue.empty():
            self.tick_queue.put(tick, block=False)

    def process_current_contract_event(self, event: Event):
        self.current_contract = event.data

    # 0
    def log(self, msg, skip_repeat="True"):
        # self.write_log("line {}:{}".format(get_current_expr().lineno, str(get_current_expr())))
        # self.write_log("表达式类型为:{}".format(type(msg)))
        expr_str = str(msg)
        if isinstance(msg, Variable):
            expr_value = msg.value[-1]
        else:
            expr_value = msg.exec()
        if isinstance(skip_repeat, Expr):
            skip_repeat = skip_repeat.exec()
        # 运行时日志值的key的格式是: 行号_表达式
        log_key = "{}_{}".format(msg.lineno, expr_str)
        # 如果曾经日志过，需要进行判断是否一样
        if log_key in RunEnvironment.run_log_value.keys():
            log_value = RunEnvironment.run_log_value[log_key]
            if skip_repeat == 'True' and expr_value == log_value:
                return
        # 记录当前的值
        RunEnvironment.run_log_value[log_key] = expr_value
        if isinstance(expr_value, (int, float)):
            self.write_log("{} --> {:.2f}".format(expr_str, expr_value))
        else:
            self.write_log("{} --> {}".format(expr_str, expr_value))

    def money_re(self):
        """
        实际权益
        @ author liuzhu
        @ time 2020.1.13
        :return:
        """
        account = self.get_current_account()
        res = account.balance
        return res

    def money_re_av(self):
        """
        实际可用资金
        @ author yangjintao
        @ time 2020.1.13
        :return:
        """
        account = self.get_current_account()
        res = account.available
        return res

    def money_th(self):

        current_contract = self.get_current_contract(use_df=False)

        account = self.main_engine.get_current_account()

        settings = get_settings("database.")
        database_manager: "BaseDatabaseManager" = init(settings=settings)

        trades = database_manager.load_trades_by_symbol(current_contract.symbol)
        """
        理论权益
        @ author longwenhao
        @ time 2020.1.14
        :return:
        """
        initMoney = float(self.initmoney())
        if len(trades) == 0:
            self.write_log("MONEY_TH理论权益：成交记录为0")
            return initMoney
        # current_contract = self.get_current_position(use_df=False)

        positions = self.get_all_positions(use_df=False)
        pnl = 0
        for p in positions:
            # 浮动盈亏
            pnl += float(p.pnl)

        fee = 0
        # 乘数
        unit = self.unit()
        for trade in trades:
            if trade.datetime >= self.strategy_start_time:
                # 手续费
                # 如果绝对值大于0，优先采用绝对值手续费
                if self.editor_box.param_dialog.commission_abs > 0:
                    fee = float(self.editor_box.param_dialog.commission_abs) * float(trade.volume)
                # 否则，使用百分比手续费
                elif self.editor_box.param_dialog.commission > 0:
                    fee = float(trade.price) * float(self.editor_box.param_dialog.commission) * float(
                        trade.volume) * float(self.unit())

        return initMoney + account.closePnl + account.floatPnl - account.commission

    def money_th_av(self):
        """
        理论可用资金 = 理论权益 - 保证金
        保证金 = 保证金率*价格*手数*乘数
        @author hengxincheung
        @time 2020-02-05
        :return: 理论可用资金
        """
        # 获取乘数
        multiplier = self.unit()
        # 得到保证金率
        deposit = self.editor_box.param_dialog.deposit
        # 计算理论权益
        money_th_av = self.money_th()
        # 加载数据库
        settings = get_settings("database.")
        database_manager: "BaseDatabaseManager" = init(settings=settings)
        # 得到当前合约
        current_contract = self.current_contract
        # 根据合约号查询交易记录
        trades = database_manager.load_trades_by_symbol(current_contract.symbol)
        # 如果交易数量为0，则直接返回理论权益
        if len(trades) == 0:
            return money_th_av
        # 遍历交易记录
        for trade in trades:
            # 只计算策略开始之后产生的交易
            if trade.datetime >= self.strategy_start_time:
                # 根据委托类型进行计算
                # 如果是BK 或 SK
                if trade.direction == Direction.LONG and trade.offset == Offset.OPEN or \
                        trade.direction == Direction.SHORT and trade.offset == Offset.OPEN:
                    # 保证金 = 合约价格 * 合约乘数 * 手数 * 保证金比例
                    # 减去保证金
                    money_th_av -= trade.price * multiplier * trade.volume * deposit
                # 如果是BP 或 SP
                elif trade.direction == Direction.LONG and trade.offset == Offset.CLOSE or \
                        trade.direction == Direction.SHORT and trade.offset == Offset.CLOSE:
                    # 加回保证金
                    money_th_av += trade.price * multiplier * trade.volume * deposit
        return money_th_av

    # 撤单 LWH
    def cancel(self, line_num):
        all_orders = self.main_engine.get_all_orders()
        if line_num.exec() == 0:
            for order in all_orders:
                if order.traded == 0 and order.status == Status.NOTTRADED:
                    print(order)
                    req = CancelRequest(
                        orderid=order.orderid,
                        symbol=order.symbol,
                        exchange=order.exchange
                    )
                    req = order.create_cancel_request()
                    self.main_engine.cancel_order(req, order.gateway_name)
                    self.write_log("已撤销")
        else:
            order_id = self.line_oder_id[str(line_num)]
            order = self.get_order(order_id)
            if order is None:
                return
            if order and order.traded == 0 and order.status == Status.NOTTRADED:
                req = CancelRequest(
                    orderid=order.orderid,
                    symbol=order.symbol,
                    exchange=order.exchange
                )
                req = order.create_cancel_request()

                self.main_engine.cancel_order(req, order.gateway_name)
                self.write_log("已撤销")

        # for order in all_orders:
        #     if order.traded == 0 and order.status == Status.NOTTRADED:
        #         print(order)
        #         req = CancelRequest(
        #             orderid=order.orderid,
        #             symbol=order.symbol,
        #             exchange=order.exchange
        #         )
        #         req = order.create_cancel_request()
        #         print(order)
        #         self.main_engine.cancel_order(req, order.gateway_name)

    def get_jq_bars(self, symbol: str, interval: str, count: int):

        """"""
        contract = self.main_engine.get_current_contract()
        if not contract:
            return []
        req = HistoryRequest(
            symbol=contract.symbol,
            count=count,
            exchange=contract.exchange,
            interval=Interval(interval),
            start="",
            end="",
        )
        bars_list, bars_df = jqdata_client.query_history(req)

        return bars_list

        # 1
        # 第1期

    def h(self):
        now = datetime.now()
        # return self.running_bar.low_price
        current_contract = self.get_current_contract(use_df=False)
        # current_bars = self.main_engine.get_current_bars()
        current_bars = self.get_jq_bars(current_contract.symbol, str(self.editor_box.param_dialog.period) + "m", 300)
        if current_bars[0].interval.value == "1m" and current_bars[-1].datetime.minute != now.minute:
            current_bars = current_bars[:-1]
        else:
            if current_bars[-1].datetime.minute % int(self.editor_box.param_dialog.period) != 0:
                current_bars = current_bars[:-1]

        # self.tick = self.main_engine.get_current_tick(current_contract)
        # if self.tick:
        #     return max(self.tick.high_price,current_bars[-1].high_price)
        # else:
        #     return current_bars[-1].high_price
        high_bars = []
        for b in current_bars[-int(self.editor_box.param_dialog.period):]:
            high_bars.append(b.high_price)
        return max(high_bars)
        # if current_bars:
        #     return current_bars[-1].high_price
        # else:
        #     return 0

        # 1
        # 第1期

    def l(self):
        now = datetime.now()
        # return self.running_bar.low_price
        current_contract = self.get_current_contract(use_df=False)
        # current_bars = self.main_engine.get_current_bars()
        current_bars = self.get_jq_bars(current_contract.symbol, str(self.editor_box.param_dialog.period) + "m", 300)
        if current_bars[0].interval.value == "1m" and current_bars[-1].datetime.minute != now.minute:
            current_bars = current_bars[:-1]
        else:
            if current_bars[-1].datetime.minute % int(self.editor_box.param_dialog.period) != 0:
                current_bars = current_bars[:-1]
        # self.tick = self.main_engine.get_current_tick(current_contract)
        # if self.tick:
        #     return min()
        # else:
        low_bars = []
        for b in current_bars[-int(self.editor_box.param_dialog.period):]:
            low_bars.append(b.low_price)
        return max(low_bars)
        # current_bars = self.main_engine.get_current_bars()
        # if current_bars:
        #     return current_bars[-1].low_price
        # else:
        #     return 0

        # 1
        # 第1期

    def o(self):

        now = datetime.now()
        current_contract = self.get_current_contract(use_df=False)
        # current_bars = self.main_engine.get_current_bars()
        current_bars = self.get_jq_bars(current_contract.symbol, str(self.editor_box.param_dialog.period) + "m", 300)

        if current_bars[0].interval.value == "1m" and current_bars[-1].datetime.minute != now.minute:
            current_bars = current_bars[:-1]
        else:
            if current_bars[-1].datetime.minute % int(self.editor_box.param_dialog.period) != 0:
                current_bars = current_bars[:-1]
        bars = self.get_jq_bars(current_contract.symbol, "1m", 300)
        # print(current_bars[-1])

        m = 0
        for b in bars:
            m += 1
            if b.datetime.minute == current_bars[-1].datetime.minute and b.datetime.hour == current_bars[
                -1].datetime.hour:
                break
        if m < len(bars) and m != 0:
            if bars[m].open_price:
                return bars[m].open_price

        # self.tick = self.main_engine.get_current_tick(current_contract)
        # if self.tick:
        #     return self.tick.open_price
        # else:
        #     return 0
        # current_bars = self.main_engine.get_current_bars()
        # if current_bars:
        #     return current_bars[-1].open_price
        # else:
        #     return 0

        # 1
        # 第1期

    def c(self):
        now = datetime.now()

        current_contract = self.get_current_contract(use_df=False)
        current_bars = self.get_jq_bars(current_contract.symbol, str(self.editor_box.param_dialog.period) + "m", 300)
        self.tick = self.main_engine.get_current_tick(current_contract)
        if current_bars[0].interval.value == "1m" and current_bars[-1].datetime.minute != now.minute:
            current_bars = current_bars[:-1]
        else:
            if current_bars[-1].datetime.minute % int(self.editor_box.param_dialog.period) != 0:
                current_bars = current_bars[:-1]
        if self.tick:
            return self.tick.last_price
        else:
            return current_bars[-1].close_price
        # current_bars = self.main_engine.get_current_bars()
        # # print(current_bars[-1])
        # if current_bars:
        #     return current_bars[-1].close_price
        # else:
        #     return 0

    # 1
    # 第1期
    def v(self):
        # return self.running_bar.volume
        current_contract = self.get_current_contract(use_df=False)
        self.tick = self.main_engine.get_current_tick(current_contract)
        if self.tick:
            return self.tick.volume
        else:
            return 0
        # current_bars = self.main_engine.get_current_bars()
        # if current_bars:
        #     return current_bars[-1].volume
        # else:
        #     return 0

    def h_list(self):
        current_bars = self.main_engine.get_current_bars()
        highs = []
        for bar in current_bars:
            highs.append(bar.high_price)
        return highs

    def o_list(self):
        current_bars = self.main_engine.get_current_bars()
        opens = []
        for bar in current_bars:
            opens.append(bar.open_price)
        return opens

    def l_list(self):
        current_bars = self.main_engine.get_current_bars()
        lows = []
        for bar in current_bars:
            lows.append(bar.low_price)
        return lows

    def c_list(self):
        current_bars = self.main_engine.get_current_bars()
        closes = []
        for bar in current_bars:
            closes.append(bar.close_price)
        return closes

    def high_list(self):
        current_bars = self.main_engine.get_current_bars()
        highs = []
        for bar in current_bars:
            highs.append(bar.high_price)
        return highs

    def open_list(self):
        current_bars = self.main_engine.get_current_bars()
        opens = []
        for bar in current_bars:
            opens.append(bar.open_price)
        return opens

    def low_list(self):
        current_bars = self.main_engine.get_current_bars()
        lows = []
        for bar in current_bars:
            lows.append(bar.low_price)
        return lows

    def close_list(self):
        current_bars = self.main_engine.get_current_bars()
        closes = []
        for bar in current_bars:
            closes.append(bar.close_price)
        return closes

    # 2
    # 第1期
    def ask1(self):

        """
        获取tick卖一价
        :return:
        """
        current_tick = self.get_tick(self.get_current_contract().symbol)
        return current_tick.ask_price_1

    # 3
    # 第1期
    def ask1vol(self):
        current_tick = self.get_tick(self.get_current_contract().symbol)
        return current_tick.ask_volume_1

    # 4
    # 第1期
    def bid1(self):
        current_tick = self.get_tick(self.get_current_contract().symbol)
        return current_tick.bid_price_1

    # 5
    # 第1期
    def bid1vol(self):
        current_tick = self.get_tick(self.get_current_contract().symbol)
        return current_tick.bid_volume_1

    def _is_close_(self):
        # try:
        #     # order = self.get_order(self.trade_oder[-1])
        #     order = self.get_all_orders()[-1]
        #     if order.status == Status.REJECTED or order.status == Status.SUBMITTING:
        #         tick = self.get_tick(self.get_current_contract().symbol)
        #         print(tick.datetime)
        #         print(self.running_bar.datetime)
        #         if tick.datetime == self.running_bar.datetime:
        #             return True
        #         else:
        #             return False
        #     else:
        #         return False
        # except:
        #     traceback.print_exc()
        #     return True
        # try:
        #     tick = self.get_tick(self.get_current_contract().symbol)
        #     print(f"tick.time : {tick.datetime}")
        #     print(f"self.runningbar.time: {self.running_bar.datetime}")
        #     tick_datetime_str = tick.datetime.strftime("%Y-%m-%d %H:%M")
        #     runningbar_datetime_str = self.running_bar.datetime.strftime("%Y-%m-%d %H:%M")
        #     print(f"tick_datetime_str : {tick_datetime_str}")
        #     print(f"runningbar_datetime_str: {runningbar_datetime_str}")
        #     if tick.datetime == self.running_bar.datetime:
        #         return True
        #     else:
        #         return False
        #
        # except:
        #     traceback.print_exc()
        #     return True
        """
        liuzhu
        2020.4.3
        通过当前时间和tick时间的差值来比较，如果时间差相差5s，则说明收盘
        """
        try:
            error_max = 4  # seconds
            tick = self.get_tick(self.get_current_contract().symbol)
            tick_datetime_str = tick.datetime.strftime("%Y-%m-%d %H:%M:%S")
            now_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            time_delta = datetime.strptime(tick_datetime_str, "%Y-%m-%d %H:%M:%S") - datetime.strptime(now_time_str,
                                                                                                       "%Y-%m-%d %H:%M:%S")
            # print(f'ticktime:{tick_datetime_str}')
            # print(f'{now_time_str}')
            # print(f'{time_delta}')
            # if time_delta.seconds > -error_max and time_delta < error_max:
            if timedelta(seconds=error_max) > time_delta > timedelta(days=-1, hours=23, minutes=59,
                                                                     seconds=(60 - error_max)):
                return False
            else:
                return True
        except:
            traceback.print_exc()

    def state(self, line_num):
        """
        SUBMITTING = "提交中" 1
        NOTTRADED = "未成交"  2
        PARTTRADED = "部分成交" 3
        ALLTRADED = "全部成交"  4
        CANCELLED = "已撤销"   5
        REJECTED = "拒单"   6
        :param line_num:
        :return:
        """
        try:
            order_id = self.line_oder_id[str(line_num)]
            if order_id == None:
                print('该行交易没有执行过')
            order = self.get_order(order_id)
            if order is None:
                self.write_log("查询委托号 ({}) 失败".format(order_id))
                return None
            if order.status == Status.SUBMITTING:
                return 1
            elif order.status == Status.NOTTRADED:
                return 2
            elif order.status == Status.PARTTRADED:
                return 3
            elif order.status == Status.ALLTRADED:
                return 4
            elif order.status == Status.CANCELLED:
                return 5
            elif order.status == Status.REJECTED:
                return 6
        except:
            traceback.print_exc()

    # 6
    def bk(self, n, price, is_cancel=None):
        # self.log("param:@type{}@value{}, @type{}@value{}, @type{}@value{}".format(
        #     type(n), n, type(price), price, type(is_cancel), is_cancel))
        if self.editor_version == '2.0':
            n = n.exec()
            price = price.exec()
        if self.env == "real":
            # 新版本编辑器的trade_again 功能实现
            run_flag = 0
            if len(self.trade_again_time_list):
                line_num = get_current_expr().lineno
                if self.trade_again_time_list[-1] < line_num:
                    run_flag = 1
                else:
                    for i in range(len(self.trade_again_time_list)):
                        if self.trade_again_time_list[i] > line_num:
                            if self.trade_count_list[i] > 0:
                                run_flag = 1
                                self.trade_count_list[i] -= 1
                                break
                            else:
                                break
            else:
                run_flag = 1

            # 做挂单判断
            unsucc_oder_flag = False
            if self.unsuccessful_oder['BK'] == {} or not self.if_line_in_trade_fun(fun_name='BK'):
                unsucc_oder_flag = True
            else:
                line_num_if_success = get_current_expr().lineno
                oder_id = self.unsuccessful_oder['BK'][str(line_num_if_success)]
                oder = self.get_order(oder_id)
                if oder is not None:
                    if oder.status == Status.NOTTRADED:
                        unsucc_oder_flag = False
                    else:
                        unsucc_oder_flag = True

            if run_flag == 1 and unsucc_oder_flag == True and not self._is_close_():
                oder_id_res = self.send_order(self.get_current_contract(), price, n, Direction.LONG, Offset.OPEN)
                # 将所有交易的id存入trade_oder
                self.trade_oder.append(oder_id_res)
                self.trade_full_order.append(oder_id_res)
                bk_oder_dic = {'oder_id': oder_id_res, 'timeout': datetime.now() + timedelta(seconds=5)}

                # 记录交易的单号，以便判断未成交的订单
                line_num_record = get_current_expr().lineno
                self.unsuccessful_oder['BK'][str(line_num_record)] = oder_id_res

                # 记录每行行号对应的订单id
                self.line_oder_id[str(line_num_record)] = oder_id_res

                # 等待交易服务器返回结果，结果不为“提交中”
                # 等待交易服务器返回结果
                count_time = 0
                stat_flag = 1  # 交易服务器判断flag
                while True:
                    res_instance = self.get_order(oder_id_res)
                    if res_instance == None and count_time < 3:
                        count_time += 1
                        time.sleep(1)

                    elif count_time >= 3:
                        # 交易服务器未返回结果，不需要检测状态
                        stat_flag = 0
                        self.write_log("BK交易函数未得到实例或订单被撤销")
                        break

                    else:
                        break

                # 等待状态不为提交中
                # 如果交易服务器并没有实例，就不需要检测
                if stat_flag == 0:
                    pass
                else:
                    count_time = 0
                    while True:
                        order = self.get_order(oder_id_res)
                        if order is None:
                            count_time += 1
                            continue
                        res_instance_stat = order.status
                        if res_instance_stat == Status.SUBMITTING and count_time < 3:
                            count_time += 1
                            time.sleep(1)
                        elif count_time >= 3:
                            self.write_log("BK函数一直处于提交中或被服务器拒单")
                            break
                        else:
                            break

                # TODO 大小写敏感
                if is_cancel == "cancel_oder":
                    # print("cancel_oder")
                    self.bk_list.append(bk_oder_dic)
                    # print(bk_list)
                print("line_num: ", get_current_expr().lineno)
                self.write_log(
                    "成功委托<合约号: {}, 类型：开多， 数量: {}, 价格: {:.2f}>".format(
                        self.get_current_contract().symbol, n, price), line_num=get_current_expr().lineno)
        else:
            oder = OrderData(accountid="",
                             symbol="",
                             exchange=Exchange.CFFEX,
                             orderid="",
                             type=OrderType.LIMIT,
                             direction=Direction.LONG,
                             offset=Offset.OPEN,
                             price=price,
                             volume=n,
                             traded=0,
                             status=Status.SUBMITTING,
                             time="2020-01-13 12:20:53",
                             gateway_name="",
                             )
            self.backtest_order_record.append(oder)

    # 7
    # 第1期
    def sk(self, n, price, is_cancel=None):

        if self.editor_version == '2.0':
            n = n.exec()
            price = price.exec()
        if self.env == "real":
            # 新版本编辑器的trade_again 功能实现
            run_flag = 0
            if len(self.trade_again_time_list):
                line_num = get_current_expr().lineno
                if self.trade_again_time_list[-1] < line_num:
                    run_flag = 1
                else:
                    for i in range(len(self.trade_again_time_list)):
                        if self.trade_again_time_list[i] > line_num:
                            if self.trade_count_list[i] > 0:
                                run_flag = 1
                                self.trade_count_list[i] -= 1
                                break
                            else:
                                break
            else:
                run_flag = 1

            # 做挂单判断
            unsucc_oder_flag = False
            if self.unsuccessful_oder['SK'] == {} or not self.if_line_in_trade_fun(fun_name='SK'):
                unsucc_oder_flag = True
            else:
                line_num_if_success = get_current_expr().lineno
                oder_id = self.unsuccessful_oder['SK'][str(line_num_if_success)]
                oder = self.get_order(oder_id)
                if oder is not None:
                    if oder.status == Status.NOTTRADED:
                        unsucc_oder_flag = False
                    else:
                        unsucc_oder_flag = True

            if run_flag == 1 and unsucc_oder_flag == True and not self._is_close_():

                oder_id_res = self.send_order(self.get_current_contract(), price, n, Direction.SHORT, Offset.OPEN)
                # 等待交易服务器返回结果，结果不为“提交中”
                # while self.get_order(oder_id_res) == None:
                #     pass
                # while self.get_order(oder_id_res).status == Status.SUBMITTING:
                #     pass
                # 将所有交易的id存入trade_oder
                self.trade_oder.append(oder_id_res)
                # 所有交易的委托号存入trade_full_order
                self.trade_full_order.append(oder_id_res)
                bk_oder_dic = {'oder_id': oder_id_res, 'timeout': datetime.now() + timedelta(seconds=5)}

                # 记录交易的单号，以便判断未成交的订单
                line_num_record = get_current_expr().lineno
                self.unsuccessful_oder['SK'][str(line_num_record)] = oder_id_res

                # 记录每行行号对应的订单id
                self.line_oder_id[str(line_num_record)] = oder_id_res

                # 等待交易服务器返回结果，结果不为“提交中”
                # 等待交易服务器返回结果
                count_time = 0
                stat_flag = 1  # 交易服务器判断flag
                while True:
                    res_instance = self.get_order(oder_id_res)
                    if res_instance == None and count_time < 3:
                        count_time += 1
                        time.sleep(1)

                    elif count_time >= 3:
                        # 交易服务器未返回结果，不需要检测状态
                        stat_flag = 0
                        self.write_log("SK交易函数未得到实例或订单被撤销")
                        break

                    else:
                        break

                # 等待状态不为提交中
                # 如果交易服务器并没有实例，就不需要检测
                if stat_flag == 0:
                    pass
                else:
                    count_time = 0
                    while True:
                        order = self.get_order(oder_id_res)
                        if order is None:
                            count_time += 1
                            continue
                        res_instance_stat = order.status
                        if res_instance_stat == Status.SUBMITTING and count_time < 3:
                            count_time += 1
                            time.sleep(1)
                        elif count_time >= 3:
                            self.write_log("SK函数一直处于提交中或被服务器拒单")
                            break
                        else:
                            break
                if is_cancel == "cancel_oder":
                    self.bk_list.append(bk_oder_dic)
                print("line_num: ", get_current_expr().lineno)
                self.write_log(
                    "成功委托<合约号: {}, 类型：开空， 数量: {}, 价格: {:.2f}>".format(
                        self.get_current_contract().symbol, n, price), line_num=get_current_expr().lineno)
        else:
            oder = OrderData(accountid="",
                             symbol="",
                             exchange=Exchange.CFFEX,
                             orderid="",
                             type=OrderType.LIMIT,
                             direction=Direction.SHORT,
                             offset=Offset.OPEN,
                             price=price,
                             volume=n,
                             traded=0,
                             status=Status.SUBMITTING,
                             time="2020-01-13 12:20:53",
                             gateway_name="",
                             )
            self.backtest_order_record.append(oder)

    def bp(self, n, price, is_cancel=None, is_today=False):
        try:
            if self.editor_version == '2.0':
                n = n.exec()
                price = price.exec()

            if self.env == "real":
                # 新版本编辑器的trade_again 功能实现
                run_flag = 0
                if len(self.trade_again_time_list):
                    line_num = get_current_expr().lineno
                    if self.trade_again_time_list[-1] < line_num:
                        run_flag = 1
                    else:
                        for i in range(len(self.trade_again_time_list)):
                            if self.trade_again_time_list[i] > line_num:
                                if self.trade_count_list[i] > 0:
                                    run_flag = 1
                                    self.trade_count_list[i] -= 1
                                    break
                                else:
                                    break
                else:
                    run_flag = 1

                # 做挂单判断
                unsucc_oder_flag = False
                if self.unsuccessful_oder['BP'] == {} or not self.if_line_in_trade_fun(fun_name='BP'):
                    unsucc_oder_flag = True
                else:
                    line_num_if_success = get_current_expr().lineno
                    oder_id = self.unsuccessful_oder['BP'][str(line_num_if_success)]
                    oder = self.get_order(oder_id)
                    if oder is not None:
                        if oder.status == Status.NOTTRADED:
                            unsucc_oder_flag = False
                        else:
                            unsucc_oder_flag = True

                if run_flag == 1 and unsucc_oder_flag == True and not self._is_close_():
                    oder_id_res = self.send_order(self.get_current_contract(), price, n, Direction.LONG, Offset.CLOSE)
                    # 等待交易服务器返回结果，结果不为“提交中”
                    # while self.get_order(oder_id_res) == None:
                    #     pass
                    # while self.get_order(oder_id_res).status == Status.SUBMITTING:
                    #     pass

                    self.trade_full_order.append(oder_id_res)

                    if isinstance(oder_id_res, str):
                        self.write_log(oder_id_res)
                        return

                    for oid in oder_id_res:
                        # 将所有交易的id存入trade_oder
                        self.trade_oder.append(oid)
                        bk_oder_dic = {'oder_id': oid, 'timeout': datetime.now() + timedelta(seconds=5)}

                        # 记录交易的单号，以便判断未成交的订单
                        line_num_record = get_current_expr().lineno
                        self.unsuccessful_oder['BP'][str(line_num_record)] = oid

                        # 记录每行行号对应的订单id
                        self.line_oder_id[str(line_num_record)] = oid

                        # 等待交易服务器返回结果，结果不为“提交中”
                        # 等待交易服务器返回结果
                        count_time = 0
                        stat_flag = 1  # 交易服务器判断flag
                        while True:
                            res_instance = self.get_order(oid)
                            if res_instance == None and count_time < 3:
                                count_time += 1
                                time.sleep(1)

                            elif count_time >= 3:
                                # 交易服务器未返回结果，不需要检测状态
                                stat_flag = 0
                                self.write_log("BP交易函数未得到实例或订单被撤销")
                                break

                            else:
                                break

                        # 等待状态不为提交中
                        # 如果交易服务器并没有实例，就不需要检测
                        if stat_flag == 0:
                            pass
                        else:
                            count_time = 0
                            while True:
                                order  = self.get_order(oid)
                                if order is None:
                                    count_time += 1
                                    continue
                                res_instance_stat = order.status
                                if res_instance_stat == Status.SUBMITTING and count_time < 3:
                                    count_time += 1
                                    time.sleep(1)
                                elif count_time >= 3:
                                    self.write_log("BP函数一直处于提交中或被服务器拒单")
                                    break
                                else:
                                    break
                        # 大小写敏感
                        if is_cancel == "cancel_oder":
                            self.bk_list.append(bk_oder_dic)
                    print("line_num: ", get_current_expr().lineno)
                    self.write_log("成功委托<合约号: {}, 类型：平多， 数量: {}, 价格: {:.2f}, 委托数量: {}>".format(
                        self.get_current_contract().symbol, n, price, len(oder_id_res)),
                        line_num=get_current_expr().lineno)
            else:
                oder = OrderData(accountid="",
                                 symbol="",
                                 exchange=Exchange.CFFEX,
                                 orderid="",
                                 type=OrderType.LIMIT,
                                 direction=Direction.LONG,
                                 offset=Offset.CLOSE,
                                 price=price,
                                 volume=n,
                                 traded=0,
                                 status=Status.SUBMITTING,
                                 time="2020-01-13 12:20:53",
                                 gateway_name="",
                                 )
                self.backtest_order_record.append(oder)
        except:
            traceback.print_exc()

    def sp(self, n, price, is_cancel=None):
        if self.editor_version == '2.0':
            n = n.exec()
            price = price.exec()

        if self.env == "real":
            # 新版本编辑器的trade_again 功能实现
            run_flag = 0
            if len(self.trade_again_time_list):
                line_num = get_current_expr().lineno
                if self.trade_again_time_list[-1] < line_num:
                    run_flag = 1
                else:
                    for i in range(len(self.trade_again_time_list)):
                        if self.trade_again_time_list[i] > line_num:
                            if self.trade_count_list[i] > 0:
                                run_flag = 1
                                self.trade_count_list[i] -= 1
                                break
                            else:
                                break
            else:
                run_flag = 1

            # 做挂单判断
            unsucc_oder_flag = False
            if self.unsuccessful_oder['SP'] == {} or not self.if_line_in_trade_fun(fun_name='SP'):
                unsucc_oder_flag = True
            else:
                line_num_if_success = get_current_expr().lineno
                oder_id = self.unsuccessful_oder['SP'][str(line_num_if_success)]
                oder = self.get_order(oder_id)
                if oder is not None:
                    if oder.status == Status.NOTTRADED:
                        unsucc_oder_flag = False
                    else:
                        unsucc_oder_flag = True

            if run_flag == 1 and unsucc_oder_flag == True and not self._is_close_():

                oder_id_res = self.send_order(self.get_current_contract(), price, n, Direction.SHORT, Offset.CLOSE)
                # 等待交易服务器返回结果，结果不为“提交中”
                # while self.get_order(oder_id_res) == None:
                #     pass
                # while self.get_order(oder_id_res).status == Status.SUBMITTING:
                #     pass
                self.trade_full_order.append(oder_id_res)
                if isinstance(oder_id_res, str):
                    self.write_log(oder_id_res)
                    return

                for oid in oder_id_res:
                    # 将所有交易的id存入trade_oder
                    self.trade_oder.append(oid)
                    bk_oder_dic = {'oder_id': oid, 'timeout': datetime.now() + timedelta(seconds=5)}

                    # 记录交易的单号，以便判断未成交的订单
                    line_num_record = get_current_expr().lineno
                    self.unsuccessful_oder['SP'][str(line_num_record)] = oid

                    # 记录每行行号对应的订单id
                    self.line_oder_id[str(line_num_record)] = oid

                    # 等待交易服务器返回结果，结果不为“提交中”
                    # 等待交易服务器返回结果
                    count_time = 0
                    stat_flag = 1  # 交易服务器判断flag
                    while True:
                        res_instance = self.get_order(oid)
                        if res_instance == None and count_time < 3:
                            count_time += 1
                            time.sleep(1)

                        elif count_time >= 3:
                            # 交易服务器未返回结果，不需要检测状态
                            stat_flag = 0
                            self.write_log("SP交易函数未得到实例或订单被撤销")
                            break

                        else:
                            break

                    # 等待状态不为提交中
                    # 如果交易服务器并没有实例，就不需要检测
                    if stat_flag == 0:
                        pass
                    else:
                        count_time = 0
                        while True:
                            order = self.get_order(oid)
                            if order is None:
                                count_time += 1
                                continue
                            res_instance_stat = order.status
                            if res_instance_stat == Status.SUBMITTING and count_time < 3:
                                count_time += 1
                                time.sleep(1)
                            elif count_time >= 3:
                                self.write_log("SP函数一直处于提交中或被服务器拒单")
                                break
                            else:
                                break

                    # 大小写敏感
                    if is_cancel == "cancel_oder":
                        self.bk_list.append(bk_oder_dic)
                print("line_num: ", get_current_expr().lineno)
                self.write_log("成功委托<合约号: {}, 类型：平空， 数量: {}, 价格: {:.2f}>, 委托数量: {}".format(
                    self.get_current_contract().symbol, n, price, len(oder_id_res)), line_num=get_current_expr().lineno)
        else:
            oder = OrderData(accountid="",
                             symbol="",
                             exchange=Exchange.CFFEX,
                             orderid="",
                             type=OrderType.LIMIT,
                             direction=Direction.SHORT,
                             offset=Offset.CLOSE,
                             price=price,
                             volume=n,
                             traded=0,
                             status=Status.SUBMITTING,
                             time="2020-01-13 12:20:53",
                             gateway_name="",
                             )
            self.backtest_order_record.append(oder)

    def unsuccessful_oder_init(self):
        self.unsuccessful_oder = {'BK': {}, 'SK': {}, 'SP': {}, 'BP': {}}

    def if_line_in_trade_fun(self, fun_name: str):
        # 辅助交易函数做判断
        line = get_current_expr().lineno
        line_str = str(line)
        if line_str in self.unsuccessful_oder[fun_name].keys():
            return True
        else:
            return False

    # 2019/10/4 LongWenHao
    # 10
    # 第1期
    def abs(self, x):
        if self.editor_version == '2.0':
            x = x.exec()
        return abs(x)

    # 11
    def autofilter(self):
        pass

    # @Author : Yangjintao
    # @Time : 2019.10.14
    # 12
    def available_opi(self):
        position = self.get_current_position()
        # 当日买入手数不计入该函数取值
        if position:
            return position.yd_volume - position.frozen
        else:
            self.write_log("当前合约无可用手数")
            return 0

    # @Author : Yangjintao
    # @Time : 2019.10.14
    # 13
    def barpos(self):
        return len(self.main_engine.get_current_bars())

    # @Author : Yangjintao
    # 14
    def barscount(self, cond):
        bars = self.main_engine.get_current_bars()
        self.lock_getNew()
        for i in range(len(bars)):
            if self.running_bar != bars[i]:
                self.running_bar = bars[i]
                self.ix -= 1
                try:
                    tmp = cond.exec()
                except Exception as err:
                    raise Exception("未识别的表达式：" + f"{err}")
                if tmp:
                    self.ix = -1
                    return len(bars) - 1 - i
        self.unlock_getNew()
        self.write_log("未找到满足条件的K线周期")
        return None

    def oper(self, list1, list2, operator):
        arr1 = np.array(list1)
        arr2 = np.array(list2)
        # 返回满足运算符的所有索引
        if operator == '>':
            return np.where(arr1 > arr2)
        elif operator == '<':
            return np.where(arr1 < arr2)
        elif operator == '==':
            return np.where(arr1 == arr2)
        elif operator == '<>':
            return np.where(arr1 != arr2)
        else:
            pass

    # @Author : Wangyongchang
    # @Time : 2019.11.04
    # 15
    # 第1期
    # def barslast(self, *args):
    #     if len(args) != 1:
    #         raise Exception("BARSLAST函数：参数数量错误！")
    #     # kem:去掉括号
    #     # 得到判断条件
    #     condition = str(args[0]).replace('()', '').replace(' ', '')
    #     operator = re.findall(r'[<>\<\>|==]', condition)[0]
    #     if not operator:
    #         raise Exception("BARSLAST函数：参数缺少比较条件！")
    #     funcs = re.split(">|<|<>|==", condition)
    #     if len(funcs) != 2:
    #         raise Exception("BARSLAST函数：参数比较条件错误！")
    #     if funcs[0] == funcs[1]:
    #         raise Exception("BARSLAST函数：参数的左右比较条件不能相同！")
    #
    #     # kem:适配大小写
    #     if ">" in condition:
    #         if ("c" in funcs[0] or 'C' in funcs[0]) and ("o" in funcs[1] or 'O' in funcs[1]):
    #             return self.red_pos()
    #         elif ("o" in funcs[0] or 'O' in funcs[0]) and ("c" in funcs[1] or 'C' in funcs[1]):
    #             return self.green_pos()
    #         else:
    #             raise Exception("BARSLAST函数：未识别的条件！")
    #
    #     elif "<" in condition:
    #         if ("c" in funcs[0] or 'C' in funcs[0]) and ("o" in funcs[1] or 'O' in funcs[1]):
    #             return self.green_pos()
    #         elif ("o" in funcs[0] or 'O' in funcs[0]) and ("c" in funcs[1] or 'C' in funcs[1]):
    #             return self.red_pos()
    #         else:
    #             raise Exception("BARSLAST函数：未识别的条件！")
    #
    # # K线红色的位置
    # def red_pos(self):
    #     bars = self.main_engine.get_current_bars()
    #     if not bars:
    #         return
    #     count = -1
    #     for i in range(len(bars)-1, -1, -1):
    #         count = count + 1
    #         if bars[i].close_price > bars[i].open_price:
    #             return count
    #             break
    #
    # # K线绿色的位置
    # def green_pos(self):
    #     bars = self.main_engine.get_current_bars()
    #     if not bars:
    #         return
    #     count = -1
    #     for i in range(len(bars)-1, -1, -1):
    #         count = count + 1
    #         if bars[i].close_price < bars[i].open_price:
    #             return count
    #             break

    """
    @Author : Kem
    @Time : 2020.01.02
    """

    def barslast(self, *args):
        if len(args) != 1:
            raise Exception("BARSLAST函数：参数数量错误！")
        cond = args[0]
        c = 0
        iterbars = self.main_engine.get_current_bars()
        self.lock_getNew()
        for bar in iterbars[::-1]:
            if bar != self.running_bar:
                self.running_bar = bar
                self.ix -= 1
                try:
                    tmp = cond.exec()
                except Exception as err:
                    raise Exception("BARSLAST函数：未识别的条件: " + f"{err}")
                if not tmp:
                    c += 1
                else:
                    self.ix = -1
                    return c
        self.unlock_getNew()
        return None

    # 16
    # 第1期
    # def barslastcount(self, *args):
    #     # 判断参数数量
    #     if len(args) != 1:
    #         raise Exception("BARLASTCOUNT函数：参数数量错误！")
    #     # 根据解释器版本对参数进行处理
    #     if self.editor_version == '2.0':
    #         condition = str(args[0]).replace("()", "").replace(" ", "")
    #     else:
    #         condition = args[0].replace("()", "").replace(" ", "")
    #     # 判断比较操作符
    #     operator = re.findall(r'[<>\<\>|==]', condition)[0]
    #     # 如果没有比较操作符，抛出异常
    #     if not operator:
    #         raise Exception("BARSLAST函数：参数缺少比较条件！")
    #     funcs = re.split(">|<|<>|==", condition)
    #     if len(funcs) != 2:
    #         raise Exception("BARSLAST函数：参数比较条件错误！")
    #     if funcs[0] == funcs[1]:
    #         raise Exception("BARSLAST函数：参数的左右比较条件不能相同！")
    #
    #     # kem:适配大小写
    #     if ">" in condition:
    #         if ("c" in funcs[0] or 'C' in funcs[0]) and ("o" in funcs[1] or 'O' in funcs[1]):
    #             return self.red_count()
    #         elif ("o" in funcs[0] or 'O' in funcs[0]) and ("c" in funcs[1] or 'C' in funcs[1]):
    #             return self.green_count()
    #         else:
    #             raise Exception("BARLASTCOUNT函数：未识别的条件！")
    #
    #     elif "<" in condition:
    #         if ("c" in funcs[0] or 'C' in funcs[0]) and ("o" in funcs[1] or 'O' in funcs[1]):
    #             return self.green_count()
    #         elif ("o" in funcs[0] or 'O' in funcs[0]) and ("c" in funcs[1] or 'C' in funcs[1]):
    #             return self.red_count()
    #         else:
    #             raise Exception("BARLASTCOUNT函数：未识别的条件！")
    #
    # # K线红色据当前的距离
    # def red_count(self):
    #     bars = self.main_engine.get_current_bars()
    #     if not bars:
    #         return
    #     count = -1
    #     for i in range(len(bars)-1, -1, -1):
    #         count = count + 1
    #         if bars[i].close_price <= bars[i].open_price:
    #             return count
    #             break
    #
    # # K线绿色据当前的距离
    # def green_count(self):
    #     bars = self.main_engine.get_current_bars()
    #     if not bars:
    #         return
    #     count = -1
    #     for i in range(len(bars)-1, -1, -1):
    #         count = count + 1
    #         if bars[i].close_price >= bars[i].open_price:
    #             return count
    #             break

    """
    @Author : Kem
    @Time : 2020.01.03
    """

    def barslastcount(self, *args):
        if len(args) != 1:
            raise Exception("BARSLAST函数：参数数量错误！")
        cond = args[0]
        c = 0
        iterbars = self.main_engine.get_current_bars()
        for bar in iterbars[::-1]:
            self.running_bar = bar
            self.ix -= 1
            try:
                tmp = cond.exec()
            except Exception as err:
                raise Exception("BARSLAST函数：未识别的条件: " + f"{err}")
            if not tmp:
                self.ix = -1
                return c
            else:
                c += 1
        return None

    # @Author : Yangjintao
    # 17
    def barssince(self, cond):
        bars = self.main_engine.get_current_bars()
        self.lock_getNew()
        for i in range(len(bars)):
            if self.running_bar != bars[i]:
                self.running_bar = bars[i]
                self.ix -= 1
                try:
                    tmp = cond.exec()
                except Exception as err:
                    raise Exception("未识别的表达式：" + f"{err}")
                if tmp:
                    self.ix = -1
                    return len(bars) - 1 - i
        self.unlock_getNew()
        self.write_log("未找到满足条件的K线周期")
        return None

    # 18
    def barssincen(self, cond, n):
        bars = self.main_engine.get_current_bars()
        n = n.exec()
        if type(n) != int:
            raise Exception("参数错误：函数BARSSINCEN参数n应为整数")
        n = int(n)
        if n == 0:
            return None
        if n < len(bars):
            bars = bars[-n:]
        self.lock_getNew()
        for i in range(len(bars)):
            if self.running_bar != bars[i]:
                self.running_bar = bars[i]
                self.ix -= 1
                try:
                    tmp = cond.exec()
                except Exception as err:
                    raise Exception("未识别的表达式：" + f"{err}")
                if tmp:
                    self.ix = -1
                    return len(bars) - 1 - i
        self.unlock_getNew()
        self.write_log("BARSSINCEN函数：在" + str(n) + "周期内不满足条件")
        return None

    # 2019-10-15 LWH
    # 19
    def between(self, x, y, z):
        x = x.exec()
        y = y.exec()
        z = z.exec()
        try:
            if y < x < z or x == y == z:
                return True
            else:
                return False
        except:
            raise Exception("BETWEEN函数：参数比较出错")

    # 2019-10-22 LWH
    # 20
    # 第1期
    def bkhigh(self):
        settings = get_settings("database.")
        database_manager: "BaseDatabaseManager" = init(settings=settings)
        current_contract = self.get_current_contract(use_df=False)
        trades = database_manager.load_trades_by_symbol(current_contract.symbol)
        # print(trades)
        if len(trades) == 0:
            self.write_log("BKHIGH函数:全部成交记录为空")
            return
        info = {}
        newInfo = []

        current_contract = self.get_current_contract()
        current_bars = self.main_engine.get_current_bars()

        dt_ix_map = {}
        for ix, bar in enumerate(current_bars):
            dt_ix_map[bar.datetime] = ix
        # expr = get_current_expr()
        variable_name = ""
        bk_num = []
        # if self.isNew == False:
        for bar in current_bars:
            # info.append({int(self.dt_ix_map[bar.datetime]):float(bar.high_price)})
            newInfo.append(float(bar.high_price))
            info[int(dt_ix_map[bar.datetime])] = float(bar.high_price)
        for trade in trades:
            Time = trade.datetime[0:4] + "-" + trade.datetime[4:6] + "-" + trade.datetime[
                                                                           6:8] + trade.datetime[
                                                                                  8:11] + \
                   trade.datetime[11:14] + ":00"
            if trade.datetime >= self.strategy_start_time \
                    and datetime.strptime(Time, '%Y-%m-%d %H:%M:%S') in dt_ix_map \
                    and trade.offset == Offset.OPEN and trade.symbol == current_contract.symbol \
                    and trade.direction == Direction.LONG:
                bk_num.append(int(dt_ix_map[datetime.strptime(Time, '%Y-%m-%d %H:%M:%S')]))
        bk_num.append(0)
        bk_num.append(len(current_bars))

        bk_num = set(bk_num)
        bk_num = list(bk_num)
        bk_num.sort()
        print(bk_num)
        if len(bk_num) > 2:
            for i in range(len(bk_num) - 1):
                section = newInfo[bk_num[i] + 1:bk_num[i + 1]]
                if len(section) > 1:
                    num = max(section)
                else:
                    num = newInfo[bk_num[i]]
                for ix in range(len(newInfo[bk_num[i] + 1:bk_num[i + 1]])):
                    info[bk_num[i] + 1 + ix] = num
        else:
            for bar in current_bars:
                info[int(dt_ix_map[bar.datetime])] = 0
        # elif self.isNew == True:
        #     print(info)
        #     bk_num.append(int(dt_ix_map[current_bars[-1].datetime]))
        #     for bar in current_bars[bk_num[-2] + 1:bk_num[-1]]:
        #         info[int(dt_ix_map[bar.datetime])] = float(bar.high_price)
        #
        #     for ix in range(len(info[bk_num[-2] + 1:bk_num[-1]])):
        #         section = newInfo[bk_num[-2] + 1:bk_num[-1]]
        #         if len(section) > 1:
        #             num = max(section)
        #         else:
        #             num = newInfo[bk_num[-2] + 1]
        #         info[bk_num[-2] + 1 + ix] = num
        #     self.isNew = False
        if RunEnvironment.run_vars.keys():
            for var_name in RunEnvironment.run_vars.keys():
                s = "{}".format(var_name)
                variable = RunEnvironment.run_vars[s]
                # print(variable.operands[0])
                if variable.operator == ":":
                    variable_name = s
                    # print(variable_name)
                    # print(info)
                    event = Event(EVENT_INFO, {"name": variable_name, "data": info})
                    self.event_engine.put(event)
                    return info[len(bk_num) - 1]
                else:
                    return info[len(bk_num) - 1]
        else:
            return info[len(newInfo) - 1]

    # 2019-10-22 LWH
    # 21
    # 第1期
    def bklow(self):
        settings = get_settings("database.")
        database_manager: "BaseDatabaseManager" = init(settings=settings)
        current_contract = self.get_current_contract(use_df=False)
        trades = database_manager.load_trades_by_symbol(current_contract.symbol)
        # print(trades)
        if len(trades) == 0:
            self.write_log("BKLOW函数:全部成交记录为空")
            return
        info = {}
        newInfo = []

        current_contract = self.get_current_contract()
        current_bars = self.main_engine.get_current_bars()

        dt_ix_map = {}
        for ix, bar in enumerate(current_bars):
            dt_ix_map[bar.datetime] = ix
        # expr = get_current_expr()
        variable_name = ""
        bk_num = []
        # if self.isNew == False:
        for bar in current_bars:
            # info.append({int(self.dt_ix_map[bar.datetime]):float(bar.high_price)})
            newInfo.append(float(bar.low_price))
            info[int(dt_ix_map[bar.datetime])] = float(bar.low_price)
        for trade in trades:
            Time = trade.datetime[0:4] + "-" + trade.datetime[4:6] + "-" + trade.datetime[
                                                                           6:8] + trade.datetime[
                                                                                  8:11] + \
                   trade.datetime[11:14] + ":00"
            if trade.datetime >= self.strategy_start_time \
                    and datetime.strptime(Time, '%Y-%m-%d %H:%M:%S') in dt_ix_map \
                    and trade.offset == Offset.OPEN and trade.symbol == current_contract.symbol \
                    and trade.direction == Direction.LONG:
                bk_num.append(int(dt_ix_map[datetime.strptime(Time, '%Y-%m-%d %H:%M:%S')]))
        bk_num.append(0)
        bk_num.append(len(current_bars))

        bk_num = set(bk_num)
        bk_num = list(bk_num)
        bk_num.sort()
        # print(bk_num)
        if len(bk_num) > 2:
            for i in range(len(bk_num) - 1):
                section = newInfo[bk_num[i] + 1:bk_num[i + 1]]
                if len(section) > 1:
                    num = min(section)
                else:
                    num = newInfo[bk_num[i]]
                for ix in range(len(newInfo[bk_num[i] + 1:bk_num[i + 1]])):
                    info[bk_num[i] + 1 + ix] = num
        else:
            for bar in current_bars:
                info[int(dt_ix_map[bar.datetime])] = 0
        # elif self.isNew == True:
        #     print(info)
        #     bk_num.append(int(dt_ix_map[current_bars[-1].datetime]))
        #     for bar in current_bars[bk_num[-2] + 1:bk_num[-1]]:
        #         info[int(dt_ix_map[bar.datetime])] = float(bar.high_price)
        #
        #     for ix in range(len(info[bk_num[-2] + 1:bk_num[-1]])):
        #         section = newInfo[bk_num[-2] + 1:bk_num[-1]]
        #         if len(section) > 1:
        #             num = max(section)
        #         else:
        #             num = newInfo[bk_num[-2] + 1]
        #         info[bk_num[-2] + 1 + ix] = num
        #     self.isNew = False
        if RunEnvironment.run_vars.keys():
            for var_name in RunEnvironment.run_vars.keys():
                s = "{}".format(var_name)
                variable = RunEnvironment.run_vars[s]
                # print(variable.operands[0])
                if variable.operator == ":":
                    variable_name = s
                    # print(variable_name)
                    # print(info)
                    event = Event(EVENT_INFO, {"name": variable_name, "data": info})
                    self.event_engine.put(event)
                    return info[len(bk_num) - 1]
                else:
                    return info[len(bk_num) - 1]
        else:
            return info[len(newInfo) - 1]

    # 22
    # 第1期
    def bkvol1(self):
        # res_flag = "position_data" # "acountid_data"
        # res = []
        # positions = self.get_all_positions()
        # for position in positions:
        #     if position.direction == Direction.LONG:
        #         if res_flag == "position_data":
        #             res.append(position)
        #         elif res_flag == "accountid_data":
        #             res.append(position.accountid)
        #         else:
        #             pass
        # return res
        symbol = self.get_current_contract().symbol
        positions = self.main_engine.get_long_positions()
        # positions = self.get_all_positions()

        for position in positions:
            if position.symbol == symbol:
                if position.direction == Direction.LONG:
                    return position.volume
        return 0

    #
    # 23
    # 第1期
    def skvol1(self):
        # res_flag = "position_data"  # "acountid_data"
        # res = []
        # positions = self.get_all_positions()
        # for position in positions:
        #     if position.direction == Direction.SHORT:
        #         if res_flag == "position_data":
        #             res.append(position)
        #         elif res_flag == "accountid_data":
        #             res.append(position.accountid)
        #         else:
        #             pass
        # return res
        symbol = self.get_current_contract().symbol
        positions = self.main_engine.get_short_positions()
        # positions = self.get_all_positions()
        for position in positions:
            if position.symbol == symbol:
                if position.direction == Direction.SHORT:
                    return position.volume
        return 0

    # 2019-10-15 LWH
    # 24
    # 第1期
    def bkvol(self):


        settings = get_settings("database.")
        database_manager: "BaseDatabaseManager" = init(settings=settings)
        current_contract = self.get_current_contract(use_df=False)
        #trades = database_manager.load_trades_by_symbol(current_contract.symbol)
        trades = []
        if self.trade_full_order:
            for t in self.trade_full_order:
                trade = database_manager.load_trades_by_orderid(t[4:])
                if trade:
                    trades.append(trade[0])

        if trades == None:
            raise Exception("BKVOL函数：交易记录为空")
        # 根据交易记录得到的理论持仓,最开始为0
        theory_position = 0

        for trade in trades:
            # nowTime = trade.datetime[0:4] + "-" + trade.datetime[4:6] + "-" + trade.datetime[
            #                                                                6:8] + trade.datetime[
            #                                                                       8:11] + \
            #        trade.datetime[11:14] + ":00"

            if trade.datetime >= self.strategy_start_time and trade.offset == Offset.OPEN and trade.direction == Direction.LONG and trade.symbol == current_contract.symbol:
                print(trade.volume)
                theory_position += trade.volume
            elif trade.datetime >= self.strategy_start_time and (
                    trade.offset == Offset.CLOSE or trade.offset == Offset.CLOSETODAY or trade.offset == Offset.CLOSEYESTERDAY) and trade.direction == Direction.SHORT and trade.symbol == current_contract.symbol and theory_position > 0:
                # print(trade)
                theory_position -= trade.volume
        return theory_position

    # 2019-10-15 LWH
    # 25
    # 第1期
    def skvol(self):
        settings = get_settings("database.")
        database_manager: "BaseDatabaseManager" = init(settings=settings)
        current_contract = self.get_current_contract(use_df=False)
        #trades = database_manager.load_trades_by_symbol(current_contract.symbol)
        trades = []
        if self.trade_full_order:
            for t in self.trade_full_order:
                trade = database_manager.load_trades_by_orderid(t[4:])
                if trade:
                    trades.append(trade[0])
        if trades == None:
            raise Exception("SKVOL函数：交易记录为空")
        # 根据交易记录得到的理论持仓,最开始为0
        theory_position = 0

        for trade in trades:
            # nowTime = trade.datetime[0:4] + "-" + trade.datetime[4:6] + "-" + trade.datetime[
            #                                                                   6:8] + trade.datetime[
            #                                                                          8:11] + \
            #           trade.datetime[11:14] + ":00"

            if trade.datetime >= self.strategy_start_time and trade.offset == Offset.OPEN and trade.direction == Direction.SHORT and trade.symbol == current_contract.symbol:
                # print(trade)
                theory_position += trade.volume
            elif trade.datetime >= self.strategy_start_time and (
                    trade.offset == Offset.CLOSE or trade.offset == Offset.CLOSETODAY or trade.offset == Offset.CLOSEYESTERDAY) and trade.direction == Direction.LONG and trade.symbol == current_contract.symbol and theory_position > 0:
                # print(trade)
                theory_position -= trade.volume
        return theory_position

    # 26
    def closesec(self):
        # tick = self.main_engine.get_current_bars()[-1]
        # # tick = self.get_tick(vt_symbol=vt_symbol)
        # time_tick:datetime = tick.datetime
        # time_str = time_tick.strftime("%Y-%m-%d %H:%M:%S")[-8]
        # # if time_str > "09:00:00" and time_str < "11:30:00":
        # # if time_str < "11:30:00":
        # if time_tick.time() < datetime.time(hour=11, minute=30, second=0):
        #     time_delta = datetime.strptime("11:30:00", "%H:%M:%S") - datetime.strptime(time_str, "%H:%M:%S")
        #     # time_delta = (time(hour=11, minute=30, second=0) - time_tick.time()).second()
        #     return time_delta
        # # elif time_str > "13:30:00" and time_str < "15:00:00":
        # elif time_str > "11:30:00" and time_str < "15:00:00":
        #     # time_delta = datetime.strptime("15:00:00", "%H:%M:%S") - datetime.strptime(time_str, "%H:%M:%S")
        #     time_delta = time.strptime("15:00:00", "%H:%M:%S") - time.strptime(time_str, "%H:%M:%S")
        #     return time_delta
        # else:
        #     return "时间错误，无法计算closesec"
        """
        author: liuzhu
        time: 2019-10-25
        :return:
        """
        tick = self.main_engine.get_current_bars()[-1]
        time_tick: datetime = tick.datetime
        morning_start = datetime.strptime(str(datetime.now().date()) + '9:00:00', '%Y-%m-%d%H:%M:%S')
        morning_end = datetime.strptime(str(datetime.now().date()) + '11:30:00', '%Y-%m-%d%H:%M:%S')
        afternoon_start = datetime.strptime(str(datetime.now().date()) + '13:30:00', '%Y-%m-%d%H:%M:%S')
        afternoon_end = datetime.strptime(str(datetime.now().date()) + '15:00:00', '%Y-%m-%d%H:%M:%S')
        if time_tick < afternoon_end:
            timedelta = afternoon_end - time_tick
            return timedelta.seconds
        else:
            return "time is over 15:00, can not compute closesec"

    # 27
    def condbars(self):
        pass

    # 28
    # 第1期
    def count(self, cond, period):
        c = 0
        period = period.exec()
        iterbars = self.main_engine.get_current_bars()
        # print(iterbars)
        if period == None:
            return None
        elif period > len(iterbars) or period == 0:
            for bar in iterbars[::-1]:
                if self.running_bar != bar:
                    self.running_bar = bar
                    if cond.exec():
                        c += 1
                    self.ix -= 1
        else:
            for i in range(len(iterbars) - period, len(iterbars))[::-1]:
                self.running_bar = iterbars[i]
                print(cond.exec())
                if cond.exec():
                    c += 1
                self.ix -= 1
        self.ix = -1
        return c

        list2 = eval(funcs[1])
        res = self.oper(list1, list2, operator)
        c = 0
        if period == 0:
            return len(res[0])
        else:
            for r in res[0]:
                if r > len(current_bars) - period:
                    c += 1
            return c

        # print(list2)

    # 28
    # 第1期
    # def count(self, cond: str, period):
    #     cond_str = cond
    #     count_sum = 0
    #     current_bars: TickData = self.main_engine.get_current_bars()
    #     key_str = ["self.editor_engine.c()", "self.editor_engine.h()", "self.editor_engine.l()", "self.editor_engine.o()", "self.editor_engine.v()"]
    #     for key in key_str:
    #         if key in cond_str:
    #             if key == "self.editor_engine.c()":
    #                 cond_str.replace("self.editor_engine.c()", "bar.close_price")
    #             elif key == "self.editor_engine.h()":
    #                 cond_str.replace("self.editor_engine.h()", "bar.high_price")
    #             elif key == "self.editor_engine.l()":
    #                 cond_str.replace("self.editor_engine.l()", "bar.low_price")
    #             elif key == "self.editor_engine.o()":
    #                 cond_str.replace("self.editor_engine.o()", "bar.open_price")
    #             elif key == "self.editor_engine.v()":
    #                 cond_str.replace("self.editor_engine.v()", "bar.volume")
    #     for bar in current_bars:
    #         res = eval(cond_str)
    #         if res == True:
    #             count_sum += 1

    # return count_sum

    # 29
    def countsig(self):
        pass

    # 2019/9/30 LongWenHao
    # 2019/10/15 WangYongchang
    # 30
    # 第1期
    def crossup(self, *args):
        if len(args) != 2:
            raise Exception("CROSS函数：参数数量错误！")

        script_1 = args[0]
        script_2 = args[1]

        if "ma" not in script_1 and "ma" in script_2:
            current_bars = self.main_engine.get_current_bars()
            ma_list = eval(script_2.replace("ma", "ma_list"))
            if "close" in script_1:
                val_1 = current_bars[-1].close_price
                val_2 = current_bars[-2].close_price

            if "open" in script_1:
                val_1 = current_bars[-1].open_price
                val_2 = current_bars[-2].open_price

            if val_1 > ma_list[-1] and val_2 <= ma_list[-2]:
                return True
            else:
                return False

        elif "ma" in script_1 and "ma" not in script_2:
            current_bars = self.main_engine.get_current_bars()
            ma_list = eval(script_1.replace("ma", "ma_list"))
            if "close" in script_2:
                val_1 = current_bars[-1].close_price
                val_2 = current_bars[-2].close_price

            if "open" in script_2:
                val_1 = current_bars[-1].open_price
                val_2 = current_bars[-2].open_price

            if ma_list[-1] > val_1 and ma_list[-2] <= val_2:
                return True
            else:
                return False

        elif "ma" in script_1 and "ma" in script_2:
            pass
            ma_list_1 = eval(script_1.replace("ma", "ma_list"))
            ma_list_2 = eval(script_2.replace("ma", "ma_list"))
            if ma_list_1[-1] > ma_list_2[-1] and ma_list_1[-2] <= ma_list_2[-2]:
                return True
            else:
                return False
        else:
            raise Exception("CROSS函数：必须有一个参数为MA函数！")

    # 第1期
    def crossdown(self, *args):
        if len(args) != 2:
            raise Exception("CROSS函数：参数数量错误！")

        script_1 = args[0]
        script_2 = args[1]

        if "ma" not in script_1 and "ma" in script_2:
            current_bars = self.main_engine.get_current_bars()
            ma_list = eval(script_2.replace("ma", "ma_list"))
            if "close" in script_1:
                val_1 = current_bars[-1].close_price
                val_2 = current_bars[-2].close_price

            if "open" in script_1:
                val_1 = current_bars[-1].open_price
                val_2 = current_bars[-2].open_price

            if val_1 < ma_list[-1] and val_2 >= ma_list[-2]:
                return True
            else:
                return False

        elif "ma" not in script_1 and "ma" in script_2:
            current_bars = self.main_engine.get_current_bars()
            ma_list = eval(script_2.replace("ma", "ma_list"))
            if "close" in script_1:
                val_1 = current_bars[-1].close_price
                val_2 = current_bars[-2].close_price

            if "open" in script_1:
                val_1 = current_bars[-1].open_price
                val_2 = current_bars[-2].open_price

            if ma_list[-1] < val_1 and ma_list[-2] >= val_2:
                return True
            else:
                return False

        elif "ma" in script_1 and "ma" in script_2:
            pass
            ma_list_1 = eval(script_1.replace("ma", "ma_list"))
            ma_list_2 = eval(script_2.replace("ma", "ma_list"))
            if ma_list_1[-1] < ma_list_2[-1] and ma_list_1[-2] >= ma_list_2[-2]:
                return True
            else:
                return Falsei

    # 2019/12/3 LongWenHao
    def cross(self, a, b):
        iter_bars = self.main_engine.get_current_bars()
        current_contract = self.get_current_contract(use_df=False)
        tick = self.main_engine.get_current_tick(current_contract)
        print(str(a))
        print(str(b))
        print(tick)
        if self.tick == None:
            self.tick = tick
            ohlc = {'O': "open_price", 'H': "high_price", 'L': "low_price", 'C': "last_price", "V": "volume",
                    'OPEN': "open_price", 'HIGH': "high_price", 'LOW': "low_price", 'CLOSE': "last_price",
                    "VOL": "volume"}
            a_res = None
            b_res = None

            flag_a = str(a)
            flag_a = flag_a.replace("()", "").upper()
            flag_b = str(b)
            flag_b = flag_b.replace("()", "").upper()

            if flag_a in ohlc and flag_b not in ohlc:
                a_res = tick.__getattribute__(ohlc[flag_a])
                b_res = b.exec()
            elif flag_b in ohlc and flag_a not in ohlc:
                b_res = tick.__getattribute__(ohlc[flag_b])
                a_res = a.exec()
            elif flag_b in ohlc and flag_a in ohlc:
                a_res = tick.__getattribute__(ohlc[flag_a])
                b_res = tick.__getattribute__(ohlc[flag_b])
            else:
                a_res = a.exec()
                b_res = b.exec()
            self.tick = tick
            # print(flag_a)
            # print(flag_b)
            print(a_res)
            print(b_res)
            if a_res > b_res:
                self.crossMap[str(a) + ">" + str(b)] = 1
                return 1
            elif a_res < b_res:

                return 0
        # elif self.tick.datetime == tick.datetime:
        #     pass
        else:
            self.tick = tick
            # print(tick)
            ohlc = {'O': "open_price", 'H': "high_price", 'L': "low_price", 'C': "last_price", "V": "volume",
                    'OPEN': "open_price", 'HIGH': "high_price", 'LOW': "low_price", 'CLOSE': "last_price",
                    "VOL": "volume"}
            a_res = None
            b_res = None

            flag_a = str(a)
            flag_a = flag_a.replace("()", "").upper()
            flag_b = str(b)
            flag_b = flag_b.replace("()", "").upper()

            if flag_a in ohlc and flag_b not in ohlc:
                a_res = tick.__getattribute__(ohlc[flag_a])
                b_res = b.exec()
            elif flag_b in ohlc and flag_a not in ohlc:
                b_res = tick.__getattribute__(ohlc[flag_b])
                a_res = a.exec()
            elif flag_b in ohlc and flag_a in ohlc:
                a_res = tick.__getattribute__(ohlc[flag_a])
                b_res = tick.__getattribute__(ohlc[flag_b])
            else:
                a_res = a.exec()
                b_res = b.exec()
            # print(flag_a)
            # print(flag_b)
            print(a_res)
            print(b_res)
            if str(a) + ">" + str(b) in self.crossMap:
                if a_res > b_res and self.crossMap[str(a) + ">" + str(b)] == 0:
                    self.crossMap[str(a) + ">" + str(b)] = 1
                    return 1
                elif a_res < b_res and self.crossMap[str(a) + ">" + str(b)] == 1:
                    self.crossMap[str(a) + ">" + str(b)] = 0
                    return 0
            else:
                if a_res > b_res:
                    self.crossMap[str(a) + ">" + str(b)] = 1
                    return 1
                else:
                    return 0

        # a_list = []
        # b_list = []
        # self.lock_getNew()
        # for i in range(len(iter_bars) - 2, len(iter_bars))[::-1]:
        #     #print(i)
        #     self.running_bar = iter_bars[i]
        #     #print(self.running_bar)
        #     a_res = a.exec()
        #     b_res = b.exec()
        #     a_list.append(a_res)
        #     b_list.append(b_res)
        #     self.ix -= 1
        # print(a_list)
        # print(b_list)
        # self.ix = -1
        # self.unlock_getNew()
        # if a_list[0] > b_list[0]:
        #     if a_list[-1] < b_list[-1]:
        #         return 1
        #     else:
        #         return 0
        # else:
        #     return 0

    # Yangjintao
    # 31
    def daybarpos(self):
        current_bars = self.main_engine.get_current_bars()
        current_bar = current_bars[-1]
        index = 0
        for bar in current_bars:
            if current_bar.datetime.year == bar.datetime.year and \
                    current_bar.datetime.month == bar.datetime.month and \
                    current_bar.datetime.day == bar.datetime.day:
                index += 1
        return index

    # 32
    def daytrade(self):
        pass

    # 2019-10-24 LWH
    # 33
    # 第1期
    def entrysig_place(self, n):
        n = int(n.exec())
        if n == 0 or n == None:
            self.write_log("ENTRYSIG_PLACE函数:n为0或者为空")
            return None
        settings = get_settings("database.")
        database_manager: "BaseDatabaseManager" = init(settings=settings)
        current_contract = self.get_current_contract(use_df=False)
        trades = database_manager.load_trades_by_symbol(current_contract.symbol)
        print(trades)
        current_bars = self.main_engine.get_current_bars()
        # 理论多头持仓
        theory_bk_position = 0
        # 理论空头持仓
        theory_sk_position = 0
        # 开多
        bk_list = []
        # 平空
        sp_list = []
        # 开空
        sk_list = []
        # 平多
        bp_list = []
        # 持仓为0时的记录(表示交易完成的记录)
        positionZero_list = []

        isBk = 0
        for trade in trades:
            if trade.datetime >= self.strategy_start_time:
                # 如果是开多
                if trade.offset == Offset.OPEN and trade.direction == Direction.LONG:
                    bk_list.append(trade)
                    isBk += 1
                    theory_bk_position += trade.volume
                # 如果时平空
                elif trade.offset == Offset.CLOSE and trade.direction == Direction.SHORT:
                    sp_list.append(trade)
                    isBk += 1
                    theory_bk_position -= trade.volume
                    # 如果开多持仓为0，说明是一次完整交易
                if theory_bk_position == 0 and trade == trades[-1]:
                    if len(bk_list) >= n:
                        for bar in current_bars:
                            time = ""
                            # 如果k线周期为d
                            if bar.interval == Interval.DAILY:
                                time = bk_list[n - 1].datetime[0:4] + "-" + bk_list[n - 1].datetime[4:6] + "-" + \
                                       bk_list[
                                           n - 1].datetime[
                                       6:8] + " 00:00:00"
                            elif bar.interval == Interval.HOUR:
                                time = bk_list[n - 1].datetime[0:4] + "-" + bk_list[n - 1].datetime[4:6] + "-" + \
                                       bk_list[
                                           n - 1].datetime[
                                       6:8] + bk_list[
                                                  n - 1].datetime[
                                              8:11] + ":00:00"

                            elif bar.interval == Interval.MINUTE:
                                time = bk_list[n - 1].datetime[0:4] + "-" + bk_list[n - 1].datetime[4:6] + "-" + \
                                       bk_list[
                                           n - 1].datetime[
                                       6:8] + bk_list[
                                                  n - 1].datetime[
                                              8:11] + \
                                       bk_list[n - 1].datetime[11:14] + ":00"

                            if bar.datetime == datetime.strptime(time, "%Y-%m-%d %H:%M:%S"):
                                # 返回离当前k线的周期数
                                return len(current_bars) - 1 - current_bars.index(bar)
                    else:
                        bk_list.clear()
                        sp_list.clear()
                elif theory_bk_position == 0 and trade != trades[-1]:
                    bk_list.clear()
                    sp_list.clear()
                # 当一次完整交易结束后，后面还有交易，且还没结束
                elif theory_bk_position != 0 and trade == trades[-1]:
                    if len(bk_list) >= n:
                        for bar in current_bars:
                            time = ""
                            # 如果k线周期为d
                            if bar.interval == Interval.DAILY:
                                time = bk_list[n - 1].datetime[0:4] + "-" + bk_list[n - 1].datetime[4:6] + "-" + \
                                       bk_list[
                                           n - 1].datetime[
                                       6:8] + " 00:00:00"
                            elif bar.interval == Interval.HOUR:
                                time = bk_list[n - 1].datetime[0:4] + "-" + bk_list[n - 1].datetime[4:6] + "-" + \
                                       bk_list[
                                           n - 1].datetime[
                                       6:8] + bk_list[
                                                  n - 1].datetime[
                                              8:11] + ":00:00"

                            elif bar.interval == Interval.MINUTE:
                                time = bk_list[n - 1].datetime[0:4] + "-" + bk_list[n - 1].datetime[4:6] + "-" + \
                                       bk_list[
                                           n - 1].datetime[
                                       6:8] + bk_list[
                                                  n - 1].datetime[
                                              8:11] + \
                                       bk_list[n - 1].datetime[11:14] + ":00"

                            if bar.datetime == datetime.strptime(time, "%Y-%m-%d %H:%M:%S"):
                                # 返回离当前k线的周期数
                                return len(current_bars) - 1 - current_bars.index(bar)
                    else:
                        self.write_log("ENTRYSIG_PLACE函数：在一次完整交易中信号数不足n个")
                        return None

                if isBk == 0:
                    # 如果是开空
                    if trade.offset == Offset.OPEN and trade.direction == Direction.SHORT:
                        sk_list.append(trade)

                        theory_sk_position += trade.volume
                    # 如果是平多
                    elif trade.offset == Offset.CLOSE and trade.direction == Direction.LONG:
                        bp_list.append(trade)
                        theory_sk_position -= trade.volume
                        # 如果开空持仓为0，说明是一次完整交易
                    if theory_sk_position == 0 and trade == trades[-1]:
                        if len(sk_list) >= n:
                            for bar in current_bars:
                                time = ""
                                # 如果k线周期为d
                                if bar.interval == Interval.DAILY:
                                    time = sk_list[n - 1].datetime[0:4] + "-" + sk_list[n - 1].datetime[4:6] + "-" + \
                                           sk_list[
                                               n - 1].datetime[
                                           6:8] + " 00:00:00"
                                elif bar.interval == Interval.HOUR:
                                    time = sk_list[n - 1].datetime[0:4] + "-" + sk_list[n - 1].datetime[4:6] + "-" + \
                                           sk_list[
                                               n - 1].datetime[
                                           6:8] + sk_list[
                                                      n - 1].datetime[
                                                  8:11] + ":00:00"

                                elif bar.interval == Interval.MINUTE:
                                    time = sk_list[n - 1].datetime[0:4] + "-" + sk_list[n - 1].datetime[4:6] + "-" + \
                                           sk_list[
                                               n - 1].datetime[
                                           6:8] + sk_list[
                                                      n - 1].datetime[
                                                  8:11] + \
                                           sk_list[n - 1].datetime[11:14] + ":00"

                                if bar.datetime == datetime.strptime(time, "%Y-%m-%d %H:%M:%S"):
                                    # 返回离当前k线的周期数
                                    return len(current_bars) - 1 - current_bars.index(bar)
                        else:
                            sk_list.clear()
                            bp_list.clear()
                    elif theory_sk_position == 0 and trade != trades[-1]:
                        sk_list.clear()
                        bp_list.clear()
                    elif theory_bk_position != 0 and trade == trades[-1]:
                        if len(sk_list) >= n:
                            for bar in current_bars:
                                time = ""
                                # 如果k线周期为d
                                if bar.interval == Interval.DAILY:
                                    time = sk_list[n - 1].datetime[0:4] + "-" + sk_list[n - 1].datetime[4:6] + "-" + \
                                           sk_list[
                                               n - 1].datetime[
                                           6:8] + " 00:00:00"
                                elif bar.interval == Interval.HOUR:
                                    time = sk_list[n - 1].datetime[0:4] + "-" + sk_list[n - 1].datetime[4:6] + "-" + \
                                           sk_list[
                                               n - 1].datetime[
                                           6:8] + sk_list[
                                                      n - 1].datetime[
                                                  8:11] + ":00:00"

                                elif bar.interval == Interval.MINUTE:
                                    time = sk_list[n - 1].datetime[0:4] + "-" + sk_list[n - 1].datetime[4:6] + "-" + \
                                           sk_list[
                                               n - 1].datetime[
                                           6:8] + sk_list[
                                                      n - 1].datetime[
                                                  8:11] + \
                                           sk_list[n - 1].datetime[11:14] + ":00"

                                if bar.datetime == datetime.strptime(time, "%Y-%m-%d %H:%M:%S"):
                                    # 返回离当前k线的周期数
                                    return len(current_bars) - 1 - current_bars.index(bar)
                        else:
                            self.write_log("ENTRYSIG_PLACE函数：在一次完整交易中信号数不足n个")
                            return None
        self.write_log("ENTRYSIG_PLACE函数：在一次完整交易中信号数不足n个")
        return None

    # 2019-10-24 LWH
    # 33
    # 第1期
    def entrysig_price(self, n):
        if self.editor_version == '2.0':
            n = n.exec()
        if type(n) != int or n <= 0:
            raise Exception("参数错误：ENTRYSIG_PRICE函数的参数n应为整数并大于0")
        settings = get_settings("database.")
        database_manager: "BaseDatabaseManager" = init(settings=settings)
        current_contract = self.get_current_contract(use_df=False)
        trades = database_manager.load_trades_by_symbol(current_contract.symbol)

        # 理论多头持仓
        theory_bk_position = 0
        # 理论空头持仓
        theory_sk_position = 0
        # 开多
        bk_list = []
        # 平空
        sp_list = []
        # 开空
        sk_list = []
        # 平多
        bp_list = []

        isBk = 0

        for trade in trades:
            if trade.datetime >= self.strategy_start_time:
                # 如果是开多
                if trade.offset == Offset.OPEN and trade.direction == Direction.LONG:
                    bk_list.append(trade)
                    isBk += 1
                    theory_bk_position += trade.volume
                # 如果时平空
                elif trade.offset == Offset.CLOSE and trade.direction == Direction.SHORT:
                    sp_list.append(trade)
                    isBk += 1
                    theory_bk_position -= trade.volume
                # 如果开多持仓为0，说明是一次完整交易
                if theory_bk_position == 0 and trade == trades[-1]:
                    if len(bk_list) >= n:
                        order_id = bk_list[n - 1].orderid
                        order = database_manager.load_order_by_orderid(order_id)
                        return order[0].price
                    else:
                        bk_list.clear()
                        sp_list.clear()
                elif theory_bk_position == 0 and trade != trades[-1]:
                    bk_list.clear()
                    sp_list.clear()
                elif theory_bk_position != 0 and trade == trades[-1]:
                    if len(bk_list) >= n:
                        order_id = bk_list[n - 1].orderid
                        order = database_manager.load_order_by_orderid(order_id)
                        return order[0].price
                    else:
                        self.write_log("ENTRYSIG_PRICE函数：在一次完整交易中信号数不足n个")
                        return None
                if isBk == 0:
                    # 如果是开空
                    if trade.offset == Offset.OPEN and trade.direction == Direction.SHORT:
                        sk_list.append(trade)

                        theory_sk_position += trade.volume
                    # 如果是平多
                    elif trade.offset == Offset.CLOSE and trade.direction == Direction.LONG:
                        bp_list.append(trade)
                        theory_sk_position -= trade.volume
                    # 如果开空持仓为0，说明是一次完整交易
                    if theory_sk_position == 0 and trade == trades[-1]:
                        if len(sk_list) >= n:
                            order_id = sk_list[n - 1].orderid
                            order = database_manager.load_order_by_orderid(order_id)
                            return order[0].price
                        else:
                            sk_list.clear()
                            bp_list.clear()
                    elif theory_sk_position == 0 and trade != trades[-1]:
                        sk_list.clear()
                        bp_list.clear()
                    elif theory_sk_position != 0 and trade == trades[-1]:
                        if len(sk_list) >= n:
                            order_id = sk_list[n - 1].orderid
                            order = database_manager.load_order_by_orderid(order_id)
                            return order[0].price
                        else:
                            self.write_log("ENTRYSIG_PRICE函数：在一次完整交易中信号数不足n个")
                            return None
        self.write_log("ENTRYSIG_PRICE函数：在一次完整交易中信号数不足n个")
        return None

    def entrysig_price1(self, n):
        if self.editor_version == '2.0':
            n = n.exec()
        if type(n) != int or n <= 0:
            raise Exception("参数错误：ENTRYSIG_PRICE1函数的参数n应为整数并大于0")
        settings = get_settings("database.")
        database_manager: "BaseDatabaseManager" = init(settings=settings)
        current_contract = self.get_current_contract(use_df=False)
        trades = database_manager.load_trades_by_symbol(current_contract.symbol)
        # 理论多头持仓
        theory_bk_position = 0
        # 理论空头持仓
        theory_sk_position = 0
        # 开多
        bk_list = []
        # 平空
        sp_list = []
        # 开空
        sk_list = []
        # 平多
        bp_list = []

        isBk = 0

        for trade in trades:
            if trade.datetime >= self.strategy_start_time:
                # 如果是开多
                if trade.offset == Offset.OPEN and trade.direction == Direction.LONG:
                    bk_list.append(trade)

                    theory_bk_position += trade.volume
                # 如果时平空
                elif trade.offset == Offset.CLOSE and trade.direction == Direction.SHORT:
                    sp_list.append(trade)

                    theory_bk_position -= trade.volume
                    # 如果开多持仓为0，说明是一次完整交易
                if theory_bk_position == 0 and trade == trades[-1]:
                    if len(bk_list) >= n:
                        return bk_list[n - 1].price
                    else:
                        bk_list.clear()
                        sp_list.clear()
                elif theory_bk_position == 0 and trade != trades[-1]:
                    bk_list.clear()
                    sp_list.clear()
                elif theory_bk_position != 0 and trade == trades[-1]:
                    if len(bk_list) >= n:
                        return bk_list[n - 1].price
                    else:
                        self.write_log("ENTRYSIG_PRICE1函数：在一次完整交易中信号数不足n个")
                        return None
                if isBk == 0:
                    # 如果是开空
                    if trade.offset == Offset.OPEN and trade.direction == Direction.SHORT:
                        sk_list.append(trade)

                        theory_sk_position += trade.volume
                    # 如果是平多
                    elif trade.offset == Offset.CLOSE and trade.direction == Direction.LONG:
                        bp_list.append(trade)
                        theory_sk_position -= trade.volume
                        # 如果开空持仓为0，说明是一次完整交易
                    if theory_sk_position == 0 and trade == trades[-1]:
                        if len(sk_list) >= n:
                            return sk_list[n - 1].price
                        else:
                            sk_list.clear()
                            bp_list.clear()
                    elif theory_sk_position == 0 and trade != trades[-1]:
                        sk_list.clear()
                        bp_list.clear()
                    elif theory_sk_position != 0 and trade == trades[-1]:
                        if len(sk_list) >= n:
                            return sk_list[n - 1].price
                        else:
                            self.write_log("ENTRYSIG_PRICE1函数：在一次完整交易中信号数不足n个")
                            return None
        self.write_log("ENTRYSIG_PRICE1函数：在一次完整交易中信号数不足n个")
        return None

    # 2019-10-25 LWH
    # 35
    # 委托数
    def entrysig_vol(self, n):
        if self.editor_version == '2.0':
            n = n.exec()
        if type(n) != int or n <= 0:
            raise Exception("参数错误：ENTRYSIG_VOL函数的参数n应为整数并大于0")
        settings = get_settings("database.")
        database_manager: "BaseDatabaseManager" = init(settings=settings)
        current_contract = self.get_current_contract(use_df=False)
        trades = database_manager.load_trades_by_symbol(current_contract.symbol)
        # 理论多头持仓
        theory_bk_position = 0
        # 理论空头持仓
        theory_sk_position = 0
        # 开多
        bk_list = []
        # 平空
        sp_list = []
        # 开空
        sk_list = []
        # 平多
        bp_list = []

        isBk = 0

        for trade in trades:
            if trade.datetime >= self.strategy_start_time:
                # 如果是开多
                if trade.offset == Offset.OPEN and trade.direction == Direction.LONG:
                    bk_list.append(trade)
                    isBk += 1
                    theory_bk_position += trade.volume
                # 如果时平空
                elif trade.offset == Offset.CLOSE and trade.direction == Direction.SHORT:
                    sp_list.append(trade)
                    isBk += 1
                    theory_bk_position -= trade.volume
                # 如果开多持仓为0，说明是一次完整交易
                if theory_bk_position == 0 and trade == trades[-1]:
                    if len(bk_list) >= n:
                        order_id = bk_list[n - 1].orderid
                        order = database_manager.load_order_by_orderid(order_id)
                        return order[0].volume
                    else:
                        bk_list.clear()
                        sp_list.clear()
                elif theory_bk_position == 0 and trade != trades[-1]:
                    bk_list.clear()
                    sp_list.clear()
                elif theory_bk_position != 0 and trade == trades[-1]:
                    if len(bk_list) >= n:
                        order_id = bk_list[n - 1].orderid
                        order = database_manager.load_order_by_orderid(order_id)
                        return order[0].volume
                    else:
                        self.write_log("ENTRYSIG_VOL函数：在一次完整交易中信号数不足n个")
                        return None
                if isBk == 0:
                    # 如果是开空
                    if trade.offset == Offset.OPEN and trade.direction == Direction.SHORT:
                        sk_list.append(trade)

                        theory_sk_position += trade.volume
                    # 如果是平多
                    elif trade.offset == Offset.CLOSE and trade.direction == Direction.LONG:
                        bp_list.append(trade)
                        theory_sk_position -= trade.volume
                    # 如果开空持仓为0，说明是一次完整交易
                    if theory_sk_position == 0 and trade == trades[-1]:
                        if len(sk_list) >= n:
                            order_id = sk_list[n - 1].orderid
                            order = database_manager.load_order_by_orderid(order_id)
                            return order[0].volume
                        else:
                            sk_list.clear()
                            bp_list.clear()
                    elif theory_sk_position == 0 and trade != trades[-1]:
                        sk_list.clear()
                        bp_list.clear()
                    elif theory_sk_position != 0 and trade == trades[-1]:
                        if len(sk_list) >= n:
                            order_id = sk_list[n - 1].orderid
                            order = database_manager.load_order_by_orderid(order_id)
                            return order[0].volume
                        else:
                            self.write_log("ENTRYSIG_VOL函数：在一次完整交易中信号数不足n个")
                            return None
        self.write_log("ENTRYSIG_VOL函数：在一次完整交易中信号数不足n个")
        return None

    def entrysig_vol1(self, n):
        if self.editor_version == '2.0':
            n = n.exec()
        if type(n) != int or n <= 0:
            raise Exception("参数错误：ENTRYSIG_VOL1函数的参数n应为整数并大于0")
        settings = get_settings("database.")
        database_manager: "BaseDatabaseManager" = init(settings=settings)
        current_contract = self.get_current_contract(use_df=False)
        trades = database_manager.load_trades_by_symbol(current_contract.symbol)
        # 理论多头持仓
        theory_bk_position = 0
        # 理论空头持仓
        theory_sk_position = 0
        # 开多
        bk_list = []
        # 平空
        sp_list = []
        # 开空
        sk_list = []
        # 平多
        bp_list = []

        isBk = 0

        for trade in trades:
            if trade.datetime >= self.strategy_start_time:
                # 如果是开多
                if trade.offset == Offset.OPEN and trade.direction == Direction.LONG:
                    bk_list.append(trade)
                    isBk += 1
                    theory_bk_position += trade.volume
                # 如果时平空
                elif trade.offset == Offset.CLOSE and trade.direction == Direction.SHORT:
                    sp_list.append(trade)
                    isBk += 1
                    theory_bk_position -= trade.volume
                # 如果开多持仓为0，说明是一次完整交易
                if theory_bk_position == 0 and trade == trades[-1]:
                    if len(bk_list) >= n:
                        return bk_list[n - 1].volume
                    else:
                        bk_list.clear()
                        sp_list.clear()
                elif theory_bk_position == 0 and trade != trades[-1]:
                    bk_list.clear()
                    sp_list.clear()
                elif theory_bk_position != 0 and trade == trades[-1]:
                    if len(bk_list) >= n:
                        return bk_list[n - 1].volume
                    else:
                        self.write_log("ENTRYSIG_VOL1函数：在一次完整交易中信号数不足n个")
                        return None
                if isBk == 0:
                    # 如果是开空
                    if trade.offset == Offset.OPEN and trade.direction == Direction.SHORT:
                        sk_list.append(trade)

                        theory_sk_position += trade.volume
                    # 如果是平多
                    elif trade.offset == Offset.CLOSE and trade.direction == Direction.LONG:
                        bp_list.append(trade)
                        theory_sk_position -= trade.volume
                    # 如果开空持仓为0，说明是一次完整交易
                    if theory_sk_position == 0 and trade == trades[-1]:
                        if len(sk_list) >= n:
                            return sk_list[n - 1].volume
                        else:
                            sk_list.clear()
                            bp_list.clear()
                    elif theory_sk_position == 0 and trade != trades[-1]:
                        sk_list.clear()
                        bp_list.clear()
                    elif theory_sk_position != 0 and trade == trades[-1]:
                        if len(sk_list) >= n:
                            return sk_list[n - 1].volume
                        else:
                            self.write_log("ENTRYSIG_VOL1函数：在一次完整交易中信号数不足n个")
                            return None
        self.write_log("ENTRYSIG_VOL1函数：在一次完整交易中信号数不足n个")
        return None

    # 36
    def every(self):
        pass

    # 37
    def exist(self):
        pass

    # 2019-10-28 LWH
    # 38
    # 第1期
    def exitsig_place(self, n):
        if self.editor_version == '2.0':
            n = n.exec()
        else:
            n = int(n)
        if type(n) != int or n <= 0:
            raise Exception("参数错误：EXITSIG_PLACE函数的参数n应为整数并大于0")
        settings = get_settings("database.")
        database_manager: "BaseDatabaseManager" = init(settings=settings)
        current_contract = self.get_current_contract(use_df=False)
        trades = database_manager.load_trades_by_symbol(current_contract.symbol)
        current_bars = self.main_engine.get_current_bars()
        # 理论多头持仓
        theory_bk_position = 0
        # 理论空头持仓
        theory_sk_position = 0
        # 开多
        bk_list = []
        # 平空
        sp_list = []
        # 开空
        sk_list = []
        # 平多
        bp_list = []

        isBk = 0
        for trade in trades:
            if trade.datetime >= self.strategy_start_time:
                # 如果是开多
                if trade.offset == Offset.OPEN and trade.direction == Direction.LONG:
                    bk_list.append(trade)
                    isBk += 1
                    theory_bk_position += trade.volume
                # 如果时平空
                elif trade.offset == Offset.CLOSE and trade.direction == Direction.SHORT:
                    sp_list.append(trade)
                    isBk += 1
                    theory_bk_position -= trade.volume
                    # 如果开多持仓为0，说明是一次完整交易
                if theory_bk_position == 0 and trade == trades[-1]:
                    if len(sp_list) >= n:
                        for bar in current_bars:
                            time = ""
                            # 如果k线周期为d
                            if bar.interval == Interval.DAILY:
                                time = sp_list[n - 1].datetime[0:4] + "-" + sp_list[n - 1].datetime[4:6] + "-" + \
                                       sp_list[
                                           n - 1].datetime[
                                       6:8] + " 00:00:00"
                            elif bar.interval == Interval.HOUR:
                                time = sp_list[n - 1].datetime[0:4] + "-" + sp_list[n - 1].datetime[4:6] + "-" + \
                                       sp_list[
                                           n - 1].datetime[
                                       6:8] + sp_list[
                                                  n - 1].datetime[
                                              8:11] + ":00:00"

                            elif bar.interval == Interval.MINUTE:
                                time = sp_list[n - 1].datetime[0:4] + "-" + sp_list[n - 1].datetime[4:6] + "-" + \
                                       sp_list[
                                           n - 1].datetime[
                                       6:8] + sp_list[
                                                  n - 1].datetime[
                                              8:11] + \
                                       sp_list[n - 1].datetime[11:14] + ":00"

                            if bar.datetime == datetime.strptime(time, "%Y-%m-%d %H:%M:%S"):
                                # 返回离当前k线的周期数
                                return len(current_bars) - 1 - current_bars.index(bar)
                    else:
                        bk_list.clear()
                        sp_list.clear()
                elif theory_bk_position == 0 and trade != trades[-1]:
                    bk_list.clear()
                    sp_list.clear()
                # 当一次完整交易结束后，后面还有交易，且还没结束
                elif theory_bk_position != 0 and trade == trades[-1]:
                    if len(sp_list) >= n:
                        for bar in current_bars:
                            time = ""
                            # 如果k线周期为d
                            if bar.interval == Interval.DAILY:
                                time = sp_list[n - 1].datetime[0:4] + "-" + sp_list[n - 1].datetime[4:6] + "-" + \
                                       sp_list[
                                           n - 1].datetime[
                                       6:8] + " 00:00:00"
                            elif bar.interval == Interval.HOUR:
                                time = sp_list[n - 1].datetime[0:4] + "-" + sp_list[n - 1].datetime[4:6] + "-" + \
                                       sp_list[
                                           n - 1].datetime[
                                       6:8] + sp_list[
                                                  n - 1].datetime[
                                              8:11] + ":00:00"

                            elif bar.interval == Interval.MINUTE:
                                time = sp_list[n - 1].datetime[0:4] + "-" + sp_list[n - 1].datetime[4:6] + "-" + \
                                       sp_list[
                                           n - 1].datetime[
                                       6:8] + sp_list[
                                                  n - 1].datetime[
                                              8:11] + \
                                       sp_list[n - 1].datetime[11:14] + ":00"

                            if bar.datetime == datetime.strptime(time, "%Y-%m-%d %H:%M:%S"):
                                # 返回离当前k线的周期数
                                return len(current_bars) - 1 - current_bars.index(bar)
                    else:
                        self.write_log("ENTRYSIG_PLACE函数：在一次完整交易中信号数不足n个")
                        return None

                if isBk == 0:
                    # 如果是开空
                    if trade.offset == Offset.OPEN and trade.direction == Direction.SHORT:
                        sk_list.append(trade)

                        theory_sk_position += trade.volume
                    # 如果是平多
                    elif trade.offset == Offset.CLOSE and trade.direction == Direction.LONG:
                        bp_list.append(trade)
                        theory_sk_position -= trade.volume
                        # 如果开空持仓为0，说明是一次完整交易
                    if theory_sk_position == 0 and trade == trades[-1]:
                        if len(bp_list) >= n:
                            for bar in current_bars:
                                time = ""
                                # 如果k线周期为d
                                if bar.interval == Interval.DAILY:
                                    time = bp_list[n - 1].datetime[0:4] + "-" + bp_list[n - 1].datetime[4:6] + "-" + \
                                           bp_list[
                                               n - 1].datetime[
                                           6:8] + " 00:00:00"
                                elif bar.interval == Interval.HOUR:
                                    time = bp_list[n - 1].datetime[0:4] + "-" + bp_list[n - 1].datetime[4:6] + "-" + \
                                           bp_list[
                                               n - 1].datetime[
                                           6:8] + bp_list[
                                                      n - 1].datetime[
                                                  8:11] + ":00:00"

                                elif bar.interval == Interval.MINUTE:
                                    time = bp_list[n - 1].datetime[0:4] + "-" + bp_list[n - 1].datetime[4:6] + "-" + \
                                           bp_list[
                                               n - 1].datetime[
                                           6:8] + bp_list[
                                                      n - 1].datetime[
                                                  8:11] + \
                                           bp_list[n - 1].datetime[11:14] + ":00"

                                if bar.datetime == datetime.strptime(time, "%Y-%m-%d %H:%M:%S"):
                                    # 返回离当前k线的周期数
                                    return len(current_bars) - 1 - current_bars.index(bar)
                        else:
                            sk_list.clear()
                            bp_list.clear()
                    elif theory_sk_position == 0 and trade != trades[-1]:
                        sk_list.clear()
                        bp_list.clear()
                    elif theory_bk_position != 0 and trade == trades[-1]:
                        if len(bp_list) >= n:
                            for bar in current_bars:
                                time = ""
                                # 如果k线周期为d
                                if bar.interval == Interval.DAILY:
                                    time = bp_list[n - 1].datetime[0:4] + "-" + bp_list[n - 1].datetime[4:6] + "-" + \
                                           bp_list[
                                               n - 1].datetime[
                                           6:8] + " 00:00:00"
                                elif bar.interval == Interval.HOUR:
                                    time = bp_list[n - 1].datetime[0:4] + "-" + bp_list[n - 1].datetime[4:6] + "-" + \
                                           bp_list[
                                               n - 1].datetime[
                                           6:8] + bp_list[
                                                      n - 1].datetime[
                                                  8:11] + ":00:00"

                                elif bar.interval == Interval.MINUTE:
                                    time = bp_list[n - 1].datetime[0:4] + "-" + bp_list[n - 1].datetime[4:6] + "-" + \
                                           bp_list[
                                               n - 1].datetime[
                                           6:8] + bp_list[
                                                      n - 1].datetime[
                                                  8:11] + \
                                           bp_list[n - 1].datetime[11:14] + ":00"

                                if bar.datetime == datetime.strptime(time, "%Y-%m-%d %H:%M:%S"):
                                    # 返回离当前k线的周期数
                                    return len(current_bars) - 1 - current_bars.index(bar)
                        else:
                            self.write_log("EXITSIG_PLACE函数：在一次完整交易中信号数不足n个")
                            return None
        self.write_log("EXITSIG_PLACE函数：在一次完整交易中信号数不足n个")
        return None

    # 2019-10-29 LWH
    # 39
    # 第1期
    def exitsig_price(self, n):
        if self.editor_version == '2.0':
            n = n.exec()
        else:
            n = int(n)
        if type(n) != int or n <= 0:
            raise Exception("EXITSIG_PRICE函数:n为0或者为空")
        settings = get_settings("database.")
        database_manager: "BaseDatabaseManager" = init(settings=settings)
        current_contract = self.get_current_contract(use_df=False)
        trades = database_manager.load_trades_by_symbol(current_contract.symbol)
        # 理论多头持仓
        theory_bk_position = 0
        # 理论空头持仓
        theory_sk_position = 0
        # 开多
        bk_list = []
        # 平空
        sp_list = []
        # 开空
        sk_list = []
        # 平多
        bp_list = []

        isBk = 0

        for trade in trades:
            if trade.datetime >= self.strategy_start_time:
                # 如果是开多
                if trade.offset == Offset.OPEN and trade.direction == Direction.LONG:
                    bk_list.append(trade)
                    isBk += 1
                    theory_bk_position += trade.volume
                # 如果时平空
                elif trade.offset == Offset.CLOSE and trade.direction == Direction.SHORT:
                    sp_list.append(trade)
                    isBk += 1
                    theory_bk_position -= trade.volume
                # 如果开多持仓为0，说明是一次完整交易
                if theory_bk_position == 0 and trade == trades[-1]:
                    if len(sp_list) >= n:
                        order_id = sp_list[n - 1].orderid
                        order = database_manager.load_order_by_orderid(order_id)
                        return order[0].price
                    else:
                        bk_list.clear()
                        sp_list.clear()
                elif theory_bk_position == 0 and trade != trades[-1]:
                    bk_list.clear()
                    sp_list.clear()
                elif theory_bk_position != 0 and trade == trades[-1]:
                    if len(sp_list) >= n:
                        order_id = sp_list[n - 1].orderid
                        order = database_manager.load_order_by_orderid(order_id)
                        return order[0].price
                    else:
                        self.write_log("EXITSIG_PRICE函数：在一次完整交易中信号数不足n个")
                        return None
                if isBk == 0:
                    # 如果是开空
                    if trade.offset == Offset.OPEN and trade.direction == Direction.SHORT:
                        sk_list.append(trade)

                        theory_sk_position += trade.volume
                    # 如果是平多
                    elif trade.offset == Offset.CLOSE and trade.direction == Direction.LONG:
                        bp_list.append(trade)
                        theory_sk_position -= trade.volume
                    # 如果开空持仓为0，说明是一次完整交易
                    if theory_sk_position == 0 and trade == trades[-1]:
                        if len(bp_list) >= n:
                            order_id = bp_list[n - 1].orderid
                            order = database_manager.load_order_by_orderid(order_id)
                            return order[0].price
                        else:
                            sk_list.clear()
                            bp_list.clear()
                    elif theory_sk_position == 0 and trade != trades[-1]:
                        sk_list.clear()
                        bp_list.clear()
                    elif theory_sk_position != 0 and trade == trades[-1]:
                        if len(bp_list) >= n:
                            order_id = bp_list[n - 1].orderid
                            order = database_manager.load_order_by_orderid(order_id)
                            return order[0].price
                        else:
                            self.write_log("EXITSIG_PRICE函数：在一次完整交易中信号数不足n个")
                            return None
        self.write_log("EXITSIG_PRICE函数：在一次完整交易中信号数不足n个")
        return None

    def exitsig_price1(self, n):
        if self.editor_version == '2.0':
            n = n.exec()
        else:
            n = int(n)
        if type(n) != int or n <= 0:
            raise Exception("EXITSIG_PRICE1函数:n为0或者为空")
        settings = get_settings("database.")
        database_manager: "BaseDatabaseManager" = init(settings=settings)
        current_contract = self.get_current_contract(use_df=False)
        trades = database_manager.load_trades_by_symbol(current_contract.symbol)
        # 理论多头持仓
        theory_bk_position = 0
        # 理论空头持仓
        theory_sk_position = 0
        # 开多
        bk_list = []
        # 平空
        sp_list = []
        # 开空
        sk_list = []
        # 平多
        bp_list = []

        isBk = 0

        for trade in trades:
            if trade.datetime >= self.strategy_start_time:
                # 如果是开多
                if trade.offset == Offset.OPEN and trade.direction == Direction.LONG:
                    bk_list.append(trade)
                    isBk += 1
                    theory_bk_position += trade.volume
                # 如果时平空
                elif trade.offset == Offset.CLOSE and trade.direction == Direction.SHORT:
                    sp_list.append(trade)
                    isBk += 1
                    theory_bk_position -= trade.volume
                # 如果开多持仓为0，说明是一次完整交易
                if theory_bk_position == 0 and trade == trades[-1]:
                    if len(sp_list) >= n:
                        return sp_list[n - 1].price
                    else:
                        bk_list.clear()
                        sp_list.clear()
                elif theory_bk_position == 0 and trade != trades[-1]:
                    bk_list.clear()
                    sp_list.clear()
                elif theory_bk_position != 0 and trade == trades[-1]:
                    if len(sp_list) >= n:
                        return sp_list[n - 1].price
                    else:
                        self.write_log("EXITSIG_PRICE1函数：在一次完整交易中信号数不足n个")
                        return None
                if isBk == 0:
                    # 如果是开空
                    if trade.offset == Offset.OPEN and trade.direction == Direction.SHORT:
                        sk_list.append(trade)

                        theory_sk_position += trade.volume
                    # 如果是平多
                    elif trade.offset == Offset.CLOSE and trade.direction == Direction.LONG:
                        bp_list.append(trade)
                        theory_sk_position -= trade.volume
                    # 如果开空持仓为0，说明是一次完整交易
                    if theory_sk_position == 0 and trade == trades[-1]:
                        if len(bp_list) >= n:
                            return bp_list[n - 1].price
                        else:
                            sk_list.clear()
                            bp_list.clear()
                    elif theory_sk_position == 0 and trade != trades[-1]:
                        sk_list.clear()
                        bp_list.clear()
                    elif theory_sk_position != 0 and trade == trades[-1]:
                        if len(bp_list) >= n:
                            return bp_list[n - 1].price
                        else:
                            self.write_log("EXITSIG_PRICE1函数：在一次完整交易中信号数不足n个")
                            return None
        self.write_log("EXITSIG_PRICE1函数：在一次完整交易中信号数不足n个")
        return None

        # 40

    # 2019-10-28 LWH
    # 第1期
    def exitsig_vol(self, n):
        if self.editor_version == '2.0':
            n = n.exec()
        else:
            n = int(n)
        if type(n) != int or n <= 0:
            raise Exception("EXITSIG_VOL函数:n为0或者为空")
        settings = get_settings("database.")
        database_manager: "BaseDatabaseManager" = init(settings=settings)
        current_contract = self.get_current_contract(use_df=False)
        trades = database_manager.load_trades_by_symbol(current_contract.symbol)
        # 理论多头持仓
        theory_bk_position = 0
        # 理论空头持仓
        theory_sk_position = 0
        # 开多
        bk_list = []
        # 平空
        sp_list = []
        # 开空
        sk_list = []
        # 平多
        bp_list = []

        isBk = 0

        for trade in trades:
            if trade.datetime >= self.strategy_start_time:
                # 如果是开多
                if trade.offset == Offset.OPEN and trade.direction == Direction.LONG:
                    bk_list.append(trade)
                    isBk += 1
                    theory_bk_position += trade.volume
                # 如果时平空
                elif trade.offset == Offset.CLOSE and trade.direction == Direction.SHORT:
                    sp_list.append(trade)
                    isBk += 1
                    theory_bk_position -= trade.volume
                # 如果开多持仓为0，说明是一次完整交易
                if theory_bk_position == 0 and trade == trades[-1]:
                    if len(sp_list) >= n:
                        order_id = sp_list[n - 1].orderid
                        order = database_manager.load_order_by_orderid(order_id)
                        return order[0].volume
                    else:
                        bk_list.clear()
                        sp_list.clear()
                elif theory_bk_position == 0 and trade != trades[-1]:
                    bk_list.clear()
                    sp_list.clear()
                elif theory_bk_position != 0 and trade == trades[-1]:
                    if len(sp_list) >= n:
                        order_id = sp_list[n - 1].orderid
                        order = database_manager.load_order_by_orderid(order_id)
                        return order[0].volume
                    else:
                        self.write_log("EXITSIG_VOL函数：在一次完整交易中信号数不足n个")
                        return None
                if isBk == 0:
                    # 如果是开空
                    if trade.offset == Offset.OPEN and trade.direction == Direction.SHORT:
                        sk_list.append(trade)

                        theory_sk_position += trade.volume
                    # 如果是平多
                    elif trade.offset == Offset.CLOSE and trade.direction == Direction.LONG:
                        bp_list.append(trade)
                        theory_sk_position -= trade.volume
                    # 如果开空持仓为0，说明是一次完整交易
                    if theory_sk_position == 0 and trade == trades[-1]:
                        if len(bp_list) >= n:
                            order_id = bp_list[n - 1].orderid
                            order = database_manager.load_order_by_orderid(order_id)
                            return order[0].volume
                        else:
                            sk_list.clear()
                            bp_list.clear()
                    elif theory_sk_position == 0 and trade != trades[-1]:
                        sk_list.clear()
                        bp_list.clear()
                    elif theory_sk_position != 0 and trade == trades[-1]:
                        if len(bp_list) >= n:
                            order_id = bp_list[n - 1].orderid
                            order = database_manager.load_order_by_orderid(order_id)
                            return order[0].volume
                        else:
                            self.write_log("EXITSIG_VOL函数：在一次完整交易中信号数不足n个")
                            return None
        self.write_log("EXITSIG_VOL函数：在一次完整交易中信号数不足n个")
        return None

    def exitsig_vol1(self, n):
        if self.editor_version == '2.0':
            n = n.exec()
        else:
            n = int(n)
        if type(n) != int or n <= 0:
            raise Exception("EXITSIG_VOL1函数:n为0或者为空")
        settings = get_settings("database.")
        database_manager: "BaseDatabaseManager" = init(settings=settings)
        current_contract = self.get_current_contract(use_df=False)
        trades = database_manager.load_trades_by_symbol(current_contract.symbol)
        # 理论多头持仓
        theory_bk_position = 0
        # 理论空头持仓
        theory_sk_position = 0
        # 开多
        bk_list = []
        # 平空
        sp_list = []
        # 开空
        sk_list = []
        # 平多
        bp_list = []

        isBk = 0

        for trade in trades:
            if trade.datetime >= self.strategy_start_time:
                # 如果是开多
                if trade.offset == Offset.OPEN and trade.direction == Direction.LONG:
                    bk_list.append(trade)
                    isBk += 1
                    theory_bk_position += trade.volume
                # 如果时平空
                elif trade.offset == Offset.CLOSE and trade.direction == Direction.SHORT:
                    sp_list.append(trade)
                    isBk += 1
                    theory_bk_position -= trade.volume
                # 如果开多持仓为0，说明是一次完整交易
                if theory_bk_position == 0 and trade == trades[-1]:
                    if len(sp_list) >= n:
                        return sp_list[n - 1].volume
                    else:
                        bk_list.clear()
                        sp_list.clear()
                elif theory_bk_position == 0 and trade != trades[-1]:
                    bk_list.clear()
                    sp_list.clear()
                elif theory_bk_position != 0 and trade == trades[-1]:
                    if len(sp_list) >= n:
                        return sp_list[n - 1].volume
                    else:
                        self.write_log("EXITSIG_VOL1函数：在一次完整交易中信号数不足n个")
                        return None
                if isBk == 0:
                    # 如果是开空
                    if trade.offset == Offset.OPEN and trade.direction == Direction.SHORT:
                        sk_list.append(trade)

                        theory_sk_position += trade.volume
                    # 如果是平多
                    elif trade.offset == Offset.CLOSE and trade.direction == Direction.LONG:
                        bp_list.append(trade)
                        theory_sk_position -= trade.volume
                    # 如果开空持仓为0，说明是一次完整交易
                    if theory_sk_position == 0 and trade == trades[-1]:
                        if len(bp_list) >= n:
                            return bp_list[n - 1].volume
                        else:
                            sk_list.clear()
                            bp_list.clear()
                    elif theory_sk_position == 0 and trade != trades[-1]:
                        sk_list.clear()
                        bp_list.clear()
                    elif theory_sk_position != 0 and trade == trades[-1]:
                        if len(bp_list) >= n:
                            return bp_list[n - 1].volume
                        else:
                            self.write_log("EXITSIG_VOL1函数：在一次完整交易中信号数不足n个")
                            return None
        self.write_log("EXITSIG_VOL1函数：在一次完整交易中信号数不足n个")
        return None

    # 41
    def fee(self):
        account = self.get_current_account()
        return account.commission

    # 42
    def filter(self):
        pass

    # 43
    def hhv(self, x, n):
        x = str(x)
        n = n.exec()
        # 处理参数
        # 判断参数类型
        if type(x) != str or type(n) != int:
            raise Exception("参数类型错误")
        # 去除sig参数的括号
        x = x.replace("()", "")
        # sig字符串变为大写
        x = x.upper()
        ohlc = {'O': "open_price", 'H': "high_price", 'L': "low_price", 'C': "close_price", "V": "volume",
                'OPEN': "open_price", 'HIGH': "high_price", 'LOW': "low_price", 'CLOSE': "close_price",
                "VOL": "volume"}
        p = ""
        if ohlc.keys().__contains__(x):
            p = ohlc[x]
        else:
            raise Exception("HHV函数：参数出错")
        current_bars = self.main_engine.get_current_bars()
        # print(ohlc[x])
        if n == 0:
            # 用于装当前x的列表
            bars = []
            for bar in current_bars:
                bars.append(bar.__getattribute__(p))
            # x条件的最大值
            max_x = max(bars)
            return max_x
        elif n > len(current_bars):
            # 用于装当前x的列表
            bars = []
            for bar in current_bars:
                bars.append(bar.__getattribute__(p))
            # x条件的最大值
            max_x = max(bars)
            return max_x
        elif n == None:
            return None
        # 当n小于bars长度
        else:
            # 用于装当前x的列表
            bars = []
            for bar in current_bars[-n:]:
                bars.append(bar.__getattribute__(p))
            # x条件的最大值
            max_x = max(bars)
            return max_x

    # 44
    # 第1期
    def hv(self, x, n):

        def map_(x):
            if x == "o":
                return "open_price"
            elif x == "h":
                return "high_price"
            elif x == "l":
                return "low_price"
            elif x == "c":
                return "close_price"
            elif x == "v":
                return "volume"
            else:
                return "error"

        # 处理参数
        if self.editor_version == '2.0':
            x = str(x)
            x = x.replace("()", "")
            n = n.exec()

        bars_list = []
        map_res = map_(x.lower())
        if map_res != "error":
            p = map_res
            current_bars = self.main_engine.get_current_bars()
            if current_bars:
                for i in range(1, n):
                    bar = current_bars[-i].__getattribute__(p)
                    bars_list.append(bar)
                return max(bars_list)
            raise Exception("K线不足")
        else:
            raise Exception("无法解析的x参数")

        # if n != None:
        #     if n == 0:
        #         n_cycle = 1
        #     else:
        #         n_cycle = n
        #     # TODO 字符串大小写敏感设置还需要修改
        #     if x == "H":
        #         current_bars = self.main_engine.get_current_bars()
        #         if current_bars:
        #
        #
        #             hs = current_bars[-n_cycle].high_price
        #             return max(hs)
        #     elif x == "C":
        #         current_bars = self.main_engine.get_current_bars()
        #         if current_bars:
        #             hs = current_bars[-n_cycle].close_price
        #             return max(hs)
        #     elif x == "O":
        #         current_bars = self.main_engine.get_current_bars()
        #         if current_bars:
        #             hs = current_bars[-n_cycle].open_price
        #             return max(hs)
        #     elif x == "L":
        #         current_bars = self.main_engine.get_current_bars()
        #         if current_bars:
        #             hs = current_bars[-n_cycle].low_price
        #             return max(hs)
        # else:
        #     return None

    # 2019-10-14 LWH
    # 45
    # 第1期
    def hhvbars(self, x, n):
        x = str(x)
        n = n.exec()
        # 处理参数
        # 判断参数类型
        if type(x) != str or type(n) != int:
            raise Exception("参数类型错误")
        # 去除sig参数的括号
        x = x.replace("()", "")
        # sig字符串变为大写
        x = x.upper()
        ohlc = {'O': "open_price", 'H': "high_price", 'L': "low_price", 'C': "close_price", "V": "volume",
                'OPEN': "open_price", 'HIGH': "high_price", 'LOW': "low_price", 'CLOSE': "close_price",
                "VOL": "volume"}
        p = ""
        if ohlc.keys().__contains__(x):
            p = ohlc[x]
        else:
            raise Exception("HHVBARS函数：参数出错")
        current_bars = self.main_engine.get_current_bars()
        if n == 0:
            # 用于装当前x的列表
            bars = []
            for bar in current_bars[-len(current_bars):-1]:
                bars.append(bar.__getattribute__(p))
            # x条件的最小值
            max_x = max(bars)
            for bar in current_bars[-len(current_bars):-1]:
                if bar.__getattribute__(p) == max_x:
                    return len(current_bars) - current_bars.index(bar) - 1

        elif n > len(current_bars):
            # 用于装当前x的列表
            bars = []
            for bar in current_bars[-len(current_bars):-1]:
                bars.append(bar.__getattribute__(p))
            # x条件的最小值
            max_x = max(bars)
            if current_bars[-1].__getattribute__(p) > max_x:
                return None
            else:
                for bar in current_bars[-len(current_bars):-1]:
                    if bar.__getattribute__(p) == max_x:
                        return len(current_bars) - current_bars.index(bar) - 1
        elif n == None:
            return None
        else:
            # 用于装当前x的列表
            bars = []
            for bar in current_bars[-n:-1]:
                bars.append(bar.__getattribute__(p))
            # x条件的最大值
            max_x = max(bars)
            for bar in current_bars[-n:-1]:
                if bar.__getattribute__(p) == max_x:
                    return len(current_bars) - current_bars.index(bar) - 1

    # 46 if为python关键词
    def iff(self, cond, a, b):
        """
        my语言的if函数实现方式
        :return:
        """
        # @author hengxincheung
        # @time 2019/12/29

        # 得到条件的值
        cond_value = cond.exec()

        # 如果为True或大于0，返回第一个表达式的值
        if (cond_value == True) or (cond_value > 0):
            return a.exec()
        # 如果为False或小于等于0，返回第二个表达式的值
        if (cond_value == False) or (cond_value <= 0):
            return b.exec()
        # 否则，输入表达式不是关系表达式，抛出异常
        raise Exception("错误：表达式 {} 非关系表达式".format(str(cond)))

    # 2019-10-21 LWH
    # 47
    # 第1期
    def initmoney(self):
        # @author hengxincheung
        # @time 2020-01-01
        if self.editor_box != None:
            if self.editor_box.param_dialog != None:
                return self.editor_box.param_dialog.init_money
        return 0

    # 2019-10-14 LWH
    # 48
    # 第1期
    def intpart(self, x):
        x = x.exec()
        return int(x)

    # 49
    def islastbar(self):
        """
        :author: liuzhu
        :time: 2019-10-23

        :return:
        """
        current_bar: TickData = self.main_engine.get_current_bars()[-1]
        bar_time = current_bar.datetime
        now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")[-8]
        # self.write_log("bar_time:{}, now_time:{}".format(bar_time, now_time))
        if (now_time > "09:00:00" and now_time < "11:30:00") or (now_time > "13:30:00" and now_time < "15:00:00"):
            if (datetime.now() - bar_time > timedelta(seconds=1)) and (
                    datetime.now() - bar_time < timedelta(seconds=3)):
                return True
            else:
                return False
        else:
            if bar_time.strftime("%Y-%m-%d %H:%M:%S")[-8] == "11:30:00" or bar_time.strftime("%Y-%m-%d %H:%M:%S")[
                -8] == "13:00:00":
                return True
            else:
                return False

        # current_bar: TickData = self.main_engine.get_current_bars()[-1]
        # bar_time = current_bar.datetime
        # now_time = bar_time.time()
        # self.write_log("bar_time:{}, now_time:{}".format(bar_time, now_time))
        # if (now_time > datetime.time(hour=9, minute=0, second=0, microsecond=0) and now_time < datetime.time(hour=11, minute=30, second=0, microsecond=0)) or \
        #         (now_time > datetime.time(hour=13, minute=30, second=0, microsecond=0) and now_time
        #          < datetime.time(hour=15, minute=0, second=0, microsecond=0)):
        #     if (datetime.now() - bar_time > timedelta(seconds=1)) and (
        #             datetime.now() - bar_time < timedelta(seconds=3)):
        #         return True
        #     else:
        #         return False
        # else:
        #     if now_time == datetime.time(hour=11, minute=30, second=0, microsecond=0) or now_time == datetime.time(hour=15, minute=0, second=0, microsecond=0):
        #         return True
        #     else:
        #         return False

    # 50
    # 第1期
    def islastbk(self):
        """
        author: liuzhu
        time: 2019-10-24
        :return:
        """

        try:
            # current_contract = self.get_current_contract()
            # trades = self.main_engine.get_trades_by_symbol(current_contract.symbol)

            settings = get_settings("database.")
            database_manager: "BaseDatabaseManager" = init(settings=settings)
            current_contract = self.get_current_contract(use_df=False)
            trades = database_manager.load_trades_by_symbol(current_contract.symbol)

            if len(trades):
                # trades.reverse()
                # 判断是不是时间是否大于策略启动时间
                if trades[-1].datetime > self.strategy_start_time:
                    pass
                else:
                    return 0

                if trades[-1].direction == Direction.LONG and trades[-1].offset == Offset.OPEN:
                    return 1
                else:
                    return 0
            else:
                return 0
        except:
            traceback.print_exc()

    # 51
    # 第1期
    def islastsp(self):
        """
        author: liuzhu
        time: 2019-10-24
        :return:
        """
        try:
            # current_contract = self.get_current_contract()
            # # self.write_log(current_contract)
            # trades = self.main_engine.get_trades_by_symbol(current_contract.symbol)

            settings = get_settings("database.")
            database_manager: "BaseDatabaseManager" = init(settings=settings)
            current_contract = self.get_current_contract(use_df=False)
            trades = database_manager.load_trades_by_symbol(current_contract.symbol)

            # self.write_log(trades)
            # last_trade_time = time.strftime('%Y%m%d %H:%M:%S', trades[-1].datetime)

            if len(trades):

                # 判断是不是时间是否大于策略启动时间
                if trades[-1].datetime >= self.strategy_start_time:
                    pass
                else:
                    print("SP 不大于策略时间")
                    return 0

                if trades[-1].direction == Direction.SHORT and trades[-1].offset == Offset.CLOSE:
                    return 1
                else:
                    print("SP 不是sp信号")
                    return 0
            else:
                print("SP 没有交易")
                return 0
        except:
            traceback.print_exc()

    def islastsk(self):
        """
        author: liuzhu
        time: 2019-10-24
        :return:
        """
        try:
            # current_contract = self.get_current_contract()
            # # self.write_log(current_contract)
            # trades = self.main_engine.get_trades_by_symbol(current_contract.symbol)

            settings = get_settings("database.")
            database_manager: "BaseDatabaseManager" = init(settings=settings)
            current_contract = self.get_current_contract(use_df=False)
            trades = database_manager.load_trades_by_symbol(current_contract.symbol)

            # self.write_log(trades)
            if len(trades):
                # print(trades)
                # self.write_log(trades)
                # self.write_log(trades)
                # trades.reverse()
                # 判断是不是时间是否大于策略启动时间
                if trades[-1].datetime > self.strategy_start_time:
                    pass
                else:
                    return 0

                if trades[-1].direction == Direction.SHORT and trades[-1].offset == Offset.OPEN:
                    return 1
                else:
                    return 0
            else:
                return 0
        except:
            traceback.print_exc()

    def islastbp(self):
        """
        author: liuzhu
        time: 2019-10-24
        :return:
        """
        try:
            # current_contract = self.get_current_contract()
            # # self.write_log(current_contract)
            # trades = self.main_engine.get_trades_by_symbol(current_contract.symbol)

            settings = get_settings("database.")
            database_manager: "BaseDatabaseManager" = init(settings=settings)
            current_contract = self.get_current_contract(use_df=False)
            trades = database_manager.load_trades_by_symbol(current_contract.symbol)

            # self.write_log(trades)
            if len(trades):
                # print(trades)
                # self.write_log(trades)
                # self.write_log(trades)
                # trades.reverse()
                # 判断是不是时间是否大于策略启动时间
                if trades[-1].datetime > self.strategy_start_time:
                    pass
                else:
                    return 0

                if trades[-1].direction == Direction.LONG and trades[-1].offset == Offset.CLOSE:
                    return 1
                else:
                    return 0
            else:
                return 0
        except:
            traceback.print_exc()

    # 52
    def islastcloseout(self):
        pass

    # 53
    def klinesig(self):
        pass

    # Yangjintao
    # 54
    def last(self, *args):
        if len(args) != 3:
            raise Exception("LAST函数：参数数量错误！")
            # self.stop_strategy()
        arg_1 = args[0]
        arg_2 = args[1]
        arg_3 = args[2]
        try:
            start = int(arg_2)
            end = int(arg_3)
            if start <= end:
                raise Exception("LAST函数：参数错误，第二个必须大于第三参数！")
                # self.stop_strategy()
            print(arg_1)
            if (self.count(arg_1, start) - self.count(arg_1, end)) == (start - end):
                return 1
            else:
                return 0
        except:
            raise Exception("LAST函数：参数错误，第二个和第三参数必须为整数！")
            # self.stop_strategy()

    # 55
    def lastoffsetprofit(self):
        """
        author: liuzhu
        date: 2019-10-27
        :return:
        """
        try:
            current_contract = self.get_current_contract(use_df=False)
            trades = self.main_engine.get_trades_by_symbol(current_contract.symbol)
            if len(trades):
                trades.reverse()
                for trade in trades:
                    if trade.offset == Offset.CLOSE:
                        return trade.price
                    else:
                        pass
                return "no close"
            else:
                return "no trades"
        except:
            traceback.print_exc()

    # @Author : Yangjintao
    # @Time : 2019.10.14
    # 56
    def lastsig(self):
        # 最近一个信号
        current_contract = self.get_current_contract(use_df=False)
        trades = self.main_engine.get_trades_by_symbol(current_contract.symbol)

        if len(trades) > 0:
            trade = trades[-1]
            # bK 200
            if trade.offset == Offset.OPEN and trade.direction == Direction.LONG:
                return 200
            # sk 201
            elif trade.offset == Offset.OPEN and trade.direction == Direction.SHORT:
                return 201
            # bp 202
            elif trade.offset == Offset.CLOSE and trade.direction == Direction.LONG:
                return 202
            # sp 203
            elif trade.offset == Offset.CLOSE and trade.direction == Direction.SHORT:
                return 203
            else:
                return
        else:
            self.write_log("最近没有交易信号！")

    # 2019-10-16 LWH
    # 57
    def llv(self, x, n):
        x = str(x)
        n = n.exec()
        # 处理参数
        # 判断参数类型
        if type(x) != str or type(n) != int:
            raise Exception("参数类型错误")
        # 去除sig参数的括号
        x = x.replace("()", "")
        # sig字符串变为大写
        x = x.upper()
        ohlc = {'O': "open_price", 'H': "high_price", 'L': "low_price", 'C': "close_price", "V": "volume",
                'OPEN': "open_price", 'HIGH': "high_price", 'LOW': "low_price", 'CLOSE': "close_price",
                "VOL": "volume"}
        p = ""
        if ohlc.keys().__contains__(x):
            p = ohlc[x]
        else:
            raise Exception("LLV函数：参数出错")
        current_bars = self.main_engine.get_current_bars()
        # print(ohlc[x])
        n = int(n)
        if n == 0:
            # 用于装当前x的列表
            bars = []
            for bar in current_bars:
                bars.append(bar.__getattribute__(p))
            # x条件的最小值
            min_x = min(bars)
            return min_x
        elif n > len(current_bars):
            # 用于装当前x的列表
            bars = []
            for bar in current_bars:
                bars.append(bar.__getattribute__(p))
            # x条件的最小值
            min_x = min(bars)
            if current_bars[-1].__getattribute__(p) < min_x:
                return None
        elif n == None:
            return None
        # 当n小于bars长度
        else:
            # 用于装当前x的列表
            bars = []
            for bar in current_bars[-n:]:
                bars.append(bar.__getattribute__(p))
            # x条件的最小值
            min_x = min(bars)
            return min_x

    # 2019/10/11 LongWenHao
    # 58 不包含当前k线
    # 第1期
    def lv(self, x, n):
        x = str(x)
        n = n.exec()
        # 处理参数
        # 判断参数类型
        if type(x) != str or type(n) != int:
            raise Exception("参数类型错误")
        # 去除sig参数的括号
        x = x.replace("()", "")
        # sig字符串变为大写
        x = x.upper()
        ohlc = {'O': "open_price", 'H': "high_price", 'L': "low_price", 'C': "close_price", "V": "volume",
                'OPEN': "open_price", 'HIGH': "high_price", 'LOW': "low_price", 'CLOSE': "close_price",
                "VOL": "volume"}
        p = ""
        if ohlc.keys().__contains__(x):
            p = ohlc[x]
        else:
            raise Exception("LV函数：参数出错")
        current_bars = self.main_engine.get_current_bars()
        # print(ohlc[x])
        n = int(n)
        if n == 0:
            # 用于装当前x的列表
            bars = []
            for bar in current_bars[-len(current_bars):-1]:
                bars.append(bar.__getattribute__(p))
            # x条件的最小值
            min_x = min(bars)
            return min_x
        elif n > len(current_bars):
            # 用于装当前x的列表
            bars = []
            for bar in current_bars[-len(current_bars):-1]:
                bars.append(bar.__getattribute__(p))
            # x条件的最小值
            min_x = min(bars)
            if current_bars[-1].__getattribute__(p) < min_x:
                return None
            else:
                return min_x
        elif n == None:
            return None
        else:
            # 用于装当前x的列表
            bars = []
            for bar in current_bars[-n:-1]:
                bars.append(bar.__getattribute__(p))
            # x条件的最小值
            min_x = min(bars)
            return min_x

    # 2019/10/11 LongWenHao
    # 59
    # 第1期
    def llvbars(self, x, n):
        x = str(x)
        n = n.exec()
        # 处理参数
        # 判断参数类型
        if type(x) != str or type(n) != int:
            raise Exception("参数类型错误")
        # 去除sig参数的括号
        x = x.replace("()", "")
        # sig字符串变为大写
        x = x.upper()
        ohlc = {'O': "open_price", 'H': "high_price", 'L': "low_price", 'C': "close_price", "V": "volume",
                'OPEN': "open_price", 'HIGH': "high_price", 'LOW': "low_price", 'CLOSE': "close_price",
                "VOL": "volume"}
        p = ""
        n = int(n)
        if ohlc.keys().__contains__(x):
            p = ohlc[x]
        else:
            raise Exception("LLVBARS函数：参数出错")
        current_bars = self.main_engine.get_current_bars()
        if n == 0:
            # 用于装当前x的列表
            bars = []
            for bar in current_bars[-len(current_bars):-1]:
                bars.append(bar.__getattribute__(p))
            # x条件的最小值
            min_x = min(bars)
            for bar in current_bars[-len(current_bars):-1]:
                if bar.__getattribute__(p) == min_x:
                    return len(current_bars) - current_bars.index(bar) - 1

        elif n > len(current_bars):
            # 用于装当前x的列表
            bars = []
            for bar in current_bars[-len(current_bars):-1]:
                bars.append(bar.__getattribute__(p))
            # x条件的最小值
            min_x = min(bars)
            if current_bars[-1].__getattribute__(p) < min_x:
                return None
            else:
                for bar in current_bars[-len(current_bars):-1]:
                    if bar.__getattribute__(p) == min_x:
                        return len(current_bars) - current_bars.index(bar) - 1
        elif n == None:
            return None
        else:
            # 用于装当前x的列表
            bars = []
            for bar in current_bars[-n:-1]:
                bars.append(bar.__getattribute__(p))
            # x条件的最小值
            min_x = min(bars)
            for bar in current_bars[-n:-1]:
                if bar.__getattribute__(p) == min_x:
                    return len(current_bars) - current_bars.index(bar) - 1

    # 60
    def loop2(self):
        pass

    # 2019-10-15 LWH
    # 61
    # 第1期
    def max(self, *args):
        tmp = [arg.exec() for arg in args]
        return max(tmp)

    # 2019/9/29 LongWenHao
    # 62
    # 第1期
    def ma(self, x, n):
        period = n.exec()
        x = str(x)
        x = x.replace("()", "").upper()
        current_contract = self.get_current_contract(use_df=False)
        # print(current_contract)
        # tick = self.main_engine.get_current_tick(current_contract)
        # if self.tick == None:
        self.tick = self.main_engine.get_current_tick(current_contract)
        iter_bars = self.main_engine.get_current_bars()
        # print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        # print(iter_bars[-5:])

        res = 0
        if self.tick:
            if x == "C":
                print(iter_bars)
                for p in range(period + 1):
                    if p != 0 and p != 1:
                        res += iter_bars[-p].close_price

                res = (res + self.tick.last_price) / period
            elif x == "H":
                for p in range(period + 1):
                    if p != 0 and p != 1:
                        res += iter_bars[-p].high_price

                res = (res + self.tick.high_price) / period
            elif x == "O":
                for p in range(period + 1):
                    if p != 0 and p != 1:
                        res += iter_bars[-p].open_price

                res = (res + self.tick.open_price) / period
            elif x == "L":
                for p in range(period + 1):
                    if p != 0 and p != 1:
                        res += iter_bars[-p].low_price

                res = (res + self.tick.low_price) / period
            # print(res)
            return res

        # name = ""
        # # 得到周期数
        # period = n.exec()
        # # 画图
        # if type(x) == Variable:
        #     iter_bars = self.main_engine.get_current_bars()
        #     # print(iter_bars[-1])
        #     result = []
        #     # self.getNew = False
        #     for bar in iter_bars:
        #         self.running_bar = bar
        #         # 在当前k线上执行输入的表达式
        #         output = x.exec()
        #         # 添加进结果列表
        #         result.append(output)
        #     for r in result:
        #         r = float(r)
        #     temp = np.array(result)
        #     result = talib.MA(temp, period)
        #
        #     for var_name in RunEnvironment.run_vars.keys():
        #         s = "{}".format(var_name)
        #         variable = RunEnvironment.run_vars[s]
        #         if variable.operator == ":":
        #             name = var_name
        #             # print(name)
        #             d = {"name": name, "period": period, "sma": result}
        #             event = Event(EVENT_MA, d)
        #             self.event_engine.put(event)
        #             res_return = result[period - 1:][self.ix]
        #             if res_return == None:
        #                 return 0.0
        #             else:
        #                 return res_return
        #
        #         else:
        #             res_return = result[period - 1:][self.ix]
        #             if res_return == None:
        #                 return 0.0
        #             else:
        #                 return res_return
        #
        #
        # else:
        #     # 得到表达式字符串
        #     flag_str = str(x)
        #     flag_str = flag_str.replace("()", "").upper()
        #     # 判断周期数类型，如果不为整型则报错
        #     if type(period) != int:
        #         raise Exception("MA函数周期必须为整型")
        #     # 判断周期数大小不能小于等于1，否则报错
        #     if period <= 1:
        #         raise Exception("MA函数周期大小必须大于1")
        #     try:
        #         expr = get_current_expr()
        #         if RunEnvironment.run_vars.keys():
        #             for var_name in RunEnvironment.run_vars.keys():
        #                 s = "{}".format(var_name)
        #                 variable = RunEnvironment.run_vars[s]
        #                 # print(variable.operands[0])
        #                 if variable.operands[0] == expr:
        #                     name = s
        #                     if flag_str == "H":
        #                         high_price = self.h_list()
        #                         temp = np.array(high_price)
        #                         result = talib.MA(temp, period)
        #                         if variable.operator == ":":
        #                             d = {"name": name, "period": period, "sma": result}
        #                             event = Event(EVENT_MA, d)
        #                             self.event_engine.put(event)
        #                         else:
        #                             res_return = result[period - 1:][self.ix]
        #                             if res_return == None:
        #                                 return 0.0
        #                             else:
        #                                 return res_return
        #
        #                     elif flag_str == "L" in flag_str:
        #                         low_price = self.l_list()
        #                         temp = np.array(low_price)
        #                         result = talib.MA(temp, period)
        #                         if variable.operator == ":":
        #                             d = {"name": name, "period": period, "sma": result}
        #                             event = Event(EVENT_MA, d)
        #                             self.event_engine.put(event)
        #                         else:
        #                             res_return = result[period - 1:][self.ix]
        #                             if res_return == None:
        #                                 return 0.0
        #                             else:
        #                                 return res_return
        #
        #                     elif flag_str == "O" in flag_str:
        #                         open_price = self.o_list()
        #                         temp = np.array(open_price)
        #                         result = talib.MA(temp, period)
        #                         if variable.operator == ":":
        #                             d = {"name": name, "period": period, "sma": result}
        #                             event = Event(EVENT_MA, d)
        #                             self.event_engine.put(event)
        #                         else:
        #                             res_return = result[period - 1:][self.ix]
        #                             if res_return == None:
        #                                 return 0.0
        #                             else:
        #                                 return res_return
        #
        #                     elif flag_str == "C" in flag_str:
        #                         close_price = self.c_list()
        #                         # self.write_log(len(close_price))
        #                         temp = np.array(close_price)
        #                         result = talib.MA(temp, period)
        #                         if variable.operator == ":":
        #                             d = {"name": name, "period": period, "sma": result}
        #                             event = Event(EVENT_MA, d)
        #                             self.event_engine.put(event)
        #                             res_return = result[period - 1:][self.ix]
        #                             if res_return == None:
        #                                 return 0.0
        #                             else:
        #                                 return res_return
        #
        #                         else:
        #                             res_return = result[period - 1:][self.ix]
        #                             if res_return == None:
        #                                 return 0.0
        #                             else:
        #                                 return res_return
        #
        #
        #         else:
        #             if flag_str == "H":
        #                 high_price = self.h_list()
        #                 temp = np.array(high_price)
        #                 result = talib.MA(temp, period)
        #                 res_return = result[period - 1:][self.ix]
        #                 if res_return == None:
        #                     return 0.0
        #                 else:
        #                     return res_return
        #
        #
        #             elif flag_str == "L" in flag_str:
        #                 low_price = self.l_list()
        #                 temp = np.array(low_price)
        #                 result = talib.MA(temp, period)
        #                 return result[period - 1:][self.ix]
        #             elif flag_str == "O" in flag_str:
        #                 open_price = self.o_list()
        #                 temp = np.array(open_price)
        #                 result = talib.MA(temp, period)
        #                 res_return = result[period - 1:][self.ix]
        #                 if res_return == None:
        #                     return 0.0
        #                 else:
        #                     return res_return
        #
        #             elif flag_str == "C" in flag_str:
        #                 close_price = self.c_list()
        #                 temp = np.array(close_price)
        #                 result = talib.MA(temp, period)
        #                 print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        #                 print(result)
        #                 print(len(result))
        #                 res_return = result[period - 1:][self.ix]
        #                 if res_return == None:
        #                     return 0.0
        #                 else:
        #                     return res_return
        #
        #     except:
        #         if "ValueError" in traceback.format_exc():
        #             self.write_log("MA函数：周期参数为必须为数字！")
        #         return 0.0
        # return 0.0

    # 返回值为List，供其他函数调用
    def ma_list(self, flag_str, period_str):
        # flag_str = re.sub("a_list", "a", flag_str)
        period_str = int(period_str)

        try:
            if "." in period_str:
                period = float(period_str)
            else:
                period = int(period_str)

            if period <= 1:
                self.write_log("MA_LIST函数：周期参数要大于1！")
                return

            current_bars = self.main_engine.get_current_bars()
            am = ArrayManager()
            for bar in current_bars:
                am.update_bar(bar)

            if flag_str == "self.editor_engine.h()":
                return am.sma("h", period, array=True)
            elif flag_str == "self.editor_engine.l()" in flag_str:
                return am.sma("l", period, array=True)
            elif flag_str == "self.editor_engine.o()" in flag_str:
                return am.sma("o", period, array=True)
            elif flag_str == "self.editor_engine.c()" in flag_str:
                return am.sma("c", period, array=True)
        except:
            if "ValueError" in traceback.format_exc():
                self.write_log("MA函数：周期参数为必须为数字！")
            return

    # 2019-10-15 LWH
    # 63
    # 第1期
    def min(self, *args):
        tmp = [arg.exec() for arg in args]
        return min(tmp)

    # 64
    def minute(self, vt_symbol):
        """
        :author: liuzhu
        :time: 2019-10-22
        :param vt_symbol:
        :return:
        """
        tick = self.get_tick(vt_symbol=vt_symbol)
        tick_time = tick.datetime.minute
        return int(tick_time)

    # 65
    # 第1期
    def minpriced(self, symbol):
        if type(symbol) != str:
            # 参数检查
            symbol = symbol.exec()
        if type(symbol) != str:
            raise Exception('第{}行: 参数错误, symbol类型应为str，输入类型为:{}'.format(get_current_expr().lineno, type(symbol)))
        contract = self.main_engine.contracts.get(symbol.lower(), None)
        if contract:
            pricetick = contract.pricetick / contract.size
            size = contract.size
            return size * pricetick
        contract = self.main_engine.contracts.get(symbol.upper(), None)
        if contract:
            pricetick = contract.pricetick / contract.size
            size = contract.size
            return size * pricetick
        raise Exception("第{}行: 未找到合约 {} 相关信息,请检查网络或配置信息".format(get_current_expr().lineno, symbol))

    # 66
    def money(self):
        pass

    # 67
    def moneyratio(self):
        pass

    # 68
    # 第1期
    def moneyreal(self):
        pass

    # 69
    # 第1期
    def moneytot(self):
        pass

    # 70
    def multsig(self):
        pass

    # 71
    # def not(self):
    #     pass
    def nott(self, x):
        """
        对麦语言函数中的not函数的重写
        author liuzhu
        date: 20191206
        :param x:
        :return:
        """
        if self.editor_version == "2.0":
            x = x.exec()
        return not x

    # 72
    # 第1期
    def offsetprofit(self):
        """
        @ autho : liuzhu
        @ time : 2020.1.15
        @ description: 计算平仓盈亏
        :return:
        """
        try:
            if len(RunEnvironment.run_trade):

                trade_first: "TradeData" = RunEnvironment.run_trade[0]
                mean_price = trade_first.price
                init_vol = trade_first.volume
                res_profit = 0
                if trade_first.direction == Direction.LONG and trade_first.offset == Offset.OPEN:
                    for index, trade in enumerate(RunEnvironment.run_trade):
                        if index == 0:
                            # 跳过第一个trade
                            continue
                        # 当交易信号为BK的时候，更新均价和总的BKVOL
                        if trade.direction == Direction.LONG and trade.offset == Offset.OPEN:
                            mean_price = ((mean_price * init_vol) + (trade.price * trade.volume)) / (
                                    init_vol + trade.volume)
                            init_vol = init_vol + trade.volume
                        # 当交易信号为SP的时候，计算profit并更新init_vol
                        if trade.direction == Direction.SHORT and trade.offset == Offset.CLOSE:
                            res_profit = (trade.price - mean_price) * trade.volume * self.unit()
                            init_vol = init_vol - trade.volume

                elif trade_first.direction == Direction.SHORT and trade_first.offset == Offset.OPEN:
                    for index, trade in enumerate(RunEnvironment.run_trade):
                        if index == 0:
                            # 跳过第一个trade
                            continue
                        # 当交易信号为SK的时候，更新均价和总的SK的交易量
                        if trade.direction == Direction.SHORT and trade.offset == Offset.OPEN:
                            mean_price = ((mean_price * init_vol) + (trade.price * trade.volume)) / (
                                    init_vol + trade.volume)
                            init_vol = init_vol + trade.volume
                        # 当交易信号为BP的时候，计算profit并更新init_vol
                        if trade.direction == Direction.LONG and trade.offset == Offset.CLOSE:
                            res_profit = (mean_price - trade.price) * trade.volume * self.unit()
                            init_vol = init_vol - trade.volume

                else:
                    # self.write_log("初始交易函数不为BK和SK")
                    print("初始交易函数不为BK和SK")
                    return 0

                return res_profit

            else:
                # self.write_log("没有交易信号")
                print("没有交易信号")
                return 0
        except:
            traceback.print_exc()

    # 73
    def openminute(self):
        pass

    # 74
    def profit(self):
        pass

    # 75
    def peak(self):
        pass

    # 76
    def peakbars(self):
        pass

    # 2019/10/4 LongWenHao
    # 77
    # 第1期
    def ref(self, *args):
        if len(args) != 2:
            raise Exception("REF函数：参数必须为2个！")

        try:
            flag_str = str(args[0])
            period_str = args[1].exec()
            flag_str = flag_str.replace("()", "").upper()

            period = int(period_str)

            if period < 0:
                self.write_log("REF函数：周期参数必须大于0！")
                return

            ohlc = {'O': "open_price",
                    'H': "high_price",
                    'L': "low_price",
                    'C': "close_price",
                    "V": "volume",
                    'OPEN': "open_price",
                    'HIGH': "high_price",
                    'LOW': "low_price",
                    'CLOSE': "close_price",
                    "VOL": "volume"
                    }

            if ohlc.keys().__contains__(flag_str):

                current_bars = self.main_engine.get_current_bars()
                value = ohlc[flag_str]
                if len(current_bars) < period:
                    raise Exception("REF函数：K线数量小于参数！")
                if period < 0:
                    current_bars[-1].__getattribute__(value)
                return current_bars[-period].__getattribute__(value)
            else:
                self.ix = -period
                return args[0].exec()
        except:
            if "ValueError" in traceback.format_exc():
                raise Exception("REF函数：周期参数为必须为数字！")

    # 78
    # 第1期
    def refsig_place(self, sig, n):
        # 得到参数sig的字面量
        sig = str(sig)
        # 得到参数n的值
        n = n.exec()
        # 判断参数类型
        if type(sig) != str:
            raise Exception("第{}行: 参数错误, sig类型应该为str，输入类型为{}".format(get_current_expr().lineno, type(str)))
        # 处理sig信号类型
        # sig字符串变为大写
        sig = sig.upper()
        # self.write_log("统计的信号为: {}".format(sig))
        # 判断信号类型是否合规定
        if sig not in ["BK()", "SK()", "BP()", "SP()"]:
            raise Exception("第{}行: 参数错误, sig仅支持BK、SK、BP、SP,输入信号为:{}".format(get_current_expr().lineno, sig))
        # 参数n类型判断
        if type(n) != int:
            raise Exception("第{}行: 参数错误, n类型应该为整型，输入类型为:{}".format(get_current_expr().lineno, type(n)))
        if n == 0:
            return 0
        # 获取当前合约
        current_contract = self.editor_engine.current_contract
        # 获取k线数组
        current_bars = self.main_engine.get_current_bars()

        # 获取交易
        settings = get_settings("database.")
        database_manager: "BaseDatabaseManager" = init(settings=settings)
        trades = database_manager.load_trades_by_symbol(current_contract.symbol)

        print(self.strategy_start_time)
        # 统计指定的信号
        trade_list = []
        for trade in trades:
            if trade.datetime < self.strategy_start_time:
                continue
            if sig == "BK()":
                if trade.direction == Direction.LONG and trade.offset == Offset.OPEN:
                    trade_list.append(trade)
            elif sig == "SK()":
                if trade.direction == Direction.SHORT and trade.offset == Offset.OPEN:
                    trade_list.append(trade)
            elif sig == "BP()":
                if trade.direction == Direction.LONG and trade.offset == Offset.CLOSE:
                    trade_list.append(trade)
            elif sig == "SP()":
                if trade.direction == Direction.SHORT and trade.offset == Offset.CLOSE:
                    trade_list.append(trade)
        # 打印统计的信号
        # self.write_log("共有 {} 个 {} 信号".format(len(trade_list), sig))
        if len(trade_list) < n:
            return None
        trade = trade_list[-n]
        for bar in current_bars:
            # 获取k线周期
            interval = bar.interval.value
            # 计算一个bar的时间
            next_datetime = bar.datetime
            if interval[-1] == 'd':
                next_datetime += dt.timedelta(days=1)
            elif interval[-1] == 'w':
                next_datetime += dt.timedelta(days=7)
            elif interval[-1] == 'h':
                next_datetime += dt.timedelta(hours=int(interval[:-1]))
            elif interval[-1] == 'm':
                next_datetime += dt.timedelta(minutes=int(interval[:-1]))
            else:
                continue
            if bar.datetime <= datetime.strptime(trade.datetime, "%Y%m%d %H:%M:%S") <= next_datetime:
                return len(current_bars) - current_bars.index(bar)
        return None

    # 79
    # 第1期
    # 返回倒数第n个信号的成交价
    def refsig_price1(self, sig, n):
        # 得到参数sig的字面量
        sig = str(sig)
        # 得到参数n的值
        n = n.exec()
        # 判断参数类型
        if type(sig) != str:
            raise Exception("第{}行: 参数错误, sig类型应该为str，输入类型为{}".format(get_current_expr().lineno, type(str)))
        # 处理sig信号类型
        # sig字符串变为大写
        sig = sig.upper()
        # self.write_log("统计的信号为: {}".format(sig))
        # 判断信号类型是否合规定
        if sig not in ["BK()", "SK()", "BP()", "SP()"]:
            raise Exception("第{}行: 参数错误, sig仅支持BK、SK、BP、SP,输入信号为:{}".format(get_current_expr().lineno, sig))
        # 参数n类型判断
        if type(n) != int:
            raise Exception("第{}行: 参数错误, n类型应该为整型，输入类型为:{}".format(get_current_expr().lineno, type(n)))
        if n == 0:
            return None
        # 获取当前合约
        current_contract = self.editor_engine.current_contract
        # 获取交易
        settings = get_settings("database.")
        database_manager: "BaseDatabaseManager" = init(settings=settings)
        trades = database_manager.load_trades_by_symbol(current_contract.symbol)
        # 统计指定的信号
        trade_list = []
        for trade in trades:
            if trade.datetime < self.strategy_start_time:
                continue
            if sig == "BK()":
                if trade.direction == Direction.LONG and trade.offset == Offset.OPEN:
                    trade_list.append(trade)
            elif sig == "SK()":
                if trade.direction == Direction.SHORT and trade.offset == Offset.OPEN:
                    trade_list.append(trade)
            elif sig == "BP()":
                if trade.direction == Direction.LONG and trade.offset == Offset.CLOSE:
                    trade_list.append(trade)
            elif sig == "SP()":
                if trade.direction == Direction.SHORT and trade.offset == Offset.CLOSE:
                    trade_list.append(trade)
        # 打印统计的信号
        # self.write_log("共有 {} 个 {} 信号".format(len(trade_list), sig))
        if n < len(trade_list):
            return trade_list[-n].price
        else:
            return None

    # 返回倒数第n个信号的信号价
    def refsig_price(self, sig, n):
        # 得到参数sig的字面量
        sig = str(sig)
        # 得到参数n的值
        n = n.exec()
        # 判断参数类型
        if type(sig) != str:
            raise Exception("第{}行: 参数错误, sig类型应该为str，输入类型为{}".format(get_current_expr().lineno, type(str)))
        # 处理sig信号类型
        # sig字符串变为大写
        sig = sig.upper()
        # self.write_log("统计的信号为: {}".format(sig))
        # 判断信号类型是否合规定
        if sig not in ["BK()", "SK()", "BP()", "SP()"]:
            raise Exception("第{}行: 参数错误, sig仅支持BK、SK、BP、SP,输入信号为:{}".format(get_current_expr().lineno, sig))
        # 参数n类型判断
        if type(n) != int:
            raise Exception("第{}行: 参数错误, n类型应该为整型，输入类型为:{}".format(get_current_expr().lineno, type(n)))
        if n == 0:
            return None
        # 获取当前合约
        current_contract = self.editor_engine.current_contract
        # # 获取交易
        # settings = get_settings("database.")
        # database_manager: "BaseDatabaseManager" = init(settings=settings)
        # trades = database_manager.load_trades_by_symbol(current_contract.symbol)
        # 统计指定的信号
        trade_list = []
        for trade in self.trade_successful_oder:
            # if trade.datetime < self.strategy_start_time:
            #     continue
            if sig == "BK()":
                if trade.direction == Direction.LONG and trade.offset == Offset.OPEN:
                    trade_list.append(trade)
            elif sig == "SK()":
                if trade.direction == Direction.SHORT and trade.offset == Offset.OPEN:
                    trade_list.append(trade)
            elif sig == "BP()":
                if trade.direction == Direction.LONG and trade.offset == Offset.CLOSE:
                    trade_list.append(trade)
            elif sig == "SP()":
                if trade.direction == Direction.SHORT and trade.offset == Offset.CLOSE:
                    trade_list.append(trade)
        # 打印统计的信号
        # self.write_log("共有 {} 个 {} 信号".format(len(trade_list), sig))
        if n <= len(trade_list):
            # # 获取订单号
            # order_id = trade_list[-n].orderid
            # # 根据订单号查询订单
            # orders = database_manager.load_order_by_orderid(order_id)
            # # 如果存在则返回
            # if len(orders) > 0:
            #     return orders[0].price
            # else:
            #     return None
            return trade_list[-n].price
        else:
            return None

    # 80
    # 第1期
    # 取委托手数
    def refsig_vol(self, sig, n):
        # 得到参数sig的字面量
        sig = str(sig)
        # 得到参数n的值
        n = n.exec()
        # 判断参数类型
        if type(sig) != str:
            raise Exception("第{}行: 参数错误, sig类型应该为str，输入类型为{}".format(get_current_expr().lineno, type(str)))
        # 处理sig信号类型
        # sig字符串变为大写
        sig = sig.upper()
        # self.write_log("统计的信号为: {}".format(sig))
        # 判断信号类型是否合规定
        if sig not in ["BK()", "SK()", "BP()", "SP()"]:
            raise Exception("第{}行: 参数错误, sig仅支持BK、SK、BP、SP,输入信号为:{}".format(get_current_expr().lineno, sig))
        # 参数n类型判断
        if type(n) != int:
            raise Exception("第{}行: 参数错误, n类型应该为整型，输入类型为:{}".format(get_current_expr().lineno, type(n)))
        if n == 0:
            return None
        # 获取当前合约
        current_contract = self.editor_engine.current_contract
        # # 获取交易
        # settings = get_settings("database.")
        # database_manager: "BaseDatabaseManager" = init(settings=settings)
        # trades = database_manager.load_trades_by_symbol(current_contract.symbol)
        # 统计指定的信号
        trade_list = []
        for trade in self.trade_oder:
            # if trade.datetime < self.strategy_start_time:
            #     continue
            if sig == "BK()":
                if trade.direction == Direction.LONG and trade.offset == Offset.OPEN:
                    trade_list.append(trade)
            elif sig == "SK()":
                if trade.direction == Direction.SHORT and trade.offset == Offset.OPEN:
                    trade_list.append(trade)
            elif sig == "BP()":
                if trade.direction == Direction.LONG and trade.offset == Offset.CLOSE:
                    trade_list.append(trade)
            elif sig == "SP()":
                if trade.direction == Direction.SHORT and trade.offset == Offset.CLOSE:
                    trade_list.append(trade)
        # 打印统计的信号
        # self.write_log("共有 {} 个 {} 信号".format(len(trade_list), sig))
        if n <= len(trade_list):
            # # 获取订单号
            # order_id = trade_list[-n].orderid
            # # 根据订单号查询订单
            # orders = database_manager.load_order_by_orderid(order_id)
            # # 如果存在则返回
            # if len(orders) > 0:
            #     return orders[0].price
            # else:
            #     return None
            return trade_list[-n].volume
        else:
            return None

    # 取成交手数
    def refsig_vol1(self, sig, n):
        # 得到参数sig的字面量
        sig = str(sig)
        # 得到参数n的值
        n = n.exec()
        # 判断参数类型
        if type(sig) != str:
            raise Exception("第{}行: 参数错误, sig类型应该为str，输入类型为{}".format(get_current_expr().lineno, type(str)))
        # 处理sig信号类型
        # sig字符串变为大写
        sig = sig.upper()
        # self.write_log("统计的信号为: {}".format(sig))
        # 判断信号类型是否合规定
        if sig not in ["BK()", "SK()", "BP()", "SP()"]:
            raise Exception("第{}行: 参数错误, sig仅支持BK、SK、BP、SP,输入信号为:{}".format(get_current_expr().lineno, sig))
        # 参数n类型判断
        if type(n) != int:
            raise Exception("第{}行: 参数错误, n类型应该为整型，输入类型为:{}".format(get_current_expr().lineno, type(n)))
        if n == 0:
            return None
        # 获取当前合约
        current_contract = self.editor_engine.current_contract
        # # 获取交易
        # settings = get_settings("database.")
        # database_manager: "BaseDatabaseManager" = init(settings=settings)
        # trades = database_manager.load_trades_by_symbol(current_contract.symbol)
        # 统计指定的信号
        trade_list = []
        for trade in self.trade_successful_oder:
            # if trade.datetime < self.strategy_start_time:
            #     continue
            if sig == "BK()":
                if trade.direction == Direction.LONG and trade.offset == Offset.OPEN:
                    trade_list.append(trade)
            elif sig == "SK()":
                if trade.direction == Direction.SHORT and trade.offset == Offset.OPEN:
                    trade_list.append(trade)
            elif sig == "BP()":
                if trade.direction == Direction.LONG and trade.offset == Offset.CLOSE:
                    trade_list.append(trade)
            elif sig == "SP()":
                if trade.direction == Direction.SHORT and trade.offset == Offset.CLOSE:
                    trade_list.append(trade)
        # 打印统计的信号
        # self.write_log("共有 {} 个 {} 信号".format(len(trade_list), sig))
        if n <= len(trade_list):
            # # 获取订单号
            # order_id = trade_list[-n].orderid
            # # 根据订单号查询订单
            # orders = database_manager.load_order_by_orderid(order_id)
            # # 如果存在则返回
            # if len(orders) > 0:
            #     return orders[0].price
            # else:
            #     return None
            return trade_list[-n].volume
        else:
            return None

    # 2019-10-31 LWH
    # 81
    def refx(self, x, n):
        x = str(x)
        n = n.exec()
        # 去除sig参数的括号
        x = x.replace("()", "")
        # sig字符串变为大写
        x = x.upper()
        # 处理参数
        # 判断参数类型
        if type(x) != str or type(n) != int:
            self.write_log("参数类型错误")
            return 0
        ohlc = {'O': "open_price", 'H': "high_price", 'L': "low_price", 'C': "close_price", "V": "volume",
                'OPEN': "open_price", 'HIGH': "high_price", 'LOW': "low_price", 'CLOSE': "close_price",
                "VOL": "volume"}
        current_bars = self.main_engine.get_current_bars()
        # print(ohlc[x])
        if n == 0:
            # 用于装当前x的列表
            bars = []
            for bar in current_bars:
                bars.append(bar.__getattribute__(ohlc[x]))
            return bars[-1]
        elif n > len(current_bars):
            # 用于装当前x的列表
            bars = []
            for bar in current_bars:
                bars.append(bar.__getattribute__(ohlc[x]))
            return bars[0]
        elif n == None:
            return None
        # 当n小于bars长度
        else:
            # 用于装当前x的列表
            bars = []
            for bar in current_bars:
                bars.append(bar.__getattribute__(ohlc[x]))
            return bars[-n]

    # 2019/10/4 LongWenHao
    # 82
    # 第1期
    def round(self, n, m):
        n = n.exec()
        m = m.exec()
        if m < 0:
            self.write_log("ROUND函数：参数出错，不能为负数")
            return
        if m == 0:
            return int(n)
        n = str(n)
        past = n[n.index(".") + 1:len(n)]
        if len(past) % 2 != 0:
            n = float(n)
            n = round(n * 10 * (len(past) - 2), len(past) - 2)
            return n / ((len(past) - 2) * 10)
        else:
            n = float(n)
            return round(n, m)

    # 83
    def stockdivd(self):
        pass

    # 84
    def setexpiredate(self):
        pass

    # 85
    def settle(self):
        pass

    # 86
    def setdealpercent(self):
        pass

    # 2019-10-29 LWH
    # 87
    # 第1期
    # def signum(self):
    #     #run_trade = RunEnvironment.run_trade
    #     settings = get_settings("database.")
    #     database_manager: "BaseDatabaseManager" = init(settings=settings)
    #     current_contract = self.get_current_contract(use_df=False)
    #     trades = database_manager.load_trades_by_symbol(current_contract.symbol)
    #     if len(trades) == 0:
    #         self.write_log("SIGNUM函数：当前期货未进行过交易")
    #         return
    #     isBK = False
    #     isBP = False
    #     # 持仓为0时的记录(表示交易完成的记录)
    #     positionZero_list = []
    #     current_bars = self.main_engine.get_current_bars()
    #     dt_ix_map = {}
    #     for ix, bar in enumerate(current_bars):
    #         dt_ix_map[bar.datetime] = ix
    #     firstTime = current_bars[0].datetime
    #     sig = 0
    #     bk_time = None
    #     bp_time = None
    #     info = {}
    #     for bar in current_bars:
    #         info[int(dt_ix_map[bar.datetime])] = float(0)
    #     for trade in trades:
    #         Time = trade.datetime[0:4] + "-" + trade.datetime[4:6] + "-" + trade.datetime[
    #                                                                        6:8] + trade.datetime[
    #                                                                               8:11] + \
    #                trade.datetime[11:14] + ":00"
    #         if trade.datetime >= self.strategy_start_time \
    #                 and isBP == False and trade.offset == Offset.OPEN \
    #                 and trade.direction == Direction.LONG\
    #                 and trade.symbol == current_contract.symbol\
    #                 and datetime.strptime(
    #                 Time, '%Y-%m-%d %H:%M:%S') in dt_ix_map:
    #
    #             if isBK == True:
    #                 sig += 1
    #             isBK = True
    #             info[int(dt_ix_map[datetime.strptime(Time, '%Y-%m-%d %H:%M:%S')])] = sig
    #         elif trade.datetime >= self.strategy_start_time\
    #                 and isBK == True and datetime.strptime(Time, '%Y-%m-%d %H:%M:%S') in dt_ix_map \
    #                 and trade.offset == Offset.CLOSE\
    #                 and trade.direction == Direction.SHORT:
    #             sig += 1
    #             info[int(dt_ix_map[datetime.strptime(Time, '%Y-%m-%d %H:%M:%S')])] = sig
    #         if trade.datetime >= self.strategy_start_time\
    #                 and isBK == False and trade.offset == Offset.OPEN\
    #                 and trade.direction == Direction.SHORT\
    #                 and trade.symbol == current_contract.symbol\
    #                 and datetime.strptime(Time, '%Y-%m-%d %H:%M:%S') in dt_ix_map:
    #
    #             if isBP == True:
    #                 sig += 1
    #             isBP = True
    #             info[int(dt_ix_map[datetime.strptime(Time, '%Y-%m-%d %H:%M:%S')])] = sig
    #         elif trade.datetime >= self.strategy_start_time\
    #                 and isBP == True and datetime.strptime(Time, '%Y-%m-%d %H:%M:%S') in dt_ix_map \
    #                 and trade.offset == Offset.CLOSE and trade.direction == Direction.LONG:
    #             sig += 1
    #             info[int(dt_ix_map[datetime.strptime(Time, '%Y-%m-%d %H:%M:%S')])] = sig
    #     if RunEnvironment.run_vars.keys():
    #         for var_name in RunEnvironment.run_vars.keys():
    #             s = "{}".format(var_name)
    #             variable = RunEnvironment.run_vars[s]
    #             # print(variable.operands[0])
    #             if variable.operator == ":":
    #                 variable_name = s
    #                 event = Event(EVENT_INFO, {"name": variable_name, "data": info})
    #                 self.event_engine.put(event)
    #                 return info[int(dt_ix_map[current_bars[-1].datetime])]
    #             elif variable.operator == ":=":
    #                 return info[int(dt_ix_map[current_bars[-1].datetime])]
    #     return info[int(dt_ix_map[current_bars[-1].datetime])]

    def signum(self):
        settings = get_settings("database.")
        database_manager: "BaseDatabaseManager" = init(settings=settings)
        current_contract = self.get_current_contract(use_df=False)
        trades = database_manager.load_trades_by_symbol(current_contract.symbol)

        # 理论多头持仓
        theory_bk_position = 0
        # 理论空头持仓
        theory_sk_position = 0
        # 开多
        bk_list = []
        # 平空
        sp_list = []
        # 开空
        sk_list = []
        # 平多
        bp_list = []

        sigs = []
        isBk = 0

        for trade in trades:
            if trade.datetime >= self.strategy_start_time:
                # 如果是开多
                if trade.offset == Offset.OPEN and trade.direction == Direction.LONG:
                    bk_list.append(trade)
                    sigs.append(trade)
                    theory_bk_position += trade.volume
                    isBk += 1

                # 如果时平空
                elif trade.offset == Offset.CLOSE and trade.direction == Direction.SHORT:
                    sp_list.append(trade)
                    sigs.append(trade)
                    theory_bk_position -= trade.volume
                    isBk += 1

                # 如果开多持仓为0，说明是一次完整交易
                if theory_bk_position == 0 and trade == trades[-1]:
                    return len(sigs)
                elif theory_bk_position == 0 and trade != trades[-1]:
                    sigs.clear()
                elif theory_bk_position != 0 and trade == trades[-1]:

                    return len(sigs)

                if isBk == 0:
                    # 如果是开空
                    if trade.offset == Offset.OPEN and trade.direction == Direction.SHORT:
                        sk_list.append(trade)
                        sigs.append(trade)
                        theory_sk_position += trade.volume
                    # 如果是平多
                    elif trade.offset == Offset.CLOSE and trade.direction == Direction.LONG:
                        bp_list.append(trade)
                        sigs.append(trade)
                        theory_sk_position -= trade.volume
                    # 如果开空持仓为0，说明是一次完整交易
                    if theory_sk_position == 0 and trade == trades[-1]:
                        return len(sigs)
                    elif theory_sk_position == 0 and trade != trades[-1]:
                        sigs.clear()
                    elif theory_sk_position != 0 and trade == trades[-1]:
                        return len(sigs)
        self.write_log("SIGNUM函数：无交易信号")
        return None

    # 2019/10/2 LongWenHao
    # 88
    # 第1期
    # def sigvol(self, n):
    #     if self.editor_version == '2.0':
    #         n = n.exec()
    #     settings = get_settings("database.")
    #     database_manager: "BaseDatabaseManager" = init(settings=settings)
    #     current_contract = self.get_current_contract(use_df=False)
    #     trades = database_manager.load_trades_by_symbol(current_contract.symbol)
    #     if len(trades) == 0:
    #         self.write_log("SIGVOL函数：当前期货未进行过交易")
    #         return
    #     isBK = False
    #     isBP = False
    #     # 持仓为0时的记录(表示交易完成的记录)
    #     current_bars = self.main_engine.get_current_bars()
    #     dt_ix_map = {}
    #     for ix, bar in enumerate(current_bars):
    #         dt_ix_map[bar.datetime] = ix
    #     firstTime = current_bars[0].datetime
    #     volume = 0
    #     bk_time = None
    #     bp_time = None
    #     info = {}
    #     for bar in current_bars:
    #         info[int(dt_ix_map[bar.datetime])] = float(0)
    #     for trade in trades:
    #         Time = trade.datetime[0:4] + "-" + trade.datetime[4:6] + "-" + trade.datetime[
    #                                                                        6:8] + trade.datetime[
    #                                                                               8:11] + \
    #                trade.datetime[11:14] + ":00"
    #
    #         if trade.datetime >= self.strategy_start_time\
    #                 and isBP == False and trade.offset == Offset.OPEN \
    #                 and trade.direction == Direction.LONG and trade.symbol == current_contract.symbol\
    #                 and datetime.strptime(Time, '%Y-%m-%d %H:%M:%S') in dt_ix_map:
    #
    #             if isBK == True:
    #                 volume = trade.volume
    #             isBK = True
    #             info[int(dt_ix_map[datetime.strptime(Time, '%Y-%m-%d %H:%M:%S')])] = volume
    #         elif trade.datetime >= self.strategy_start_time\
    #                 and isBK == True \
    #                 and datetime.strptime(Time, '%Y-%m-%d %H:%M:%S') in dt_ix_map\
    #                 and trade.offset == Offset.CLOSE and trade.direction == Direction.SHORT:
    #             volume = trade.volume
    #             info[int(dt_ix_map[datetime.strptime(Time, '%Y-%m-%d %H:%M:%S')])] = volume
    #         if trade.datetime >= self.strategy_start_time\
    #                 and isBK == False and trade.offset == Offset.OPEN \
    #                 and trade.direction == Direction.SHORT and trade.symbol == current_contract.symbol \
    #                 and datetime.strptime(Time, '%Y-%m-%d %H:%M:%S') in dt_ix_map:
    #
    #
    #             if isBP == True:
    #                 volume = trade.volume
    #             isBP = True
    #             info[int(dt_ix_map[datetime.strptime(Time, '%Y-%m-%d %H:%M:%S')])] = volume
    #         elif trade.datetime >= self.strategy_start_time\
    #                 and isBP == True \
    #                 and datetime.strptime(Time, '%Y-%m-%d %H:%M:%S') in dt_ix_map \
    #                 and trade.offset == Offset.CLOSE and trade.direction == Direction.LONG:
    #             volume = trade.volume
    #             info[int(dt_ix_map[datetime.strptime(Time, '%Y-%m-%d %H:%M:%S')])] = volume
    #     if len(info) < n:
    #         self.write_log("SIGVOL函数：信号数不足n个")
    #         return
    #     if RunEnvironment.run_vars.keys():
    #         for var_name in RunEnvironment.run_vars.keys():
    #             s = "{}".format(var_name)
    #             variable = RunEnvironment.run_vars[s]
    #             # print(variable.operands[0])
    #             if variable.operator == ":":
    #                 variable_name = s
    #                 event = Event(EVENT_INFO, {"name": variable_name, "data": info})
    #                 self.event_engine.put(event)
    #                 return info[n-1]
    #             elif variable.operator == ":=":
    #                 return info[n-1]
    #     return info[n-1]

    def sigvol(self, n):
        if self.editor_version == '2.0':
            n = n.exec()
        if type(n) != int or n <= 0:
            raise Exception("参数错误：SIGVOL函数的参数n应为整数并大于0")
        settings = get_settings("database.")
        database_manager: "BaseDatabaseManager" = init(settings=settings)
        current_contract = self.get_current_contract(use_df=False)
        trades = database_manager.load_trades_by_symbol(current_contract.symbol)

        # 理论多头持仓
        theory_bk_position = 0
        # 理论空头持仓
        theory_sk_position = 0
        # 开多
        bk_list = []
        # 平空
        sp_list = []
        # 开空
        sk_list = []
        # 平多
        bp_list = []

        sigs = []

        isBk = 0

        for trade in trades:
            if trade.datetime >= self.strategy_start_time:
                # 如果是开多
                if trade.offset == Offset.OPEN and trade.direction == Direction.LONG:
                    bk_list.append(trade)
                    sigs.append(trade)
                    theory_bk_position += trade.volume
                    isBk += 1
                # 如果时平空
                elif trade.offset == Offset.CLOSE and trade.direction == Direction.SHORT:
                    sp_list.append(trade)
                    sigs.append(trade)
                    theory_bk_position -= trade.volume
                    isBk += 1
                # 如果开多持仓为0，说明是一次完整交易
                if theory_bk_position == 0 and trade == trades[-1]:
                    if len(sigs) >= n:

                        return sigs[n - 1].volume
                    else:
                        bk_list.clear()
                        sp_list.clear()
                        sigs.clear()
                elif theory_bk_position == 0 and trade != trades[-1]:
                    bk_list.clear()
                    sp_list.clear()
                    sigs.clear()
                elif theory_bk_position != 0 and trade == trades[-1]:
                    if len(sigs) >= n:
                        return sigs[n - 1].volume
                    else:
                        self.write_log("SIGVOL函数：在一次完整交易中信号数不足n个")
                        return None

                if isBk == 0:
                    # 如果是开空
                    if trade.offset == Offset.OPEN and trade.direction == Direction.SHORT:
                        sk_list.append(trade)
                        sigs.append(trade)
                        theory_sk_position += trade.volume
                    # 如果是平多
                    elif trade.offset == Offset.CLOSE and trade.direction == Direction.LONG:
                        bp_list.append(trade)
                        sigs.append(trade)
                        theory_sk_position -= trade.volume
                    # 如果开空持仓为0，说明是一次完整交易
                    if theory_sk_position == 0 and trade == trades[-1]:
                        if len(sigs) >= n:
                            return sigs[n - 1].volume
                        else:
                            sk_list.clear()
                            bp_list.clear()
                            sigs.clear()
                    elif theory_sk_position == 0 and trade != trades[-1]:
                        sk_list.clear()
                        bp_list.clear()
                        sigs.clear()
                    elif theory_sk_position != 0 and trade == trades[-1]:
                        if len(sigs) >= n:
                            return sigs[n - 1].volume
                        else:
                            self.write_log("SIGVOL函数：在一次完整交易中信号数不足n个")
                            return None
        self.write_log("SIGVOL函数：在一次完整交易中信号数不足n个")
        return None

    # 2019/10/4 LongWenHao
    # 89
    # 第1期
    def sum(self, x, n):
        x = str(x)
        n = n.exec()
        # 处理参数
        # 判断参数类型
        if type(x) != str or type(n) != int:
            self.write_log("参数类型错误")
            return 0
        # 去除sig参数的括号
        x = x.replace("()", "")
        # sig字符串变为大写
        x = x.upper()
        ohlc = {'O': "open_price", 'H': "high_price", 'L': "low_price", 'C': "close_price", "V": "volume",
                'OPEN': "open_price", 'HIGH': "high_price", 'LOW': "low_price", 'CLOSE': "close_price",
                "VOL": "volume"}
        current_bars = self.main_engine.get_current_bars()
        sum = 0
        n = int(n)
        if n < 0:
            self.write_log("SUM函数：参数出错，不能为负数")
            return
        if n == 0:
            return current_bars[-1].__getattribute__(ohlc[x])
        elif len(current_bars) < n:
            for row in current_bars:
                sum += row.__getattribute__(ohlc[x])
            return sum
        else:
            for row in current_bars[-n:]:
                sum += row.__getattribute__(ohlc[x])
            return sum

    # 2019-10-16 LWH
    # 90
    def sumbars(self, x, a):
        x = str(x)
        a = a.exec()
        # 处理参数
        # 判断参数类型
        if type(x) != str or type(a) != int:
            raise Exception("参数类型错误")
        a = float(a)
        # 去除sig参数的前缀
        x = x.replace("self.editor_engine.", "")
        # 去除sig参数的括号
        x = x.replace("()", "")
        # sig字符串变为大写
        x = x.upper()
        ohlc = {'O': "open_price", 'H': "high_price", 'L': "low_price", 'C': "close_price", "V": "volume",
                'OPEN': "open_price", 'HIGH': "high_price", 'LOW': "low_price", 'CLOSE': "close_price",
                "VOL": "volume"}
        current_bars = self.main_engine.get_current_bars()
        sum = 0
        for i in range(len(current_bars)):
            if sum >= a:
                return i
            sum += float(current_bars[-(i + 1)].__getattribute__(ohlc[x]))

    # 91
    # 第1期
    # def time(self):
    #
    #     hour = datetime.now().hour
    #     min = datetime.now().minute
    #     return hour*100+min

    # 2019/10/3 LongWenHao
    # 92
    def tmaxwin(self):
        position = self.get_all_positions(use_df=True)
        if max(position["pnl"].values) > 0:
            return max(position["pnl"].values)

    # 2019/10/3 LongWenHao
    # 93
    def tmaxloss(self):
        position = self.get_all_positions(use_df=True)
        if min(position["pnl"].values) < 0:
            return abs(min(position["pnl"].values))
        # print(max(position["pnl"].values))

    # 2019/10/3 LongWenHao
    # 94
    def tmaxseqloss(self):
        position = self.get_all_positions(use_df=True)
        count = 0
        loss = []
        for pnl in position["pnl"].values:
            if pnl < 0:
                count += 1
            else:
                loss.append(count)
                count = 0
        return abs(min(loss))

    # 2019/10/3 LongWenHao
    # 95
    def tmaxseqwin(self):
        position = self.get_all_positions(use_df=True)
        count = 0
        win = []
        for pnl in position["pnl"].values:
            if pnl > 0:
                count += 1
            else:
                win.append(count)
                count = 0
        return max(win)

    # 2019/10/3 LongWenHao
    # 因信号消失产生的盈亏、交易次数未纳入TNUMSEQLOSS 的计算?
    # 96
    def tnumseqloss(self):
        position = self.get_all_positions(use_df=True)
        count = 0
        loss = []
        for pnl in position["pnl"].values:
            if pnl < 0:
                count += 1
            else:
                loss.append(count)
                count = 0
        return len(loss)

    # 2019/10/3 LongWenHao
    # 因信号消失产生的盈亏、交易次数未纳入TNUMSEQWIN 的计算。
    # 97
    def tnumsseqwin(self):
        position = self.get_all_positions(use_df=True)
        count = 0
        win = []
        for pnl in position["pnl"].values:
            if pnl > 0:
                count += 1
            else:
                win.append(count)
                count = 0
        return len(win)

    # 98
    def trade_again(self, n):
        """
        : author liuzhu
        : date 2019-11-29
        :param n: 交易函数需要运行的次数
        :return:
        """
        # liuzhu
        # 20191224
        if self.editor_version == '2.0':
            n = n.exec()
        line_num = get_current_expr().lineno
        if len(self.trade_again_time_list) and line_num <= self.trade_again_time_list[-1]:
            pass
        else:
            self.trade_again_time_list.append(line_num)
            self.trade_count_list.append(n - 1)
            self.trade_again_init.append(n)

    def trade_again_init_in_restart_strategy(self):

        self.trade_count_list = list(self.trade_again_init)

        # if self.iteration_count != 1:
        #     return
        # else:
        #     if self.trade_count['BK'] == 0:
        #         self.trade_count['BK'] = n-1
        #     if self.trade_count['SP'] == 0:
        #         self.trade_count['SP'] = n-1
        #     if self.trade_count['SK'] == 0:
        #         self.trade_count['SK'] = n-1
        #     if self.trade_count['BP'] == 0:
        #         self.trade_count['BP'] = n-1
        #
        #     return

    # 99
    def trade_ref(self):
        pass

    # 2019/10/3 LongWenHao
    # 100
    def tseqloss(self):
        position = self.get_all_positions(use_df=True)
        loss = []
        loss_sum = 0
        for pnl in position["pnl"].values:
            if pnl < 0:
                loss_sum += pnl
            else:
                loss.append(loss_sum)
                loss_sum = 0
        return abs(min(loss))

    # 101
    def troughbars(self):
        pass

    # 2019/10/3 LongWenHao
    # 102
    def tseqwin(self):
        position = self.get_all_positions(use_df=True)
        win = []
        win_sum = 0
        for pnl in position["pnl"].values:
            if pnl > 0:
                win_sum += pnl
            else:
                win.append(win_sum)
                win_sum = 0
        return max(win)

    # Yangjintao
    # 103
    def unit(self):
        current_contract = self.get_current_contract()
        return current_contract.size

    # @Author : Yangjintao
    # @Time : 2019.10.15
    # 104
    def valuewhen(self, cond, x):
        try:
            tmp = cond.exec()
        except Exception as err:
            raise Exception("未识别的表达式：" + f"{err}")
        if tmp:
            return x.exec()
        else:
            bars = self.main_engine.get_current_bars()
            self.lock_getNew()
            for bar in bars[::-1]:
                if self.running_bar != bar:
                    self.running_bar = bar
                    self.ix -= 1
                    try:
                        tmp = cond.exec()
                    except Exception as err:
                        raise Exception("未识别的表达式：" + f"{err}")
                    if tmp:
                        self.ix = -1
                        return x.exec()
            self.unlock_getNew()
        self.write_log("未找到满足条件的周期")
        return None

    # 105
    def volmargin(self):
        pass

    # 106
    def wavepeak(self):
        pass

    # 107
    def call(self, cond, sig):
        ohlc = {'O': "open_price", 'H': "high_price", 'L': "low_price", 'C': "close_price", "V": "volume",
                'OPEN': "open_price", 'HIGH': "high_price", 'LOW': "low_price", 'CLOSE': "close_price",
                "VOL": "volume"}
        cond = re.sub("\(", "_list(", cond)
        funcs = re.split(">|<|<>|==", cond)
        # 目前只有一个运算符时可以计算
        operator = re.findall(r'[<>\<\>|==]', cond)[0]
        list1 = eval(funcs[0])
        list2 = eval(funcs[1])
        res = self.oper(list1, list2, operator)

        sig = sig.replace("self.editor_engine.", "")
        # 去除sig参数的括号
        sig = sig.replace("()", "")
        # sig字符串变为大写
        sig = sig.upper()
        sig = sig.replace(" ", "")
        num = sig[sig.index("(") + 1:sig.index(",")]
        num = int(num)
        price = sig[sig.index(",") + 1:sig.index(")")]
        trades = []
        current_bars = self.main_engine.get_current_bars()
        for a in res[0]:
            trades.append(current_bars[a])
        # print(trades)

        data = {"trades": trades, "sig": sig[0:2], "num": num, "price": ohlc[price]}
        event = Event(EVENT_SCATTER, data)
        self.event_engine.put(event)

    # 108
    # def import(self):
    #     pass

    # 109
    def call_plus(self):
        print('c_test')

    def clear_long(self):
        long_positions = self.main_engine.get_long_positions()
        print(long_positions)
        for p in long_positions:
            if p.volume != 0:
                current_tick = self.get_tick(p.symbol)
                minpriced = self.minpriced(p.symbol)
                status = self.send_order(current_tick, current_tick.bid_price_1 - 30, p.volume, Direction.SHORT,
                                         Offset.CLOSE)

    def clear_short(self):
        short_positions = self.main_engine.get_short_positions()
        for p in short_positions:
            if p.volume != 0:
                current_tick = self.get_tick(p.symbol)
                minpriced = self.minpriced(p.symbol)

                status = self.send_order(current_tick, current_tick.bid_price_1 + 30, p.volume, Direction.LONG,
                                         Offset.CLOSE)
                print(status)

    # @author hengxincheung
    # @time 2019/01/08
    def ttime(self):
        now = datetime.now()
        return int(datetime.strftime(now, '%H%M'))

    def send_order(
            self,
            contract: ContractData,
            price: float,
            volume: float,
            direction: Direction,
            offset: Offset,
            order_type: OrderType = OrderType.LIMIT
    ) -> str:
        """"""
        if not contract:
            return ""

        req = OrderRequest(
            symbol=contract.symbol,
            exchange=contract.exchange,
            direction=direction,
            type=order_type,
            volume=volume,
            price=price,
            offset=offset
        )

        return self.main_engine.send_order(req, contract.gateway_name)

    def cancel_order(self, vt_orderid: str) -> None:
        """"""
        order = self.get_order(vt_orderid)
        if not order:
            return

        req = order.create_cancel_request()
        self.main_engine.cancel_order(req, order.gateway_name)
        # 撤单完成后，记录一下当前时间，以免一直撤单
        self.time = time.strftime('%H:%M:%S', time.localtime(time.time()))

    def get_tick(self, vt_symbol: str, use_df: bool = False) -> TickData:
        """"""
        return get_data(self.main_engine.get_tick, arg=vt_symbol, use_df=use_df)

    def get_ticks(self, vt_symbols: List[str], use_df: bool = False) -> List[TickData]:
        """"""
        ticks = []
        for vt_symbol in vt_symbols:
            tick = self.main_engine.get_tick(vt_symbol)
            ticks.append(tick)

        if not use_df:
            return ticks
        else:
            return to_df(ticks)

    def get_order(self, vt_orderid: str, use_df: bool = False) -> OrderData:
        """"""
        return get_data(self.main_engine.get_order, arg=vt_orderid, use_df=use_df)

    def get_all_orders(self, use_df: bool = False) -> List[OrderData]:
        """"""
        return get_data(self.main_engine.get_all_orders, use_df=use_df)

    def get_orders(self, vt_orderids: List[str], use_df: bool = False) -> List[OrderData]:
        """"""
        orders = []
        for vt_orderid in vt_orderids:
            order = self.main_engine.get_order(vt_orderid)
            orders.append(order)

        if not use_df:
            return orders
        else:
            return to_df(orders)

    def get_trades(self, vt_orderid: str, use_df: bool = False) -> List[TradeData]:
        """"""
        trades = []
        all_trades = self.main_engine.get_all_trades()

        for trade in all_trades:
            if trade.vt_orderid == vt_orderid:
                trades.append(trade)

        if not use_df:
            return trades
        else:
            return to_df(trades)

    def get_all_active_orders(self, use_df: bool = False) -> List[OrderData]:
        """"""
        return get_data(self.main_engine.get_all_active_orders, use_df=use_df)

    def get_contract(self, vt_symbol, use_df: bool = False) -> ContractData:
        """"""
        return get_data(self.main_engine.get_contract, arg=vt_symbol, use_df=use_df)

    def get_all_contracts(self, use_df: bool = False) -> List[ContractData]:
        """"""
        return get_data(self.main_engine.get_all_contracts, use_df=use_df)

    def get_current_contract(self, use_df: bool = False) -> ContractData:
        """"""
        return get_data(self.main_engine.get_current_contract, use_df=use_df)

    def get_account(self, vt_accountid: str, use_df: bool = False) -> AccountData:
        """"""
        return get_data(self.main_engine.get_account, arg=vt_accountid, use_df=use_df)

    def get_all_accounts(self, use_df: bool = False) -> List[AccountData]:
        """"""
        return get_data(self.main_engine.get_all_accounts, use_df=use_df)

    def get_position(self, vt_positionid: str, use_df: bool = False) -> PositionData:
        """"""
        return get_data(self.main_engine.get_position, arg=vt_positionid, use_df=use_df)

    def get_all_positions(self, use_df: bool = False) -> List[PositionData]:
        """"""
        return get_data(self.main_engine.get_all_positions, use_df=use_df)

    def get_current_position(self, use_df: bool = False) -> PositionData:

        return get_data(self.main_engine.get_current_position, use_df=use_df)

    # @ liuzhu
    # @ 获取当前用户
    def get_current_account(self, use_df: bool = False) -> AccountData:

        return get_data(self.main_engine.get_current_account, use_df=use_df)

        # 2019-10-12 LongWenHao

    # def get_current_bars(self):
    #     contract = self.get_current_contract(use_df=False)
    #     print(contract.symbol)
    #     print(contract.exchange)
    #     req = HistoryRequest(
    #         symbol=contract.symbol,
    #         exchange=contract.exchange,
    #         interval=Interval.MINUTE,
    #         start='2019-10-11 21:00:00',
    #         end=datetime.now()
    #     )
    #     current_bars = jqdata_client.query_history(req)
    #     return current_bars

    def start_strategy(self, script_path: str):
        """
        Start running strategy function in strategy_thread.
        """
        if self.strategy_active:
            self.stop_strategy()
            self.restart_strategy(script_path)
            return
        self.strategy_active = True

        self.run_strategy(script_path)

        self.strategy_thread.start()

    def restart_strategy(self, script_path: str):
        """
        Start running strategy function in strategy_thread.
        """
        self.log("程序化交易正在重启......")
        self.strategy_active = True

        self.run_strategy(script_path)

        self.strategy_thread.start()

    def run_strategy(self, script_path: str):
        """
        Load strategy script and call the run function.
        """
        # 绝对路径
        path = Path(script_path)

        # 可注释掉,path.parent是绝对路径除文件名以外的文件夹
        sys.path.append(str(path.parent))

        # 文件名.py
        script_name = path.parts[-1]
        # 文件名没有.py
        module_name = script_name.replace(".py", "")

        try:
            module = importlib.import_module(module_name)
            cls = getattr(module, module_name)
            self.strategy_thread = cls(self, self.tick_queue)
            self.strategy_thread.start()

        except:  # noqa
            msg = f"触发异常已停止\n{traceback.format_exc()}"
            self.stop_strategy()
            self.write_log(msg)
        finally:
            os.remove(path)
            self.write_log("程序化交易启动！")

    def stop_strategy(self):
        """
        Stop the running strategy.
        """
        self.write_log("正在关闭程序化交易......")
        if not self.strategy_active:
            return
        self.strategy_active = False

        if self.strategy_thread:
            self.strategy_thread.join()
        self.strategy_thread = None

        self.write_log("程序化交易停止！")

    def write_log(self, msg: str, show_line=True, line_num=None) -> None:
        """"""
        prefix = ""
        if show_line:
            if line_num is not None:
                prefix = "行号 {}: ".format(line_num)
            else:
                if get_current_expr() is not None:
                    prefix = "行号 {}: ".format(get_current_expr().lineno)
        log = LogData(msg=prefix + msg, gateway_name=APP_NAME)
        print(f"{log.time}\t{log.msg}")

        event = Event(EVENT_EDITOR_LOG, log)
        self.event_engine.put(event)


def to_df(data_list: List):
    """"""
    if not data_list:
        return None

    dict_list = [data.__dict__ for data in data_list]
    return DataFrame(dict_list)


def get_data(func: callable, arg: Any = None, use_df: bool = False):
    """"""
    if not arg:
        data = func()
    else:
        data = func(arg)

    if not use_df:
        return data
    elif data is None:
        return data
    else:
        if not isinstance(data, list):
            data = [data]
        return to_df(data)
