""""""
from datetime import datetime
import pandas as pd
from typing import List, Optional, Sequence, Type

from peewee import (
    CompositeKey,
    AutoField,
    CharField,
    Database,
    DateTimeField,
    BooleanField,
    IntegerField,
    FloatField,
    Model,
    MySQLDatabase,
    PostgresqlDatabase,
    SqliteDatabase,
    chunked,
)

from vnpy.trader.constant import (
    Exchange,
    Interval,
    Product,
    Direction,
    Offset,
)

from vnpy.trader.object import BarData, TickData, ContractData, TradeData,OrderData
from vnpy.trader.utility import get_file_path
from .database import BaseDatabaseManager, Driver


def init(driver: Driver, settings: dict):
    init_funcs = {
        Driver.SQLITE: init_sqlite,
        Driver.MYSQL: init_mysql,
        Driver.POSTGRESQL: init_postgresql,
    }
    assert driver in init_funcs

    db = init_funcs[driver](settings)
    bar, tick, contract, trade,order = init_models(db, driver)
    return SqlManager(bar, tick, contract, trade,order)


def init_sqlite(settings: dict):
    database = settings["database"]
    path = str(get_file_path(database))
    db = SqliteDatabase(path)
    return db


def init_mysql(settings: dict):
    keys = {"database", "user", "password", "host", "port"}
    settings = {k: v for k, v in settings.items() if k in keys}
    db = MySQLDatabase(**settings)
    return db


def init_postgresql(settings: dict):
    keys = {"database", "user", "password", "host", "port"}
    settings = {k: v for k, v in settings.items() if k in keys}
    db = PostgresqlDatabase(**settings)
    return db


class ModelBase(Model):

    def to_dict(self):
        return self.__data__


def init_models(db: Database, driver: Driver):
    class DbBarData(ModelBase):
        """
        Candlestick bar data for database storage.

        Index is defined unique with datetime, interval, symbol
        """

        id = AutoField()
        symbol: str = CharField()
        exchange: str = CharField()
        datetime: datetime = DateTimeField()
        interval: str = CharField()

        volume: float = FloatField()
        open_interest: float = FloatField()
        open_price: float = FloatField()
        high_price: float = FloatField()
        low_price: float = FloatField()
        close_price: float = FloatField()

        class Meta:
            database = db
            indexes = ((("symbol", "exchange", "interval", "datetime"), True),)

        @staticmethod
        def from_bar(bar: BarData):
            """
            Generate DbBarData object from BarData.
            """
            db_bar = DbBarData()
            db_bar.symbol = bar.symbol
            db_bar.exchange = bar.exchange.value
            db_bar.datetime = bar.datetime
            db_bar.interval = bar.interval.value
            db_bar.volume = bar.volume
            db_bar.open_interest = bar.open_interest
            db_bar.open_price = bar.open_price
            db_bar.high_price = bar.high_price
            db_bar.low_price = bar.low_price
            db_bar.close_price = bar.close_price
            return db_bar

        def to_bar(self):
            """
            Generate BarData object from DbBarData.
            """
            bar = BarData(
                symbol=self.symbol,
                exchange=Exchange(self.exchange),
                datetime=self.datetime,
                interval=Interval(self.interval),
                volume=self.volume,
                open_price=self.open_price,
                high_price=self.high_price,
                open_interest=self.open_interest,
                low_price=self.low_price,
                close_price=self.close_price,
                gateway_name="DB",
            )
            return bar

        @staticmethod
        def save_all(objs: List["DbBarData"]):
            """
            save a list of objects, update if exists.
            """
            dicts = [i.to_dict() for i in objs]
            with db.atomic():
                if driver is Driver.POSTGRESQL:
                    for bar in dicts:
                        DbBarData.insert(bar).on_conflict(
                            update=bar,
                            conflict_target=(
                                DbBarData.symbol,
                                DbBarData.exchange,
                                DbBarData.interval,
                                DbBarData.datetime,
                            ),
                        ).execute()
                else:
                    for c in chunked(dicts, 50):
                        DbBarData.insert_many(
                            c).on_conflict_replace().execute()

    class DbTickData(ModelBase):
        """
        Tick data for database storage.

        Index is defined unique with (datetime, symbol)
        """

        id = AutoField()

        symbol: str = CharField()
        exchange: str = CharField()
        datetime: datetime = DateTimeField()

        name: str = CharField()
        volume: float = FloatField()
        open_interest: float = FloatField()
        last_price: float = FloatField()
        last_volume: float = FloatField()
        limit_up: float = FloatField()
        limit_down: float = FloatField()

        open_price: float = FloatField()
        high_price: float = FloatField()
        low_price: float = FloatField()
        pre_close: float = FloatField()

        bid_price_1: float = FloatField()
        bid_price_2: float = FloatField(null=True)
        bid_price_3: float = FloatField(null=True)
        bid_price_4: float = FloatField(null=True)
        bid_price_5: float = FloatField(null=True)

        ask_price_1: float = FloatField()
        ask_price_2: float = FloatField(null=True)
        ask_price_3: float = FloatField(null=True)
        ask_price_4: float = FloatField(null=True)
        ask_price_5: float = FloatField(null=True)

        bid_volume_1: float = FloatField()
        bid_volume_2: float = FloatField(null=True)
        bid_volume_3: float = FloatField(null=True)
        bid_volume_4: float = FloatField(null=True)
        bid_volume_5: float = FloatField(null=True)

        ask_volume_1: float = FloatField()
        ask_volume_2: float = FloatField(null=True)
        ask_volume_3: float = FloatField(null=True)
        ask_volume_4: float = FloatField(null=True)
        ask_volume_5: float = FloatField(null=True)

        class Meta:
            database = db
            indexes = ((("symbol", "exchange", "datetime"), True),)

        @staticmethod
        def from_tick(tick: TickData):
            """
            Generate DbTickData object from TickData.
            """
            db_tick = DbTickData()

            db_tick.symbol = tick.symbol
            db_tick.exchange = tick.exchange.value
            db_tick.datetime = tick.datetime
            db_tick.name = tick.name
            db_tick.volume = tick.volume
            db_tick.open_interest = tick.open_interest
            db_tick.last_price = tick.last_price
            db_tick.last_volume = tick.last_volume
            db_tick.limit_up = tick.limit_up
            db_tick.limit_down = tick.limit_down
            db_tick.open_price = tick.open_price
            db_tick.high_price = tick.high_price
            db_tick.low_price = tick.low_price
            db_tick.pre_close = tick.pre_close

            db_tick.bid_price_1 = tick.bid_price_1
            db_tick.ask_price_1 = tick.ask_price_1
            db_tick.bid_volume_1 = tick.bid_volume_1
            db_tick.ask_volume_1 = tick.ask_volume_1

            if tick.bid_price_2:
                db_tick.bid_price_2 = tick.bid_price_2
                db_tick.bid_price_3 = tick.bid_price_3
                db_tick.bid_price_4 = tick.bid_price_4
                db_tick.bid_price_5 = tick.bid_price_5

                db_tick.ask_price_2 = tick.ask_price_2
                db_tick.ask_price_3 = tick.ask_price_3
                db_tick.ask_price_4 = tick.ask_price_4
                db_tick.ask_price_5 = tick.ask_price_5

                db_tick.bid_volume_2 = tick.bid_volume_2
                db_tick.bid_volume_3 = tick.bid_volume_3
                db_tick.bid_volume_4 = tick.bid_volume_4
                db_tick.bid_volume_5 = tick.bid_volume_5

                db_tick.ask_volume_2 = tick.ask_volume_2
                db_tick.ask_volume_3 = tick.ask_volume_3
                db_tick.ask_volume_4 = tick.ask_volume_4
                db_tick.ask_volume_5 = tick.ask_volume_5

            return db_tick

        def to_tick(self):
            """
            Generate TickData object from DbTickData.
            """
            tick = TickData(
                symbol=self.symbol,
                exchange=Exchange(self.exchange),
                datetime=self.datetime,
                name=self.name,
                volume=self.volume,
                open_interest=self.open_interest,
                last_price=self.last_price,
                last_volume=self.last_volume,
                limit_up=self.limit_up,
                limit_down=self.limit_down,
                open_price=self.open_price,
                high_price=self.high_price,
                low_price=self.low_price,
                pre_close=self.pre_close,
                bid_price_1=self.bid_price_1,
                ask_price_1=self.ask_price_1,
                bid_volume_1=self.bid_volume_1,
                ask_volume_1=self.ask_volume_1,
                gateway_name="DB",
            )

            if self.bid_price_2:
                tick.bid_price_2 = self.bid_price_2
                tick.bid_price_3 = self.bid_price_3
                tick.bid_price_4 = self.bid_price_4
                tick.bid_price_5 = self.bid_price_5

                tick.ask_price_2 = self.ask_price_2
                tick.ask_price_3 = self.ask_price_3
                tick.ask_price_4 = self.ask_price_4
                tick.ask_price_5 = self.ask_price_5

                tick.bid_volume_2 = self.bid_volume_2
                tick.bid_volume_3 = self.bid_volume_3
                tick.bid_volume_4 = self.bid_volume_4
                tick.bid_volume_5 = self.bid_volume_5

                tick.ask_volume_2 = self.ask_volume_2
                tick.ask_volume_3 = self.ask_volume_3
                tick.ask_volume_4 = self.ask_volume_4
                tick.ask_volume_5 = self.ask_volume_5

            return tick

        @staticmethod
        def save_all(objs: List["DbTickData"]):
            dicts = [i.to_dict() for i in objs]
            with db.atomic():
                if driver is Driver.POSTGRESQL:
                    for tick in dicts:
                        DbTickData.insert(tick).on_conflict(
                            update=tick,
                            conflict_target=(
                                DbTickData.symbol,
                                DbTickData.exchange,
                                DbTickData.datetime,
                            ),
                        ).execute()
                else:
                    for c in chunked(dicts, 50):
                        DbTickData.insert_many(c).on_conflict_replace().execute()

    class DbContractData(ModelBase):
        id: str = CharField()
        symbol: str = CharField()
        exchange: str = CharField()
        name: str = CharField()
        product: str = CharField()
        size: int = IntegerField()
        pricetick: float = FloatField()
        min_volume: float = FloatField()  # minimum trading volume of the contract
        stop_supported: bool = BooleanField()  # whether server supports stop order
        net_position: bool = BooleanField()  # whether gateway uses net position volume
        history_data: bool = BooleanField()  # whether gateway provides bar history data

        option_strike: float = FloatField()
        option_underlying: str = CharField()  # vt_symbol of underlying contract
        option_type: str = CharField(null=True)
        option_expiry: datetime = DateTimeField(null=True)

        class Meta:
            database = db
            indexes = ((("symbol", "symbol", "exchange"), True),)

        @staticmethod
        def from_contract(contract: ContractData):
            """
            Generate DbContractData object from ContractData.
            """

            db_contract = DbContractData()
            db_contract.id = contract.symbol + "." + contract.exchange.value
            db_contract.symbol = contract.symbol
            db_contract.exchange = contract.exchange.value
            db_contract.name = contract.name
            db_contract.product = contract.product.value
            db_contract.size = contract.size
            db_contract.pricetick = contract.pricetick

            db_contract.min_volume = contract.min_volume
            db_contract.stop_supported = contract.stop_supported
            db_contract.net_position = contract.net_position
            db_contract.history_data = contract.history_data

            db_contract.option_strike = contract.option_strike
            db_contract.option_underlying = contract.option_underlying
            db_contract.option_type = contract.option_type
            db_contract.option_expiry = contract.option_expiry

            return db_contract

        def to_contract(self):
            """
            Generate ContractData object from DbContractData.
            """
            contract = ContractData(
                symbol=self.symbol,
                exchange=Exchange(self.exchange),
                name=self.name,
                product=Product(self.product),
                size=self.size,
                pricetick=self.pricetick,
                min_volume=self.min_volume,
                stop_supported=self.stop_supported,
                net_position=self.net_position,
                history_data=self.history_data,
                option_strike=self.option_strike,
                option_expiry=self.option_expiry,
                # option_type=OptionType(self.option_type),
                # 因为option_type没有值，会实例化失败，暂时to_contract过程中不实例化
                option_type=self.option_type,
                option_underlying=self.option_underlying,
                gateway_name="DB",
            )
            return contract

        @staticmethod
        def save_all(objs: List["DbContractData"]):
            """
            save a list of objects, update if exists.
            """
            dicts = [i.to_dict() for i in objs]
            with db.atomic():
                if driver is Driver.POSTGRESQL:
                    for contract in dicts:
                        DbContractData.insert(contract).on_conflict(
                            update=contract,
                            conflict_target=(
                                DbContractData.id,
                            ),
                        ).execute()
                else:
                    for c in chunked(dicts, 50):
                        DbContractData.insert_many(
                            c).on_conflict_ignore().execute()

    class DbTradeData(ModelBase):
        id: str = CharField()
        accountid: str = CharField()
        symbol: str = CharField()
        exchange: str = CharField()
        orderid: str = CharField()
        tradeid: str = CharField()
        direction: str = CharField()
        offset: str = CharField()
        price: float = FloatField()
        volume: int = IntegerField()
        datetime: datetime = DateTimeField()
        #time: datetime = DateTimeField()

        class Meta:
            database = db
            indexes = ((("id", "orderid"), True),)

        @staticmethod
        def from_trade(trade: TradeData):
            """
            Generate DbContractData object from ContractData.
            """
            db_trade = DbTradeData()
            #
            db_trade.id = trade.orderid
            db_trade.accountid = trade.accountid
            db_trade.symbol = trade.symbol
            db_trade.exchange = trade.exchange.value
            db_trade.orderid = trade.orderid
            db_trade.tradeid = trade.tradeid
            db_trade.direction = trade.direction.value
            db_trade.offset = trade.offset.value
            db_trade.price = trade.price
            db_trade.volume = trade.volume
            db_trade.datetime = datetime.now().strftime("%Y%m%d %H:%M:%S")

            return db_trade

        def to_trade(self):
            """
            Generate ContractData object from DbContractData.
            """
            trade = TradeData(
                accountid=self.accountid,
                symbol=self.symbol,
                exchange=Exchange(self.exchange),
                orderid=self.orderid,
                tradeid=self.tradeid,
                direction=Direction(self.direction),
                offset=Offset(self.offset),
                price=self.price,
                volume=self.volume,
                datetime=self.datetime,
                gateway_name="DB"
            )

            return trade

        @staticmethod
        def save_all(objs: List["DbTradeData"]):
            """
            save a list of objects, update if exists.
            """
            dicts = [i.to_dict() for i in objs]
            with db.atomic():
                if driver is Driver.POSTGRESQL:
                    for trade in dicts:
                        DbTradeData.insert(trade).on_conflict(
                            update=trade,
                            conflict_target=(
                                DbTradeData.id,
                            ),
                        ).execute()
                else:
                    for c in chunked(dicts, 50):
                        DbTradeData.insert_many(
                            c).on_conflict_ignore().execute()

    # @Author : LongWenHao
    # @Time : 2020.3.9
    # @Dec : OrderData
    class DbOrderData(ModelBase):
        id: str = CharField()
        accountid: str = CharField()
        symbol: str = CharField()
        exchange: str = CharField()
        orderid: str = CharField()
        type: str = CharField()
        direction: str = CharField()
        offset: str = CharField()
        price: float = FloatField()
        volume: int = IntegerField()
        traded: float = FloatField()
        status: str = CharField()
        time: datetime = DateTimeField()

        class Meta:
            database = db
            indexes = ((("id", "orderid"), True),)

        @staticmethod
        def from_order(order: OrderData):
            """
            Generate DbContractData object from ContractData.
            """
            db_order = DbOrderData()
            #
            db_order.id = order.orderid
            db_order.accountid = order.accountid
            db_order.symbol = order.symbol
            db_order.exchange = order.exchange.value
            db_order.orderid = order.orderid
            db_order.type = order.type
            db_order.direction = order.direction.value
            db_order.offset = order.offset.value
            db_order.price = order.price
            db_order.volume = order.volume
            db_order.traded = order.traded
            db_order.status = order.status
            db_order.time = datetime.now().strftime("%Y%m%d %H:%M:%S")

            return db_order

        def to_order(self):
            """
            Generate ContractData object from DbContractData.
            """
            order = OrderData(
                accountid=self.accountid,
                symbol=self.symbol,
                exchange=Exchange(self.exchange),
                orderid=self.orderid,
                type=self.type,
                direction=Direction(self.direction),
                offset=Offset(self.offset),
                price=self.price,
                volume=self.volume,
                traded=self.traded,
                status=self.status,
                time=self.time,
                gateway_name="DB"
            )

            return order

        @staticmethod
        def save_all(objs: List["DbOrderData"]):
            """
            save a list of objects, update if exists.
            """
            dicts = [i.to_dict() for i in objs]
            with db.atomic():
                if driver is Driver.POSTGRESQL:
                    for order in dicts:
                        DbOrderData.insert(order).on_conflict(
                            update=order,
                            conflict_target=(
                                DbOrderData.id,
                            ),
                        ).execute()
                else:
                    for c in chunked(dicts, 50):
                        DbOrderData.insert_many(
                            c).on_conflict_ignore().execute()

    db.connect()
    db.create_tables([DbBarData, DbTickData, DbContractData, DbTradeData,DbOrderData])
    return DbBarData, DbTickData, DbContractData, DbTradeData,DbOrderData


class SqlManager(BaseDatabaseManager):

    def __init__(self, class_bar: Type[Model], class_tick: Type[Model], class_contract: Type[Model], class_trade: Type[Model],class_order:Type[Model]):
        self.class_bar = class_bar
        self.class_tick = class_tick
        self.class_contract = class_contract
        self.class_trade = class_trade
        self.class_order = class_order

    def load_bar_data(
        self,
        symbol: str,
        exchange: Exchange,
        interval: Interval,
        start: datetime,
        end: datetime,
    ) -> Sequence[BarData]:
        s = (
            self.class_bar.select()
                .where(
                (self.class_bar.symbol == symbol)
                & (self.class_bar.exchange == exchange.value)
                & (self.class_bar.interval == interval.value)
                & (self.class_bar.datetime >= start)
                & (self.class_bar.datetime <= end)
            )
            .order_by(self.class_bar.datetime)
        )
        data = [db_bar.to_bar() for db_bar in s]
        return data

    def load_tick_data(
        self, symbol: str, exchange: Exchange, start: datetime, end: datetime
    ) -> Sequence[TickData]:
        s = (
            self.class_tick.select()
                .where(
                (self.class_tick.symbol == symbol)
                & (self.class_tick.exchange == exchange.value)
                & (self.class_tick.datetime >= start)
                & (self.class_tick.datetime <= end)
            )
            .order_by(self.class_tick.datetime)
        )

        data = [db_tick.to_tick() for db_tick in s]
        return data

    def save_bar_data(self, datas: Sequence[BarData]):
        ds = [self.class_bar.from_bar(i) for i in datas]
        self.class_bar.save_all(ds)

    def save_tick_data(self, datas: Sequence[TickData]):
        ds = [self.class_tick.from_tick(i) for i in datas]
        self.class_tick.save_all(ds)

    def get_newest_bar_data(
        self, symbol: str, exchange: "Exchange", interval: "Interval"
    ) -> Optional["BarData"]:
        s = (
            self.class_bar.select()
                .where(
                (self.class_bar.symbol == symbol)
                & (self.class_bar.exchange == exchange.value)
                & (self.class_bar.interval == interval.value)
            )
            .order_by(self.class_bar.datetime.desc())
            .first()
        )
        if s:
            return s.to_bar()
        return None

    def get_newest_tick_data(
        self, symbol: str, exchange: "Exchange"
    ) -> Optional["TickData"]:
        s = (
            self.class_tick.select()
                .where(
                (self.class_tick.symbol == symbol)
                & (self.class_tick.exchange == exchange.value)
            )
            .order_by(self.class_tick.datetime.desc())
            .first()
        )
        if s:
            return s.to_tick()
        return None

    # @Author : Yangjintao
    # @Time : 2019.10.09
    # @Dec : 从SQLite加载、保存、获取最新contract data
    def load_all_contract_data(
            self
    ) -> Sequence["ContractData"]:
        """
        获取所有合约数据
        """
        s = (
            self.class_contract.select()
        )
        data = [db_contract.to_contract() for db_contract in s]
        return data

    def load_contract_by_symbol(
        self, symbol: str,
    ) -> Sequence[ContractData]:
        s = (
            self.class_contract.select()
                .where(
                (self.class_contract.symbol == symbol)
            )
        )

        data = [db_contract.to_contract() for db_contract in s]
        # data = []
        # for db_trade in s:
        #     data.append(db_trade)
        return data

    def save_contract_data(
            self,
            datas: Sequence["ContractData"],
    ):
        ds = [self.class_contract.from_contract(data) for data in datas]
        self.class_contract.save_all(ds)



    def get_newest_contract_data(
            self,
            symbol: str,
    ) -> Optional["ContractData"]:
        """
        根据symbol获取一条合约数据
        """
        s = (
            self.class_contract.select()
                .where(
                self.class_contract.symbol == symbol
            )
                .first()
        )
        if s:
            return s.to_contract()
        return None

    # @Author : WangYongchang
    # @Time : 2019.10.18
    # @Dec : 从SQLite加载、保存、获取最新trade data

    def save_trade_data(
        self, datas: Sequence["ContractData"],
    ):
        ds = [self.class_trade.from_trade(data) for data in datas]
        self.class_trade.save_all(ds)

    def load_trades_by_symbol(
        self, symbol: str,
    ) -> Sequence[TradeData]:
        s = (
            self.class_trade.select()
                .where(
                (self.class_trade.symbol == symbol)
            )
            .order_by(self.class_trade.datetime)
        )

        data = [db_trade.to_trade() for db_trade in s]
        # data = []
        # for db_trade in s:
        #     data.append(db_trade)
        return data

    def load_trades_by_orderid(
        self, orderid: str,
    ) -> Sequence[TradeData]:
        s = (
            self.class_trade.select()
                .where(
                (self.class_trade.orderid == orderid)
            )
            .order_by(self.class_trade.datetime)
        )

        data = [db_trade.to_trade() for db_trade in s]
        # data = []
        # for db_trade in s:
        #     data.append(db_trade)
        return data


    # @Author : LongWenHao
    # @Time : 2019.10.18
    # @Dec : 从SQLite加载trade data
    def load_all_trade_data(
            self
    ) -> Sequence["TradeData"]:
        """
        获取所有合约数据
        """
        s = (
            self.class_trade.select()
        )
        data = [db_trade.to_trade() for db_trade in s]
        return data

    # @Author : LongWenHao
    # @Time : 2020.3.9
    # @Dec : 存储OrderData
    def save_order_data(self,datas:Sequence["OrderData"]):
        ds = [self.class_order.from_order(data) for data in datas]
        self.class_order.save_all(ds)

    # @Author : LongWenHao
    # @Time : 2020.3.9
    # @Dec : 按symbol查询OrderData
    def load_orders_by_symbol(
        self, symbol: str,
    ) -> Sequence[OrderData]:
        s = (
            self.class_order.select()
                .where(
                (self.class_order.symbol == symbol)
            )
            .order_by(self.class_order.time)
        )

        data = [db_order.to_order() for db_order in s]
        # data = []
        # for db_order in s:
        #     data.append(db_order)
        return data

    # @Author : LongWenHao
    # @Time : 2020.3.9
    # @Dec : 从SQLite加载OrderData
    def load_all_order_data(
            self
    ) -> Sequence["OrderData"]:
        """
        获取所有合约数据
        """
        s = (
            self.class_order.select()
        )
        data = [db_order.to_order() for db_order in s]
        return data

    # @Author : LongWenHao
    # @Time : 2020.3.9
    # @Dec : 按orderid查询OrderData
    def load_order_by_orderid(
            self, orderid: str,
    ) -> Sequence[OrderData]:
        s = (
            self.class_order.select()
                .where(
                (self.class_order.orderid == orderid)
            )
                .order_by(self.class_order.time)
        )

        data = [db_order.to_order() for db_order in s]
        # data = []
        # for db_order in s:
        #     data.append(db_order)
        return data

    def clean(self, symbol: str):
        self.class_bar.delete().where(self.class_bar.symbol == symbol).execute()
        self.class_tick.delete().where(self.class_tick.symbol == symbol).execute()
        self.class_contract.delete().where(self.class_contract.symbol == symbol).execute()
        self.class_trade.delete().where(self.class_trade.symbol == symbol).execute()
        self.class_order.delete().where(self.class_order.symbol == symbol).execute()