"""
"""

import logging
import smtplib
import os
import sys
from abc import ABC
from datetime import datetime
from email.message import EmailMessage
from queue import Empty, Queue
from threading import Thread
from typing import Any, Sequence, List, Type
from PyQt5.QtWidgets import QApplication
from vnpy.event import Event, EventEngine
from .app import BaseApp
from .event import (
    EVENT_TICK,
    EVENT_ORDER,
    EVENT_TRADE,
    EVENT_POSITION,
    EVENT_ACCOUNT,
    EVENT_CONTRACT,
    EVENT_CURRENT_CONTRACT,
    EVENT_CURRENT_SYMBOL,
    EVENT_CURRENT_TICK,
    EVENT_LOG,
    EVENT_CURRENT_POSITION,

)
from .gateway import BaseGateway
from .object import (
    AccountData,
    TickData,
    BarData,
    ContractData,
    CancelRequest,
    LogData,
    OrderRequest,
    SubscribeRequest,
    HistoryRequest,
    Interval,
    Exchange,
    PositionData
)
from .setting import SETTINGS
from .utility import get_folder_path, TRADER_DIR
from vnpy.trader.rqdata import rqdata_client
from .constant import Direction


class MainEngine:
    """
    Acts as the core of VN Trader.
    """

    def __init__(self, event_engine: EventEngine = None):
        """"""
        print("Init MainEngine")

        if event_engine:
            self.event_engine = event_engine
        else:
            self.event_engine = EventEngine()
        self.event_engine.start()

        self.gateways = {}
        self.engines = {}
        self.apps = {}
        self.exchanges = []
        self.current_bars = []

        self.contracts = None

        os.chdir(TRADER_DIR)  # Change working directory
        self.init_engines()  # Initialize function engines

    def add_engine(self, engine_class: Any):
        """
        Add function engine.
        """
        engine = engine_class(self, self.event_engine)
        self.engines[engine.engine_name] = engine
        return engine

    def add_gateway(self, gateway_class: Type[BaseGateway]):
        """
        Add gateway.
        """
        gateway = gateway_class(self.event_engine)
        self.gateways[gateway.gateway_name] = gateway

        # Add gateway supported exchanges into engine

        for exchange in gateway.exchanges:
            if exchange not in self.exchanges:
                self.exchanges.append(exchange)

        return gateway

    def add_app(self, app_class: Type[BaseApp]):
        """
        Add app.
        """
        app = app_class()
        self.apps[app.app_name] = app

        engine = self.add_engine(app.engine_class)
        return engine

    def init_engines(self):
        """
        Init all engines.
        """
        self.add_engine(LogEngine)
        self.add_engine(OmsEngine)
        self.add_engine(EmailEngine)

        # @Time    : 2019-09-25
        # @Author  : Wang Yongchang
        # 添加TickEngine专门处理Tick
        self.add_engine(TickEngine)

    def write_log(self, msg: str, source: str = ""):
        """
        Put log event with specific message.
        """
        log = LogData(msg=msg, gateway_name=source)
        event = Event(EVENT_LOG, log)
        self.event_engine.put(event)

    def get_gateway(self, gateway_name: str):
        """
        Return gateway object by name.
        """
        gateway = self.gateways.get(gateway_name, None)
        if not gateway:
            self.write_log(f"找不到底层接口：{gateway_name}")
        return gateway

    def get_engine(self, engine_name: str):
        """
        Return engine object by name.
        """
        engine = self.engines.get(engine_name, None)
        if not engine:
            self.write_log(f"找不到引擎：{engine_name}")
        return engine

    def get_default_setting(self, gateway_name: str):
        """
        Get default setting dict of a specific gateway.
        """
        gateway = self.get_gateway(gateway_name)
        if gateway:
            return gateway.get_default_setting()
        return None

    def get_all_gateway_names(self):
        """
        Get all names of gatewasy added in main engine.
        """
        return list(self.gateways.keys())

    def get_all_apps(self):
        """
        Get all app objects.
        """
        return list(self.apps.values())

    def get_all_exchanges(self):
        """
        Get all exchanges.
        """
        return self.exchanges

    def get_current_bars(self):

        return self.current_bars

    def connect(self, setting: dict, gateway_name: str):
        """
        Start connection of a specific gateway.
        """
        gateway = self.get_gateway(gateway_name)
        if gateway:
            gateway.connect(setting)
            # event = Event(EVENT_DEPOSIT, "cal")
            # self.event_engine.put(event)

    def subscribe(self, req: SubscribeRequest, gateway_name: str):
        """
        Subscribe tick data update of a specific gateway.
        """
        gateway = self.get_gateway(gateway_name)
        if gateway:
            gateway.subscribe(req)

    def send_order(self, req: OrderRequest, gateway_name: str):
        """
        Send new order request to a specific gateway.
        """
        gateway = self.get_gateway(gateway_name)
        if gateway:

            return gateway.send_order(req)
            # QApplication.processEvents()

        else:
            return ""

    def cancel_order(self, req: CancelRequest, gateway_name: str):
        """
        Send cancel order request to a specific gateway.
        """
        gateway = self.get_gateway(gateway_name)
        if gateway:
            gateway.cancel_order(req)
            # QApplication.processEvents()

    def send_orders(self, reqs: Sequence[OrderRequest], gateway_name: str):
        """
        """
        gateway = self.get_gateway(gateway_name)
        if gateway:
            return gateway.send_orders(reqs)
            # QApplication.processEvents()
        else:
            return ["" for req in reqs]

    def cancel_orders(self, reqs: Sequence[CancelRequest], gateway_name: str):
        """
        """
        gateway = self.get_gateway(gateway_name)
        if gateway:
            gateway.cancel_orders(reqs)
            # QApplication.processEvents()

    def query_history(self, req: HistoryRequest, gateway_name: str):
        """
        Send cancel order request to a specific gateway.
        """
        gateway = self.get_gateway(gateway_name)
        if gateway:
            return gateway.query_history(req)
        else:
            return None

    def close(self):
        """
        Make sure every gateway and app is closed properly before
        programme exit.
        """
        # Stop event engine first to prevent new timer event.
        self.event_engine.stop()

        for engine in self.engines.values():
            engine.close()

        for gateway in self.gateways.values():
            gateway.close()


class BaseEngine(ABC):
    """
    Abstract class for implementing an function engine.
    """

    def __init__(
            self,
            main_engine: MainEngine,
            event_engine: EventEngine,
            engine_name: str,
    ):
        """"""
        self.main_engine = main_engine
        self.event_engine = event_engine
        self.engine_name = engine_name

    def close(self):
        """"""
        pass


class LogEngine(BaseEngine):
    """
    Processes log event and output with logging module.
    """

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        """"""
        super(LogEngine, self).__init__(main_engine, event_engine, "log")

        if not SETTINGS["log.active"]:
            return

        self.level = SETTINGS["log.level"]

        self.logger = logging.getLogger("VN Trader")
        self.logger.setLevel(self.level)

        self.formatter = logging.Formatter(
            "%(asctime)s  %(levelname)s: %(message)s"
        )

        self.add_null_handler()

        if SETTINGS["log.console"]:
            self.add_console_handler()

        if SETTINGS["log.file"]:
            self.add_file_handler()

        self.register_event()

    def add_null_handler(self):
        """
        Add null handler for logger.
        """
        null_handler = logging.NullHandler()
        self.logger.addHandler(null_handler)

    def add_console_handler(self):
        """
        Add console output of log.
        """
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.level)
        console_handler.setFormatter(self.formatter)
        self.logger.addHandler(console_handler)

    def add_file_handler(self):
        """
        Add file output of log. 
        """
        today_date = datetime.now().strftime("%Y%m%d")
        filename = f"vt_{today_date}.log"
        log_path = get_folder_path("log")
        file_path = log_path.joinpath(filename)

        file_handler = logging.FileHandler(
            file_path, mode="a", encoding="utf8"
        )
        file_handler.setLevel(self.level)
        file_handler.setFormatter(self.formatter)
        self.logger.addHandler(file_handler)

    def register_event(self):
        """"""
        self.event_engine.register(EVENT_LOG, self.process_log_event)

    def process_log_event(self, event: Event):
        """
        Process log event.
        """
        log = event.data
        self.logger.log(log.level, log.msg)


class OmsEngine(BaseEngine):
    """
    Provides order management system function for VN Trader.
    """

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        """"""
        super(OmsEngine, self).__init__(main_engine, event_engine, "oms")

        print("Init OmsEngine")

        self.orders = {}
        self.trades = {}
        self.positions = {}
        self.accounts = {}
        self.contracts = {}

        # 2020-3-24 lwh
        self.long_positions = {}
        self.short_positions = {}

        self.main_engine.contracts = self.contracts

        self.current_account: AccountData = None
        self.current_contract: ContractData = None
        self.current_position: PositionData = None

        self.active_orders = {}
        self.add_function()
        self.register_event()

    def add_function(self):
        """Add query function to main engine."""

        self.main_engine.get_order = self.get_order
        self.main_engine.get_trade = self.get_trade
        self.main_engine.get_trades_by_symbol = self.get_trades_by_symbol
        self.main_engine.get_position = self.get_position
        self.main_engine.get_account = self.get_account
        # @Time    : 2019-09-19
        # @Author  : Wang Yongchang
        # 返回当前选取的合约
        self.main_engine.get_current_account = self.get_current_account
        self.main_engine.get_contract = self.get_contract
        self.main_engine.get_current_contract = self.get_current_contract
        self.main_engine.get_all_orders = self.get_all_orders
        self.main_engine.get_all_trades = self.get_all_trades
        self.main_engine.get_all_positions = self.get_all_positions
        self.main_engine.get_long_positions = self.get_long_positions
        self.main_engine.get_short_positions = self.get_short_positions
        # self.main_engine.get_all_positions = self.get_position_list
        self.main_engine.get_all_accounts = self.get_all_accounts
        self.main_engine.get_all_contracts = self.get_all_contracts
        self.main_engine.get_all_active_orders = self.get_all_active_orders
        self.main_engine.get_current_position = self.get_current_position

        # @author hengxincheung
        # @date 2020-05-15
        self.main_engine.get_long_position_by_symbol = self.get_long_position_by_symbol
        self.main_engine.get_short_position_by_symbol = self.get_short_position_by_symbol

    def register_event(self):
        """"""
        self.event_engine.register(EVENT_ORDER, self.process_order_event)
        self.event_engine.register(EVENT_TRADE, self.process_trade_event)
        self.event_engine.register(EVENT_POSITION, self.process_position_event)
        self.event_engine.register(EVENT_ACCOUNT, self.process_account_event)
        self.event_engine.register(EVENT_CONTRACT, self.process_contract_event)

        """
        #@ 添加实时持仓功能
        #@ liuzhu
        #@ 2019.10.15 
        """
        self.event_engine.register(EVENT_CURRENT_POSITION, self.process_current_position_event)

        # @Time    : 2019-09-19
        # @Author  : Wang Yongchang
        # 注册当前合约代码事件
        self.event_engine.register(EVENT_CURRENT_SYMBOL, self.process_current_symbol_event)

    def process_order_event(self, event: Event):
        """"""
        order = event.data
        self.orders[order.vt_orderid] = order

        # If order is active, then update data in dict.
        if order.is_active():
            self.active_orders[order.vt_orderid] = order
        # Otherwise, pop inactive order from in dict
        elif order.vt_orderid in self.active_orders:
            self.active_orders.pop(order.vt_orderid)

    def process_trade_event(self, event: Event):
        """"""
        trade = event.data
        self.trades[trade.vt_tradeid] = trade

    def process_position_event(self, event: Event):
        """"""
        position = event.data
        # print("position: ", position)
        self.positions[position.symbol] = position
        if position.direction == Direction.LONG:
            self.long_positions[position.symbol] = position
        elif position.direction == Direction.SHORT:
            self.short_positions[position.symbol] = position

    def process_account_event(self, event: Event):
        """"""
        account = event.data
        # @Time    : 2019-09-23
        # @Author  : Wang Yongchang
        # 处理当前账户事件
        self.current_account = account
        self.accounts[account.accountid] = account

    def process_contract_event(self, event: Event):
        """"""
        contract = event.data
        self.contracts[contract.symbol] = contract

    # @Time    : 2019-09-19
    # @Author  : Wang Yongchang
    # 注册处理当前合约事件

    def process_current_contract_event(self, event: Event):
        """"""
        contract = event.data
        self.current_contract = contract

    # @Time    : 2019-09-19
    # @Author  : Wang Yongchang
    # 注册处理当前合约代码事件

    def process_current_symbol_event(self, event: Event):
        """"""
        symbol = event.data.symbol
        self.current_contract = self.contracts.get(symbol, None)
        # self.current_position = self.positions.get(symbol, None)

    """
    @# 处理实时的持仓
    @# liuzhu
    @# 2019.10.15
    """

    def process_current_position_event(self, event: Event):
        position = event.data
        self.current_position = position

    def get_order(self, vt_orderid):
        """
        Get latest order data by vt_orderid.
        """
        return self.orders.get(vt_orderid, None)

    def get_trade(self, vt_tradeid):
        """
        Get trade data by vt_tradeid.
        """
        return self.trades.get(vt_tradeid, None)

    def get_trades_by_symbol(self, symbol):
        """
        Get trade data by vt_tradeid.
        """
        trade_list = [trade for trade in self.get_all_trades() if trade.symbol == symbol]

        return trade_list

    def get_position(self, symbol):
        """
        Get latest position data by symbol.
        """
        return self.positions.get(symbol, None)

    def get_account(self, accountid):
        """
        Get latest account data by accountid.
        """
        return self.accounts.get(accountid, None)

    # @Time    : 2019-09-23
    # @Author  : Wang Yongchang
    # 处理当前账户事件
    def get_current_account(self):
        """
        Get latest account data by accountid.
        """
        return self.current_account

    def get_contract(self, symbol):
        """
        Get contract data by symbol.
        """
        return self.contracts.get(symbol, None)

    # @Time    : 2019-09-19
    # @Author  : Wang Yongchang
    # 返回选取的当前合约
    def get_current_contract(self):
        """
        Get contract data by symbol.
        """
        return self.current_contract

    """
    @# 获取当前持仓
    @# liuzhu
    @# 2019.10.15
    """

    def get_current_position(self):

        """
        Get position data by symbol
        :return:
        """
        return self.current_position

    def get_all_orders(self):
        """
        Get all order data.
        """
        return list(self.orders.values())

    def get_all_trades(self):
        """
        Get all trade data.
        """
        return list(self.trades.values())

    def get_all_positions(self):
        """
        Get all position data.
        """
        return list(self.positions.values())

    # 2020-3-25 LWH
    def get_long_positions(self):
        """
            获取开多的持仓
        """
        return list(self.long_positions.values())

    def get_long_position_by_symbol(self, symbol):
        """根据合约号获取开多的持仓"""
        return self.long_positions.get(symbol, None)

    # 2020-3-25 LWH
    def get_short_positions(self):
        """
            获取开空的持仓
        """
        return list(self.short_positions.values())

    def get_short_position_by_symbol(self, symbol):
        """根据合约号获取开空的持仓"""
        return self.short_positions.get(symbol, None)

    def get_position_list(self):
        return self.position_list

    def get_all_accounts(self):
        """
        Get all account data.
        """
        return list(self.accounts.values())

    def get_all_contracts(self):
        """
        Get all contract data.
        """
        return list(self.contracts.values())

    def get_all_active_orders(self, vt_symbol: str = ""):
        """
        Get all active orders by vt_symbol.

        If vt_symbol is empty, return all active orders.
        """
        if not vt_symbol:
            return list(self.active_orders.values())
        else:
            active_orders = [
                order
                for order in self.active_orders.values()
                if order.vt_symbol == vt_symbol
            ]
            return active_orders


# @Time    : 2019-09-25
# @Author  : Wang Yongchang
# 添加TickEngine专门处理Tick

class TickEngine(BaseEngine):
    """
    Provides order management system function for VN Trader.
    """

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        """"""
        super(TickEngine, self).__init__(main_engine, event_engine, "tick")

        self.ticks = {}
        self.add_function()
        self.register_event()

    def add_function(self):
        """Add query function to main engine."""
        self.main_engine.get_tick = self.get_tick
        # @Time    : 2019-09-19
        # @Author  : Wang Yongchang
        # 返回当前tick
        self.main_engine.get_current_tick = self.get_current_tick
        # @Time    : 2019-09-19
        # @Author  : Wang Yongchang
        # 返回当前tick列表
        # self.main_engine.get_ticks_in_span = self.get_ticks_in_span

        self.main_engine.get_all_ticks = self.get_all_ticks

    def register_event(self):
        """"""
        self.event_engine.register(EVENT_TICK, self.process_tick_event)

    def process_tick_event(self, event: Event):
        """"""
        tick = event.data
        self.ticks[tick.symbol] = tick

        # print(tick)
        # @Time    : 2019-09-19
        # @Author  : Wang Yongchang
        # 根据当前合约设置当前tick列表
        current_contract = self.main_engine.get_current_contract()
        if current_contract:
            if tick.symbol == current_contract.symbol:
                # print(tick.symbol)
                # @Time    : 2019-09-20
                # @Author  : Wang Yongchang
                # 当前有新的tick，发送到事件引擎，经ScriptEngine传给脚本使用
                event = Event(EVENT_CURRENT_TICK, tick)
                self.event_engine.put(event)

    def process_order_event(self, event: Event):
        """"""
        order = event.data
        self.orders[order.vt_orderid] = order

        # If order is active, then update data in dict.
        if order.is_active():
            self.active_orders[order.vt_orderid] = order
        # Otherwise, pop inactive order from in dict
        elif order.vt_orderid in self.active_orders:
            self.active_orders.pop(order.vt_orderid)

    def set_ticks(self, event: Event):
        """
        Get all tick data.
        """
        trade = event.data
        self.trades[trade.vt_tradeid] = trade

    def get_tick(self, symbol):
        """
        Get latest market tick data by symbol.
        """
        return self.ticks.get(symbol, None)

    def get_ticks_in_span(self) -> List[TickData]:

        return self.ticks_in_span

    def get_all_ticks(self):
        """
        Get all tick data.
        """
        return list(self.ticks.values())

    # @Time    : 2019-09-19
    # @Author  : Wang Yongchang
    # 设置获取所选合约的当前tick
    def get_current_tick(self, contract: ContractData):
        """
        Get all tick data.
        """
        self.main_engine.current_contract = contract
        return self.ticks.get(contract.symbol, None)


class EmailEngine(BaseEngine):
    """
    Provides email sending function for VN Trader.
    """

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        """"""
        super(EmailEngine, self).__init__(main_engine, event_engine, "email")

        self.thread = Thread(target=self.run)
        self.queue = Queue()
        self.active = False

        self.main_engine.send_email = self.send_email

    def send_email(self, subject: str, content: str, receiver: str = ""):
        """"""
        # Start email engine when sending first email.
        if not self.active:
            self.start()

        # Use default receiver if not specified.
        if not receiver:
            receiver = SETTINGS["email.receiver"]

        msg = EmailMessage()
        msg["From"] = SETTINGS["email.sender"]
        msg["To"] = SETTINGS["email.receiver"]
        msg["Subject"] = subject
        msg.set_content(content)

        self.queue.put(msg)

    def run(self):
        """"""
        while self.active:
            try:
                msg = self.queue.get(block=True, timeout=1)

                with smtplib.SMTP_SSL(
                        SETTINGS["email.server"], SETTINGS["email.port"]
                ) as smtp:
                    smtp.login(
                        SETTINGS["email.username"], SETTINGS["email.password"]
                    )
                    smtp.send_message(msg)
            except Empty:
                pass

    def start(self):
        """"""
        self.active = True
        self.thread.start()

    def close(self):
        """"""
        if not self.active:
            return

        self.active = False
        self.thread.join()
