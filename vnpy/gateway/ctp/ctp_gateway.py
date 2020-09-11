"""
"""
import time
from datetime import datetime
from vnpy.trader.utility import round_up

from vnpy.api.ctp import (
    MdApi,
    TdApi,
    THOST_FTDC_OAS_Submitted,
    THOST_FTDC_OAS_Accepted,
    THOST_FTDC_OAS_Rejected,
    THOST_FTDC_OST_NoTradeQueueing,
    THOST_FTDC_OST_PartTradedQueueing,
    THOST_FTDC_OST_AllTraded,
    THOST_FTDC_OST_Canceled,
    THOST_FTDC_D_Buy,
    THOST_FTDC_D_Sell,
    THOST_FTDC_PD_Long,
    THOST_FTDC_PD_Short,
    THOST_FTDC_OPT_LimitPrice,
    THOST_FTDC_OPT_AnyPrice,
    THOST_FTDC_OF_Open,
    THOST_FTDC_OFEN_Close,
    THOST_FTDC_OFEN_CloseYesterday,
    THOST_FTDC_OFEN_CloseToday,
    THOST_FTDC_PC_Futures,
    THOST_FTDC_PC_Options,
    THOST_FTDC_PC_Combination,
    THOST_FTDC_CP_CallOptions,
    THOST_FTDC_CP_PutOptions,
    THOST_FTDC_HF_Speculation,
    THOST_FTDC_CC_Immediately,
    THOST_FTDC_FCC_NotForceClose,
    THOST_FTDC_TC_GFD,
    THOST_FTDC_VC_AV,
    THOST_FTDC_TC_IOC,
    THOST_FTDC_VC_CV,
    THOST_FTDC_AF_Delete
)
from vnpy.trader.constant import (
    Direction,
    Offset,
    Exchange,
    OrderType,
    Product,
    Status,
    OptionType
)
from vnpy.trader.gateway import BaseGateway
from vnpy.trader.object import (
    TickData,
    OrderData,
    TradeData,
    PositionData,
    AccountData,
    ContractData,
    OrderRequest,
    CancelRequest,
    SubscribeRequest,
)
from vnpy.trader.utility import get_folder_path
from vnpy.event import Event
from vnpy.trader.event import EVENT_TIMER, EVENT_CONTRACT, EVENT_CURRENT_ACCOUNT
from vnpy.trader.database import database_manager

# 2020-2-6 LWH 算持仓保证金
from vnpy.trader.engine import BaseEngine, MainEngine
from vnpy.event import Event, EventEngine
from vnpy.app.editor_manager.ui.editor_box import EditorBox
from vnpy.app.editor_manager.ui.widget import EditorManager
from vnpy.trader.object import PositionData

STATUS_CTP2VT = {
    THOST_FTDC_OAS_Submitted: Status.SUBMITTING,
    THOST_FTDC_OAS_Accepted: Status.SUBMITTING,
    THOST_FTDC_OAS_Rejected: Status.REJECTED,
    THOST_FTDC_OST_NoTradeQueueing: Status.NOTTRADED,
    THOST_FTDC_OST_PartTradedQueueing: Status.PARTTRADED,
    THOST_FTDC_OST_AllTraded: Status.ALLTRADED,
    THOST_FTDC_OST_Canceled: Status.CANCELLED
}

DIRECTION_VT2CTP = {
    Direction.LONG: THOST_FTDC_D_Buy,
    Direction.SHORT: THOST_FTDC_D_Sell
}
DIRECTION_CTP2VT = {v: k for k, v in DIRECTION_VT2CTP.items()}
DIRECTION_CTP2VT[THOST_FTDC_PD_Long] = Direction.LONG
DIRECTION_CTP2VT[THOST_FTDC_PD_Short] = Direction.SHORT

ORDERTYPE_VT2CTP = {
    OrderType.LIMIT: THOST_FTDC_OPT_LimitPrice,
    OrderType.MARKET: THOST_FTDC_OPT_AnyPrice
}
ORDERTYPE_CTP2VT = {v: k for k, v in ORDERTYPE_VT2CTP.items()}

OFFSET_VT2CTP = {
    Offset.OPEN: THOST_FTDC_OF_Open,
    Offset.CLOSE: THOST_FTDC_OFEN_Close,
    Offset.CLOSETODAY: THOST_FTDC_OFEN_CloseToday,
    Offset.CLOSEYESTERDAY: THOST_FTDC_OFEN_CloseYesterday,
}
OFFSET_CTP2VT = {v: k for k, v in OFFSET_VT2CTP.items()}

EXCHANGE_CTP2VT = {
    "CFFEX": Exchange.CFFEX,
    "SHFE": Exchange.SHFE,
    "CZCE": Exchange.CZCE,
    "DCE": Exchange.DCE,
    "INE": Exchange.INE
}

PRODUCT_CTP2VT = {
    THOST_FTDC_PC_Futures: Product.FUTURES,
    THOST_FTDC_PC_Options: Product.OPTION,
    THOST_FTDC_PC_Combination: Product.SPREAD
}

OPTIONTYPE_CTP2VT = {
    THOST_FTDC_CP_CallOptions: OptionType.CALL,
    THOST_FTDC_CP_PutOptions: OptionType.PUT
}

symbol_exchange_map = {}
symbol_name_map = {}
symbol_size_map = {}

subscribed_contract = set()


class CtpGateway(BaseGateway):
    """
    VN Trader Gateway for CTP .
    """

    default_setting = {
        "用户名": "",
        "密码": "",
        "经纪商代码": "",
        "交易服务器": [],
        "行情服务器": [],
        "产品名称": "",
        "授权编码": "",
        "合约代码": "",
    }

    exchanges = list(EXCHANGE_CTP2VT.values())

    def __init__(self, event_engine):
        """Constructor"""
        super().__init__(event_engine, "CTP")

        self.td_api = CtpTdApi(self)
        self.md_api = CtpMdApi(self)




    def connect(self, setting: dict):

        """"""
        userid = setting["用户名"].replace(" ", "")
        password = setting["密码"].replace(" ", "")
        brokerid = setting["经纪商代码"].replace(" ", "")
        td_address = setting["交易服务器"].replace(" ", "").replace("：", ":")
        md_address = setting["行情服务器"].replace(" ", "").replace("：", ":")
        appid = setting["产品名称"].replace(" ", "")
        auth_code = setting["授权编码"].replace(" ", "")
        instrument_ids = setting["合约代码"].replace(" ", "")

        subscribed_contract.clear()
        for ids in instrument_ids.split(","):
            subscribed_contract.add(ids)

        if not td_address.startswith("tcp://"):
            td_address = "tcp://" + td_address
        if not md_address.startswith("tcp://"):
            md_address = "tcp://" + md_address

        self.td_api.connect(td_address, userid, password, brokerid, auth_code, appid, instrument_ids)
        time.sleep(1)
        self.md_api.connect(md_address, userid, password, brokerid)

        self.init_query()
        # @Time    : 2019-09-16
        # @Author  : Wang Yongchang
        self.register_contract()

        # 订阅合约
        self.md_api.subscribed.clear()
        instrument_ids_list = instrument_ids.split(",")
        for ids in instrument_ids_list:
            self.md_api.subscribed.add(ids.encode("utf-8"))
            # self.md_api.subscribeMarketData(ids.encode("utf-8"))


    def subscribe(self, req: SubscribeRequest):
        """"""
        self.md_api.subscribe(req)

    def send_order(self, req: OrderRequest):
        """"""
        return self.td_api.send_order(req)

    def cancel_order(self, req: CancelRequest):
        """"""
        self.td_api.cancel_order(req)

    def query_account(self):
        """"""
        self.td_api.query_account()

    def query_position(self):
        """"""
        self.td_api.query_position()

    def query_order(self):
        """"""
        self.td_api.query_order()

    def close(self):
        """"""
        self.td_api.close()
        self.md_api.close()

    def write_error(self, msg: str, error: dict):
        """"""
        error_id = error["ErrorID"]
        error_msg = error["ErrorMsg"]
        msg = f"{msg}，代码：{error_id}，信息：{error_msg}"
        self.write_log(msg)

    def process_timer_event(self, event):

        """"""
        self.count += 1
        if self.count % 2 == 0:
            self.count = 1
            func = self.query_functions.pop(0)
            func()
            self.query_functions.append(func)
        else:
            return

    def init_query(self):

        """"""
        self.count = 1
        self.query_functions = [self.query_account, self.query_position, self.query_order]
        self.event_engine.register(EVENT_TIMER, self.process_timer_event)

    # @Time    : 2019-09-16
    # @Author  : Wang Yongchang
    # 注册EVENT_CONTRACT事件，获取所有合约信息
    def register_contract(self):
        self.event_engine.register(EVENT_CONTRACT, self.subscribe_tick)

    # @Time    : 2020-02-10
    # @Author  : LongWenHao
    # def process_current_contract_event(self, event) -> None:
    #     self.current_contract = event.data
    #     print(self.current_contract)





    # @Time    : 2019-09-16
    # @Author  : Wang Yongchang
    # 订阅Tick数据
    def subscribe_tick(self, event: Event):

        req = SubscribeRequest(
            symbol=event.data.symbol,
            exchange=event.data.exchange,
        )
        self.subscribe(req)


class CtpMdApi(MdApi):
    """"""

    def __init__(self, gateway):
        """Constructor"""
        super(CtpMdApi, self).__init__()

        self.gateway = gateway
        self.gateway_name = gateway.gateway_name

        self.reqid = 0

        self.connect_status = False
        self.login_status = False
        self.subscribed = set()

        self.userid = ""
        self.password = ""
        self.brokerid = ""

    def onFrontConnected(self):
        """
        Callback when front server is connected.
        """
        self.gateway.write_log("行情服务器连接成功")
        self.login()
        print("行情服务器连接成功")

    def onFrontDisconnected(self, reason: int):
        """
        Callback when front server is disconnected.
        """
        self.login_status = False
        self.gateway.write_log(f"行情服务器连接断开，原因{reason}")

    def onRspUserLogin(self, data: dict, error: dict, reqid: int, last: bool):
        """
        Callback when user is logged in.
        """
        print("登录成功: ", data)
        if not error["ErrorID"]:
            self.login_status = True
            self.gateway.write_log("行情服务器登录成功")

            for symbol in self.subscribed:
                print("正在订阅: {}".format(symbol))
                self.subscribeMarketData(symbol)
        else:
            self.gateway.write_error("行情服务器登录失败", error)

    def onRspError(self, error: dict, reqid: int, last: bool):
        """
        Callback when error occured.
        """
        self.gateway.write_error("行情接口报错", error)

    def onRspSubMarketData(self, data: dict, error: dict, reqid: int, last: bool):
        """"""
        if not error or not error["ErrorID"]:
            print("行情订阅成功:", data)
            return
        self.gateway.write_error("行情订阅失败", error)

    def onRtnDepthMarketData(self, data: dict):
        """
        Callback of tick data update.
        """
        symbol = data["InstrumentID"]
        exchange = symbol_exchange_map.get(symbol, Exchange.UNK)
        # print(exchange)
        # @Time    : 2019-09-20
        # @Author  : Wang Yongchang
        # 过滤ActionDay为空的合约，导致datetime=datetime.strptime(timestamp, "%Y%m%d %H:%M:%S.%f"),报错

        if data['ActionDay']:
            timestamp = f"{data['ActionDay']} {data['UpdateTime']}.{int(data['UpdateMillisec'] / 100)}"
        else:
            timestamp = f"{datetime.now().strftime('%Y%m%d')} {data['UpdateTime']}.{int(data['UpdateMillisec'] / 100)}"

        # print(timestamp)

        # @Time    : 2019-09-20
        # @Author  : Wang Yongchang
        # 过滤不活跃的合约，价格越界的数据

        open_price = data["OpenPrice"]
        # if open_price == 1.7976931348623157e+308:
        #     open_price = 0

        high_price = data["HighestPrice"]
        # if high_price == 1.7976931348623157e+308:
        #     high_price = 0

        low_price = data["LowestPrice"]
        # if low_price == 1.7976931348623157e+308:
        #     low_price = 0

        bid_price_1 = data["BidPrice1"]
        # if bid_price_1 == 1.7976931348623157e+308:
        #     bid_price_1 = 0

        ask_price_1 = data["AskPrice1"]
        # if ask_price_1 == 1.7976931348623157e+308:
        #     ask_price_1 = 0

        tick = TickData(
            symbol=symbol,
            exchange=exchange,
            datetime=datetime.strptime(timestamp, "%Y%m%d %H:%M:%S.%f"),
            name=symbol_name_map.get(symbol, "未知"),
            volume=data["Volume"],
            open_interest=round_up(data["OpenInterest"]),
            last_price=round_up(data["LastPrice"]),
            limit_up=round_up(data["UpperLimitPrice"]),
            limit_down=round_up(data["LowerLimitPrice"]),
            open_price=round_up(open_price),
            high_price=round_up(high_price),
            low_price=round_up(low_price),
            pre_close=round_up(data["PreClosePrice"]),
            bid_price_1=round_up(bid_price_1),
            ask_price_1=round_up(ask_price_1),
            bid_volume_1=data["BidVolume1"],
            ask_volume_1=data["AskVolume1"],
            gateway_name=self.gateway_name
        )
        #print("{}, {}".format(tick.symbol, tick.datetime))
        if not tick:
            print("tick为空")

        self.gateway.on_tick(tick)

    def connect(self, address: str, userid: str, password: str, brokerid: int):
        """
        Start connection to server.
        """
        self.userid = userid
        self.password = password
        self.brokerid = brokerid

        # If not connected, then start connection first.
        if not self.connect_status:
            path = get_folder_path(self.gateway_name.lower())
            self.createFtdcMdApi(str(path) + "\\Md")

            self.registerFront(address)
            self.init()

            self.connect_status = True
        # If already connected, then login immediately.
        elif not self.login_status:
            self.login()

    def login(self):
        """
        Login onto server.
        """
        req = {
            "UserID": self.userid,
            "Password": self.password,
            "BrokerID": self.brokerid
        }

        self.reqid += 1
        self.reqUserLogin(req, self.reqid)

    def subscribe(self, req: SubscribeRequest):
        """
        Subscribe to tick data update.
        """
        if self.login_status:
            self.subscribeMarketData(req.symbol)
        self.subscribed.add(req.symbol)

    def close(self):
        """
        Close the connection.
        """
        if self.connect_status:
            self.exit()


class CtpTdApi(TdApi):
    """"""

    def __init__(self, gateway):
        """Constructor"""
        super(CtpTdApi, self).__init__()

        self.gateway = gateway
        self.gateway_name = gateway.gateway_name

        self.reqid = 0
        self.order_ref = 0

        self.connect_status = False
        self.login_status = False
        self.auth_staus = False
        self.login_failed = False

        self.userid = ""
        self.password = ""
        self.brokerid = ""
        self.auth_code = ""
        self.appid = ""
        self.instrument_ids = ""

        self.frontid = 0
        self.sessionid = 0

        self.order_data = []
        self.trade_data = []
        self.positions = {}
        self.sysid_orderid_map = {}



    def onFrontConnected(self):
        """"""
        self.gateway.write_log("交易服务器连接成功")

        if self.auth_code:
            self.authenticate()
        else:
            self.login()

    def onFrontDisconnected(self, reason: int):
        """"""
        self.login_status = False
        self.gateway.write_log(f"交易服务器连接断开，原因{reason}")

    def onRspAuthenticate(self, data: dict, error: dict, reqid: int, last: bool):
        """"""
        if not error['ErrorID']:
            self.auth_staus = True
            self.gateway.write_log("交易服务器授权验证成功")
            self.login()
        else:
            self.gateway.write_error("交易服务器授权验证失败", error)

    def onRspUserLogin(self, data: dict, error: dict, reqid: int, last: bool):
        """"""
        if not error["ErrorID"]:
            self.frontid = data["FrontID"]
            self.sessionid = data["SessionID"]
            self.login_status = True
            self.gateway.write_log("交易服务器登录成功")

            # Confirm settlement
            req = {
                "BrokerID": self.brokerid,
                "InvestorID": self.userid
            }
            self.reqid += 1
            self.reqSettlementInfoConfirm(req, self.reqid)

            self.reqid += 1
            self.reqQryInstrument({}, self.reqid)
        else:
            self.login_failed = True

            self.gateway.write_error("交易服务器登录失败", error)

    def onRspOrderInsert(self, data: dict, error: dict, reqid: int, last: bool):
        """"""
        order_ref = data["OrderRef"]
        orderid = f"{self.frontid}_{self.sessionid}_{order_ref}"

        symbol = data["InstrumentID"]
        exchange = symbol_exchange_map[symbol]

        order = OrderData(
            accountid="",
            symbol=symbol,
            exchange=exchange,
            orderid=orderid,
            direction=DIRECTION_CTP2VT[data["Direction"]],
            offset=OFFSET_CTP2VT.get(data["CombOffsetFlag"], Offset.NONE),
            price=round_up(data["LimitPrice"]),
            volume=data["VolumeTotalOriginal"],
            status=Status.REJECTED,
            gateway_name=self.gateway_name
        )
        self.gateway.on_order(order)

        self.gateway.write_error("交易委托失败", error)

    def onRspOrderAction(self, data: dict, error: dict, reqid: int, last: bool):
        """"""
        self.gateway.write_error("交易撤单失败", error)

    def onRspQueryMaxOrderVolume(self, data: dict, error: dict, reqid: int, last: bool):
        """"""
        pass

    def onRspSettlementInfoConfirm(self, data: dict, error: dict, reqid: int, last: bool):
        """
        Callback of settlment info confimation.
        """
        self.gateway.write_log("结算信息确认成功")

        self.reqid += 1
        self.reqQryInstrument({}, self.reqid)

    def onRspQryInvestorPosition(self, data: dict, error: dict, reqid: int, last: bool):
        """"""
        if not data:
            return

        # position = self.positions.get(key, None)
        # if not position:
        # @Time    : 2020-01-17
        # @Author  : hengxinchueng
        # 修改持仓数据不同步问题
        position = PositionData(
            accountid=data["InvestorID"],
            symbol=data["InstrumentID"],
            exchange=symbol_exchange_map[data["InstrumentID"]],
            direction=DIRECTION_CTP2VT[data["PosiDirection"]],
            gateway_name=self.gateway_name
        )
        # Get buffered position object
        key = f"{position.symbol, position.direction.value}"

        # For SHFE position data update
        if position.exchange == Exchange.SHFE:
            if data["YdPosition"] and not data["TodayPosition"]:
                position.yd_volume = data["Position"]
        # For other exchange position data update
        else:
            position.yd_volume = data["Position"] - data["TodayPosition"]

        # Get contract size (spread contract has no size value)
        size = symbol_size_map.get(position.symbol, 0)

        # Calculate previous position cost
        # cost = position.price * position.volume * size
        # cost = data["PositionCost"]

        # Update new position volume
        position.volume = data["Position"]
        position.pnl = data["PositionProfit"]

        # Calculate average position price
        if position.volume and size:
            cost = data["PositionCost"]
            position.price = round_up(cost / (position.volume * size))

        # Get frozen volume
        if position.direction == Direction.LONG:
            position.frozen = data["ShortFrozen"]
        else:
            position.frozen = data["LongFrozen"]
        # print(position)
        self.positions[key] = position
        # print(position)
        # print(last)
        # if last:
        #     for position in self.positions.values():
        #         # @Time    : 2020-01-17
        #         # @Author  : hengxincheung
        #         # 解决清仓界面不同步的问题
        #         if position.volume >= 0:
        #             self.gateway.on_position(position)
        #
        #     self.positions.clear()
        self.gateway.on_position(position)

    def onRspQryTradingAccount(self, data: dict, error: dict, reqid: int, last: bool):
        """"""
        if "AccountID" not in data:
            return

        account = AccountData(
            accountid=data["AccountID"],
            balance=round_up(data["Balance"]),
            frozen=round_up(round_up(data["FrozenMargin"] + round_up(data["FrozenCash"]) + round_up(data["FrozenCommission"]))),
            deposit=round_up(data["ExchangeMargin"]),
            commission=round_up(data["Commission"]),
            floatPnl=round_up(data["PositionProfit"]),
            closePnl=round_up(data["CloseProfit"]),
            gateway_name=self.gateway_name
        )
        account.available = round_up(data["Available"])

        self.gateway.on_account(account)

    # 2020-2-6 lwh
    # def onDeposit(self,symbol,size,price,deposit,all_orders,all_positions,fee,offsetprofit):
    # current_position = PositionData
    # 2020-2-6 LWH 算持仓保证金
    # for position in all_positions:
    #     if position.symbol == symbol:
    #         current_position = position
    #         self.pnl = position.pnl
    # untraded_num = 0
    # traded_num = 0
    # print(all_orders)
    # for order in all_orders:
    #     if order.symbol == symbol and order.status == Status.NOTTRADED:
    #         untraded_num += order.volume
    #     elif order.symbol == symbol and order.status == Status.ALLTRADED:
    #         traded_num += order.volume
    # self.deposit = (current_position.volume + untraded_num) * 0.1 * price * size
    # print(deposit)
    # if deposit != None:
    #     self.deposit = (current_position.volume + untraded_num) * deposit * price * size
    #     print(self.deposit)
    # else:
    #     self.deposit = (current_position.volume + untraded_num) * 0.1 * price * size

    # print(self.deposit)
    # self.offsetprofit = offsetprofit
    # self.commission = fee

    def onRspQryInstrument(self, data: dict, error: dict, reqid: int, last: bool):
        """
        Callback of instrument query.
        """
        if data["InstrumentID"] in subscribed_contract:
            print(data)

        product = PRODUCT_CTP2VT.get(data["ProductClass"], None)
        if product:
            contract = ContractData(
                symbol=data["InstrumentID"],
                exchange=EXCHANGE_CTP2VT[data["ExchangeID"]],
                name=data["InstrumentName"],
                product=product,
                size=data["VolumeMultiple"],
                pricetick=data["PriceTick"],
                gateway_name=self.gateway_name
            )
            database_manager.save_contract_data([contract])

            # For option only
            if contract.product == Product.OPTION:
                contract.option_underlying = data["UnderlyingInstrID"],
                contract.option_type = OPTIONTYPE_CTP2VT.get(data["OptionsType"], None),
                contract.option_strike = data["StrikePrice"],
                contract.option_expiry = datetime.strptime(data["ExpireDate"], "%Y%m%d"),

            # @Time    : 2019-10-09
            # @Author  : Wang Yongchang
            # 倍特真实交易服务器合约太多导致卡顿
            # 通过输入合约代码订阅所需合约，不再显示所有合约

            self.instrument_ids = self.instrument_ids.replace("，", ",")
            instrument_ids_list = self.instrument_ids.split(",")

            if contract.symbol in instrument_ids_list:
                self.gateway.on_contract(contract)

            symbol_exchange_map[contract.symbol] = contract.exchange
            symbol_name_map[contract.symbol] = contract.name
            symbol_size_map[contract.symbol] = contract.size

        if last:
            self.gateway.write_log("合约信息查询成功")

            for data in self.order_data:
                self.onRtnOrder(data)
            self.order_data.clear()

            for data in self.trade_data:
                self.onRtnTrade(data)
            self.trade_data.clear()

    def onRtnOrder(self, data: dict):
        """
        Callback of order status update.
        """
        # print(data)
        if not data:
            return
        symbol = data["InstrumentID"]
        exchange = symbol_exchange_map.get(symbol, "")
        if not exchange:
            self.order_data.append(data)
            return

        accountid = data["InvestorID"]
        frontid = data["FrontID"]
        sessionid = data["SessionID"]
        order_ref = data["OrderRef"]
        orderid = f"{frontid}_{sessionid}_{order_ref}"
        order = OrderData(
            accountid=accountid,
            symbol=symbol,
            exchange=exchange,
            orderid=orderid,
            type=ORDERTYPE_CTP2VT.get(data["OrderPriceType"], OrderType.UNK),
            direction=DIRECTION_CTP2VT[data["Direction"]],
            offset=OFFSET_CTP2VT[data["CombOffsetFlag"]],
            price=round_up(data["LimitPrice"]),
            volume=data["VolumeTotalOriginal"],
            traded=data["VolumeTraded"],
            status=STATUS_CTP2VT[data["OrderStatus"]],
            time=data["InsertTime"],
            gateway_name=self.gateway_name
        )
        # @Author : LongWenHao
        # @Time : 2020.3.8
        # @Dec : 保存orderdata
        database_manager.save_order_data([order])
        self.gateway.on_order(order)

        self.sysid_orderid_map[data["OrderSysID"]] = orderid

    def onRspQryOrder(self, data, *args):
        """查询当日委托的回调函数"""
        if not data:
            return
        symbol = data["InstrumentID"]
        exchange = symbol_exchange_map.get(symbol, "")
        if not exchange:
            self.order_data.append(data)
            return
        accountid = data["InvestorID"]
        frontid = data["FrontID"]
        sessionid = data["SessionID"]
        order_ref = data["OrderRef"]
        orderid = f"{frontid}_{sessionid}_{order_ref}"
        order = OrderData(
            accountid=accountid,
            symbol=symbol,
            exchange=exchange,
            orderid=orderid,
            type=ORDERTYPE_CTP2VT.get(data["OrderPriceType"], OrderType.UNK),
            direction=DIRECTION_CTP2VT[data["Direction"]],
            offset=OFFSET_CTP2VT[data["CombOffsetFlag"]],
            price=round_up(data["LimitPrice"]),
            volume=data["VolumeTotalOriginal"],
            traded=data["VolumeTraded"],
            status=STATUS_CTP2VT[data["OrderStatus"]],
            time=data["InsertTime"],
            gateway_name=self.gateway_name
        )

        database_manager.save_order_data([order])
        self.gateway.on_order(order)

        self.sysid_orderid_map[data["OrderSysID"]] = orderid

    def onRtnTrade(self, data: dict):
        """
        Callback of trade status update.
        """
        accountid = data["InvestorID"]
        symbol = data["InstrumentID"]
        exchange = symbol_exchange_map.get(symbol, "")
        if not exchange:
            self.trade_data.append(data)
            return

        orderid = self.sysid_orderid_map[data["OrderSysID"]]

        trade_date = data["TradeDate"][0:4] + "-" + data["TradeDate"][4:6] + "-" + data["TradeDate"][6:8]

        # @Time    : 2019-09-19
        # @Author  : Wang Yongchang
        # 增加账号accountid，区分多账号

        trade = TradeData(
            accountid=accountid,
            symbol=symbol,
            exchange=exchange,
            orderid=orderid,
            tradeid=data["TradeID"],
            direction=DIRECTION_CTP2VT[data["Direction"]],
            offset=OFFSET_CTP2VT[data["OffsetFlag"]],
            price=round_up(data["Price"]),
            volume=data["Volume"],
            datetime=trade_date + " " + data["TradeTime"],
            gateway_name=self.gateway_name
        )
        database_manager.save_trade_data([trade])
        self.gateway.on_trade(trade)

    def connect(
            self,
            address: str,
            userid: str,
            password: str,
            brokerid: int,
            auth_code: str,
            appid: str,
            instrument_ids: str,
    ):
        """
        Start connection to server.
        """
        self.userid = userid
        self.password = password
        self.brokerid = brokerid
        self.auth_code = auth_code
        self.appid = appid
        self.instrument_ids = instrument_ids

        if not self.connect_status:
            path = get_folder_path(self.gateway_name.lower())
            self.createFtdcTraderApi(str(path) + "\\Td")

            self.subscribePrivateTopic(0)
            self.subscribePublicTopic(0)

            self.registerFront(address)
            self.init()

            self.connect_status = True
        else:
            self.authenticate()

    def authenticate(self):
        """
        Authenticate with auth_code and appid.
        """
        req = {
            "UserID": self.userid,
            "BrokerID": self.brokerid,
            "AuthCode": self.auth_code,
            "AppID": self.appid
        }

        self.reqid += 1
        self.reqAuthenticate(req, self.reqid)

    def login(self):
        """
        Login onto server.
        """
        if self.login_failed:
            return

        req = {
            "UserID": self.userid,
            "Password": self.password,
            "BrokerID": self.brokerid,
            "AppID": self.appid
        }

        self.reqid += 1
        self.reqUserLogin(req, self.reqid)

    def send_order(self, req: OrderRequest):
        """
        Send new order.
        """
        self.order_ref += 1

        # @author: hengxincheung
        # @time: 2020-05-22
        # 加入平仓时的处理

        # 如果是平仓操作
        if req.offset == Offset.CLOSE:
            if req.direction == Direction.LONG:
                key = f"{req.symbol, Direction.SHORT.value}"
            else:
                key = f"{req.symbol, Direction.LONG.value}"
            position = self.positions.get(key, None)
            # 如果没有持仓数据，返回
            if not position:
                return "无持仓数据"
            # 获得允许委托的持仓量：总持仓量 - 冻结数
            allowed_volumn = position.volume - position.frozen
            # 如果委托数量大于允许委托的持仓量，返回
            if req.volume > allowed_volumn:
                return "请求平仓数量大于允许平仓数量"
            # 获取昨仓数量
            yd_volumn = position.yd_volume
            # 如果昨仓数量大于0
            if yd_volumn > 0:
                # 如果委托数量小于等于昨仓数量
                if req.volume <= yd_volumn:
                    # 修改委托的方式
                    req.offset = Offset.CLOSEYESTERDAY
                    return [self.__send_order(req)]
                # 如果委托数量大于昨仓数量拆分成两个委托
                else:
                    order_id_list = []
                    # 需要平掉的今仓数量
                    td_volumn = req.volume - yd_volumn
                    # 委托1，平掉昨仓
                    req.volume = yd_volumn
                    req.offset = Offset.CLOSEYESTERDAY
                    order_id_list.append(self.__send_order(req))
                    # 委托2，平掉今仓
                    req.volume = td_volumn
                    req.offset = Offset.CLOSETODAY
                    order_id_list.append(self.__send_order(req))
                    return order_id_list
            # 没有昨仓
            else:
                req.offset = Offset.CLOSETODAY
                return [self.__send_order(req)]
        # 如果是开仓操作
        else:
            return self.__send_order(req)

    def __send_order(self, req):
        ctp_req = {
            "InstrumentID": req.symbol,
            "ExchangeID": req.exchange.value,
            "LimitPrice": req.price,
            "VolumeTotalOriginal": int(req.volume),
            "OrderPriceType": ORDERTYPE_VT2CTP.get(req.type, ""),
            "Direction": DIRECTION_VT2CTP.get(req.direction, ""),
            "CombOffsetFlag": OFFSET_VT2CTP.get(req.offset, ""),
            "OrderRef": str(self.order_ref),
            "InvestorID": self.userid,
            "UserID": self.userid,
            "BrokerID": self.brokerid,
            "CombHedgeFlag": THOST_FTDC_HF_Speculation,
            "ContingentCondition": THOST_FTDC_CC_Immediately,
            "ForceCloseReason": THOST_FTDC_FCC_NotForceClose,
            "IsAutoSuspend": 0,
            "TimeCondition": THOST_FTDC_TC_GFD,
            "VolumeCondition": THOST_FTDC_VC_AV,
            "MinVolume": 1
        }

        if req.type == OrderType.FAK:
            ctp_req["OrderPriceType"] = THOST_FTDC_OPT_LimitPrice
            ctp_req["TimeCondition"] = THOST_FTDC_TC_IOC
            ctp_req["VolumeCondition"] = THOST_FTDC_VC_AV
        elif req.type == OrderType.FOK:
            ctp_req["OrderPriceType"] = THOST_FTDC_OPT_LimitPrice
            ctp_req["TimeCondition"] = THOST_FTDC_TC_IOC
            ctp_req["VolumeCondition"] = THOST_FTDC_VC_CV

        self.reqid += 1
        self.reqOrderInsert(ctp_req, self.reqid)

        orderid = f"{self.frontid}_{self.sessionid}_{self.order_ref}"
        order = req.create_order_data(orderid, self.gateway_name)
        self.gateway.on_order(order)

        return order.vt_orderid

    def cancel_order(self, req: CancelRequest):
        """
        Cancel existing order.
        """
        frontid, sessionid, order_ref = req.orderid.split("_")

        ctp_req = {
            "InstrumentID": req.symbol,
            "ExchangeID": req.exchange.value,
            "OrderRef": order_ref,
            "FrontID": int(frontid),
            "SessionID": int(sessionid),
            "ActionFlag": THOST_FTDC_AF_Delete,
            "BrokerID": self.brokerid,
            "InvestorID": self.userid
        }

        self.reqid += 1
        self.reqOrderAction(ctp_req, self.reqid)

    def query_account(self):
        """
        Query account balance data.
        """
        self.reqid += 1
        self.reqQryTradingAccount({}, self.reqid)

    def query_position(self):
        """
        Query position holding data.
        """
        if not symbol_exchange_map:
            return

        req = {
            "BrokerID": self.brokerid,
            "InvestorID": self.userid
        }

        self.reqid += 1
        self.reqQryInvestorPosition(req, self.reqid)

    def query_order(self):
        """查询当日委托"""
        req = {
            "BrokerID": self.brokerid,
            "InvestorID": self.userid
        }
        self.reqid += 1
        self.reqQryOrder(req, self.reqid)

    def close(self):
        """"""
        if self.connect_status:
            self.exit()
