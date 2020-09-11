import datetime
from typing import List, Dict, Type
import pyqtgraph as pg
import time
from vnpy.event import Event, EventEngine
from vnpy.trader.engine import MainEngine
from vnpy.trader.object import (
    MaData
)
from vnpy.trader.utility import ArrayManager
from vnpy.trader.constant import Direction
from datetime import datetime
from vnpy.chart import ChartWidget, VolumeItem, CandleItem
from MyLang.metadata import RunEnvironment, get_current_expr
from MyLang.metadata import Variable
from vnpy.app.editor_manager.engine import EditorEngine
from vnpy.trader.object import (
    HistoryRequest,
)
from vnpy.trader.utility import BarGenerator
import re

# K线

from vnpy.trader.ui import QtGui, QtWidgets, QtCore
from vnpy.trader.object import BarData, TickData, ContractData

from vnpy.trader.event import (
    EVENT_TICK,
    EVENT_CURRENT_CONTRACT,
    EVENT_CURRENT_SYMBOL,
    EVENT_CURRENT_INTERVAL,
    EVENT_SCATTER,
    EVENT_MA,
    EVENT_CLEAN,
    EVENT_INFO,
    EVENT_NEW_K,
    EVENT_TIMER

)
from vnpy.trader.constant import Direction, Offset, OrderType, Interval, Status,Exchange
from vnpy.trader.constant import Interval, Exchange
from vnpy.chart.manager import BarManager
from vnpy.chart.base import (
    GREY_COLOR, WHITE_COLOR, CURSOR_COLOR, BLACK_COLOR,
    to_int, NORMAL_FONT
)
from vnpy.chart.axis import DatetimeAxis
from vnpy.chart.item import ChartItem
from vnpy.trader.database import database_manager
from vnpy.trader.jqdata import readCTP
from PyQt5.QtCore import QTimer
COLOR_LONG = QtGui.QColor("red")
COLOR_SHORT = QtGui.QColor("green")
COLOR_BID = QtGui.QColor(255, 174, 201)
COLOR_ASK = QtGui.QColor(160, 255, 160)
COLOR_BLACK = QtGui.QColor("black")

from vnpy.trader.jqdata import jqdata_client

# @Time    : 2019-09-17
# @Author  : 龙文浩
# 绘制k线图


class KLineMonitor(pg.PlotWidget):
    MIN_BAR_COUNT = 100

    def __init__(self, main_engine: MainEngine,  event_engine: EventEngine, parent: QtWidgets.QWidget = None):
        super(KLineMonitor, self).__init__(parent)
        self.main_engine = main_engine
        self.event_engine = event_engine
        self.bar_generator = None

        self._manager: BarManager = BarManager()

        self._plots: Dict[str, pg.PlotItem] = {}
        self._items: Dict[str, ChartItem] = {}
        self._item_plot_map: Dict[ChartItem, pg.PlotItem] = {}

        self.current_interval = "1m"
        self.current_contract: ContractData = None
        self.current_tick: TickData = None

        self._first_plot: pg.PlotItem = None
        self._cursor: ChartCursor = None

        self._right_ix: int = 0  # Index of most right data
        self._bar_count: int = self.MIN_BAR_COUNT  # Total bar visible in chart
        self._bars: List[BarData] = []
        self._init_ui()

        # @Time    : 2019-09-24
        # @Author  : Wang Yongchang
        # 绘制默认K线图元素，没有数据
        self.add_plot("candle", hide_x_axis=False)
        #self.add_plot("volume", maximum_height=200)
        self.add_item(CandleItem, "candle", "candle")
        #self.add_item(VolumeItem, "volume", "volume")
        self.add_cursor()
        self.dt_ix_map = {}
        self.updated = False
        self.trade_scatter = pg.ScatterPlotItem()
        candle_plot = self.get_plot("candle")
        # 向该plot中添加散点视图
        candle_plot.addItem(self.trade_scatter)
        # 2019-12-23 用于装显示在图上的信息
        self.info = {}

        # @Time    : 2019-09-24
        # @Author  : Wang Yongchang
        # 注册事件
        self._register_event()

        # 设置启动定时器
        # self.timer = QTimer()
        # self.timer.setInterval(10000)
        # self.timer.start()
        # self.timer.timeout.connect(self.onTimerOut)
        self.all_orders = None
        self.all_positions = None

    def _init_ui(self) -> None:
        """"""
        self._layout = pg.GraphicsLayout()
        self._layout.setContentsMargins(10, 10, 10, 10)
        self._layout.setSpacing(0)
        self._layout.setBorder(color=GREY_COLOR, width=0.8)
        self._layout.setZValue(0)
        self.setCentralItem(self._layout)

        self._x_axis = DatetimeAxis(self._manager, orientation='bottom')

        # @Time    : 2019-09-24
        # @Author  : Wang Yongchang
        # 注册事件
    def _register_event(self) -> None:
        self.event_engine.register(EVENT_TICK, self.process_tick_event)
        self.event_engine.register(EVENT_CURRENT_CONTRACT, self.process_current_contract_event)
        self.event_engine.register(EVENT_CURRENT_SYMBOL, self.process_current_contract_event)
        self.event_engine.register(EVENT_TIMER, self.process_timer_event)
        # @Time    : 2019-09-26
        # @Author  : Long WenHao
        # 接收EVENT_CURRENT_INTERVAL事件
        self.event_engine.register(EVENT_CURRENT_INTERVAL, self.process_current_interval)
        # 绘制散点图(交易标记)
        self.event_engine.register(EVENT_SCATTER, self.process_scatter)
        # 绘制MA均线
        self.event_engine.register(EVENT_MA, self.process_ma)
        # 清空
        self.event_engine.register(EVENT_CLEAN,self.process_clean)
        # 信息显示
        self.event_engine.register(EVENT_INFO, self.process_info)

    # def onTimerOut(self):
    #     all_positions = self.main_engine.get_all_positions()
    #     all_orders = self.main_engine.get_all_orders()
    #
    #     if all_positions and (self.all_orders!=all_orders or self.all_positions!=all_positions):
    #
    #         r = readCTP()
    #         #print(all_positions[0].symbol)
    #         size = r.readFile(all_positions[0].symbol)
    #         data = {"symbol": all_positions[0].symbol,"size": size,"price":all_positions[0].price,"all_orders": all_orders,
    #                 "all_positions": all_positions}
    #         event = Event(EVENT_DEPOSIT, data)
    #         self.event_engine.put(event)
    #         self.all_orders = all_orders
    #         self.all_positions = all_positions
    #         #self.timer.stop()
    #         #readCTP.readFile(all_positions[0].symbol)

    # @Time    : 2019-09-26
    # @Author  : Long WenHao
    # 发送处理EVENT_CURRENT_INTERVAL事件
    def process_current_interval(self, event):
        self.current_interval = event.data
        self.process_clean(event)
        self.clear_all()
        self.process_current_contract_event(event)

    # @Time    : 2019-09-24
    # @Author  : Wang Yongchang
    # 处理实时tick数据

    def process_tick_event(self, event) -> None:
        tick = event.data

        #print(tick)
        # if self._right_ix >= (self._manager.get_count() - self._bar_count / 2):
        #     self._update_x_range()
        # self._cursor.update_info()
        if self._bars:
            if self.current_contract.symbol == tick.symbol:
                if self._bars[0].interval.value == "d":
                    self._bars = self.get_day_bar(tick, self._bars)
                    self.main_engine.current_bars = self._bars
                    self.update_history(self._bars)
                #elif self._bars[0].interval.value == "1m":

                    # 使用BarGenerator
                    # self.bar_generator = BarGenerator(self.on_generated_bar, 1)
                    # self.bar_generator.update_tick(tick)
                    # print(self.bar_generator.bar)

                    latest_bar = self._bars[-2]

                    # 每分钟校正一次，从JQ获取新的数据
                    # if tick.datetime.hour != latest_bar.datetime.hour:
                    #     self._bars = self.get_jq_bars(self.current_contract.symbol, "1m", 300)
                    # else:
                        # 每分钟校正一次，从JQ获取新的数据
                    #bar = None
                    # if tick.datetime.minute != latest_bar.datetime.minute:
                    #     try:
                    #         bars = self.get_jq_bars(self.current_contract.symbol, "1m", 2)[-2:]
                    #         print(bars)
                    #         for b in bars:
                    #             if b.datetime.minute == tick.datetime.minute:
                    #                 bar = b
                    #
                    #     except:
                    #         pass
                    #
                    # if self._bars[-1] != bar and bar:
                    #     self._bars.append(bar)
                    #     self.update_bar(bar)
                    #
                    #
                    #
                    # if self._bars[-1].datetime not in self.dt_ix_map:
                    #
                    #
                    #     for ix, bar in enumerate(self._bars):
                    #         self.dt_ix_map[bar.datetime] = ix
                    #     #print(self.dt_ix_map)
                    #
                    #     self.main_engine.current_bars = self._bars
                    #
                    #     # 注册事件，表示k线已更新
                    #     event = Event(EVENT_NEW_K, "newKline")
                    #     self.event_engine.put(event)
                    #     items = {}
                    #     for item_name, item in self._items.items():
                    #         # print(item_name)
                    #
                    #         for item_name, item in self._items.items():
                    #             if item_name == "candle":
                    #                 items[item_name] = item
                    #         if item_name != "candle":
                    #             candle = self.get_plot("candle")
                    #             candle.removeItem(item)
                    #     self._items = items

    def process_timer_event(self,event):
        now = datetime.now()
        bar = None
        if self._bars:
            #print(self._bars[-1])

            if self._bars[0].interval.value == "1m":
                #print("在更新")
                latest_bar = self._bars[-2]
                if now.minute != latest_bar.datetime.minute:
                    try:
                        bars = self.get_jq_bars(self.current_contract.symbol, "1m", 2)[-2:]
                        #print(bars)
                        for b in bars:
                            if b.datetime.minute == now.minute:
                                bar = b

                    except:
                        pass

                if self._bars[-1] != bar and bar:
                    self._bars.append(bar)
                    self.main_engine.current_bars = self._bars
                    self.update_bar(bar)
                if self._bars[-1].datetime not in self.dt_ix_map:

                    for ix, bar in enumerate(self._bars):
                        self.dt_ix_map[bar.datetime] = ix
                    # 注册事件，表示k线已更新
                    event = Event(EVENT_NEW_K, "newKline")
                    self.event_engine.put(event)
                    items = {}
                    for item_name, item in self._items.items():
                        # print(item_name)

                        for item_name, item in self._items.items():
                            if item_name == "candle":
                                items[item_name] = item
                        if item_name != "candle":
                            candle = self.get_plot("candle")
                            candle.removeItem(item)
                    self._items = items
            elif self._bars[-1].datetime.minute % int(''.join(re.findall(r"\d+\.?\d*",self._bars[0].interval.value))) != 0:
                #print(int(''.join(re.findall(r"\d+\.?\d*",self._bars[0].interval.value))))
                self._bars = self._bars[:-1]

                if self._bars[-1].datetime.minute + int(''.join(re.findall(r"\d+\.?\d*",self._bars[0].interval.value))) == now.minute:
                    #print("进来了")
                    try:
                        bars = self.get_jq_bars(self.current_contract.symbol, self._bars[0].interval.value, int(''.join(re.findall(r"\d+\.?\d*",self._bars[0].interval.value))))[-int(''.join(re.findall(r"\d+\.?\d*",self._bars[0].interval.value))):]
                        #print(bars)
                        # print(bars)
                        for b in bars:
                            if b.datetime.minute == now.minute:
                                bar = b

                    except:
                        pass

                    if self._bars[-1] != bar and bar:
                        self._bars.append(bar)
                        self.main_engine.current_bars = self._bars
                        self.update_bar(bar)
                    # if self._bars[-1].datetime not in self.dt_ix_map:
                    #     self.dt_ix_map.clear()
                    #     for ix, bar in enumerate(self._bars):
                    #         self.dt_ix_map[bar.datetime] = ix
                    #     # 注册事件，表示k线已更新
                    #     event = Event(EVENT_NEW_K, "newKline")
                    #     self.event_engine.put(event)
                    #     items = {}
                    #     for item_name, item in self._items.items():
                    #         # print(item_name)
                    #
                    #         for item_name, item in self._items.items():
                    #             if item_name == "candle":
                    #                 items[item_name] = item
                    #         if item_name != "candle":
                    #             candle = self.get_plot("candle")
                    #             candle.removeItem(item)
                    #     self._items = items
                # print(str(latest_bar.datetime.minute)[-1])
                # print(self._bars)
            #     if self._bars[-5].datetime.minute == 10:
            #         print("yes")
                # print(latest_bar)
                # print(self._bars[-1])
                # print(latest_bar.datetime.minute)
        # if now.minute
        # self.count += 1
        # if self.count % 6 == 0:
        #     self.count = 1



    # @Time    : 2019-09-24
    # @Author  : Wang Yongchang
    # 处理点击根据当前Contract获取rqdata数据

    def process_current_contract_event(self, event) -> None:

        self.process_clean(event)
        self.clear_all()
        self._bars = []
        if type(event.data) != str:
            self.current_contract = event.data

        if self.current_interval == "d":
            self._bars = self.get_jq_bars(self.current_contract.symbol, "d", 300)
        elif self.current_interval == "1h":
            self._bars = self.get_jq_bars(self.current_contract.symbol, "1h", 300)
        elif self.current_interval == "1m":
            self._bars = self.get_jq_bars(self.current_contract.symbol, "1m", 300)

        elif self.current_interval == "5m":
            self._bars = self.get_jq_bars(self.current_contract.symbol, "5m", 300)
        elif self.current_interval == "15m":
            self._bars = self.get_jq_bars(self.current_contract.symbol, "15m", 300)

        if self._bars and self.current_contract:

            if self._bars[0].interval.value == "d":
                if self.current_tick:
                    now = datetime.now()
                    current_bar = BarData(
                        gateway_name='JQ',
                        symbol=self.current_tick.symbol,
                        exchange=self.current_tick.exchange,
                        interval=Interval('d'),
                        datetime=datetime(now.year, now.month, now.day, 0, 0),
                        volume=self.current_tick.volume,
                        open_price=self.current_tick.open_price,
                        high_price=self.current_tick.high_price,
                        low_price=self.current_tick.low_price,
                        close_price=self.current_tick.last_price,
                    )
                    self._bars.append(current_bar)

                self.update_history(self._bars[:-1])

            elif self._bars[0].interval.value == "1h":
                self.update_history(self._bars[:-1])
            elif self._bars[0].interval.value == "1m":
                self.update_history(self._bars[:-1])
                # self.update_trades(self._bars,"BK",1,"close_price")
            elif self._bars[0].interval.value == "5m":
                self.update_history(self._bars[:-1])
                # self.update_trades(trades)
            elif self._bars[0].interval.value == "15m":
                self.update_history(self._bars[:-1])
                # self.update_trades(trades)

            self.main_engine.current_bars = self._bars[:-1]
            #self.event_engine.unregister(EVENT_CURRENT_INTERVAL, self.process_current_interval)

    def process_scatter(self,event):
        self.update_trades(event.data)

    def process_ma(self, event):
        # 清空ma
        # if self._items.__contains__(str(event.data["name"])) == True:
        #     time.sleep(1)
        #     # self.process_clean(event)
        #
        #     candle = self.get_plot("candle")
        #     candle.removeItem(self._items[str(event.data["name"])])
        #     self._items.pop(str(event.data["name"]))
        if self._items.__contains__(str(event.data["name"])) == False:
            #print(event.data["name"])
        # if event.data["name"] not in self._items:
            datas: List[MaData] = []
            info = {}
            for bar in self._bars[:-1]:
                print(bar)
                print(self.dt_ix_map)
                #print("ix:" + str(self.dt_ix_map[bar.datetime]))
                if self.dt_ix_map[bar.datetime] >= int(event.data["period"]) - 1 and len(self.dt_ix_map) == len(
                        event.data["sma"]):
                    data = event.data["sma"][self.dt_ix_map[bar.datetime]]
                    # print("dt:"+str(data))
                    info[int(self.dt_ix_map[bar.datetime])] = data
                    m = MaData(
                        t=int(self.dt_ix_map[bar.datetime]),
                        # datetime=bar.datetime,
                        open=float(bar.open_price),
                        close=float(bar.close_price),
                        min=float(bar.low_price),
                        max=float(bar.high_price),
                        volume=float(bar.volume),
                        ma=float(data)
                    )
                    datas.append(m)

            # self._cursor.init_inf(info)
            maItem = MaItem(datas, event.data["period"])
            self.addMa(maItem, str(event.data["name"]), "candle")
            name = ""
            if event.data["period"] == 5:
                name = str(event.data["name"]) + "(白色)"
            elif event.data["period"] == 10:
                name = str(event.data["name"]) + "(青色)"
            elif event.data["period"] == 20:
                name = str(event.data["name"]) + "(粉色)"
            event = Event(EVENT_INFO, {"name": name, "data": info})
            self.process_info(event)
            return


    def process_info(self,event):


        #if not self.info.__contains__(event.data["name"]):
        self.info[event.data["name"]] = event.data["data"]
        # else:
        #     self.info.pop(event.data["name"])
        #     self.info[event.data["name"]] = event.data["data"]



        self._cursor.init_inf(self.info)
        #self._cursor.init_inf(event.data)

    # 清空
    def process_clean(self,event):
        #print(self._items.__contains__("ma5"))


        items = {}
        for item_name,item in self._items.items():

            if item_name == "candle":
                items[item_name] = item
            #print(item_name)
            if item_name != "candle":
                candle = self.get_plot("candle")
                candle.removeItem(item)

        self._items = items
        self.updated = False

        self.trade_scatter.clear()



    def get_day_bar(self, tick: TickData, bars: List[BarData]) -> List[BarData]:
        bars[-1].volume = tick.volume
        bars[-1].high_price = tick.high_price
        bars[-1].low_price = tick.low_price
        bars[-1].close_price = tick.last_price
        return bars

    def get_minute_bar(self, tick: TickData, bars: List[BarData]) -> List[BarData]:
        if tick.last_price > bars[-1].high_price:
            bars[-1].high_price = tick.last_price
        if tick.last_price < bars[-1].low_price:
            bars[-1].low_price = tick.last_price
        bars[-1].close_price = tick.last_price
        return bars

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

    def add_cursor(self) -> None:
        """"""
        if not self._cursor:
            self._cursor = ChartCursor(
                self, self._manager, self._plots, self._item_plot_map,self.event_engine)

    def add_plot(
            self,
            plot_name: str,
            minimum_height: int = 80,
            maximum_height: int = None,
            hide_x_axis: bool = False
    ) -> None:
        """
        Add plot area.
        """
        # Create plot object
        plot = pg.PlotItem(axisItems={'bottom': self._x_axis})
        plot.setMenuEnabled(False)
        plot.setClipToView(True)
        plot.hideAxis('left')
        plot.showAxis('right')
        plot.setDownsampling(mode='peak')
        plot.setRange(xRange=(0, 1), yRange=(0, 1))
        plot.hideButtons()
        plot.setMinimumHeight(minimum_height)

        if maximum_height:
            plot.setMaximumHeight(maximum_height)

        if hide_x_axis:
            plot.hideAxis("bottom")

        if not self._first_plot:
            self._first_plot = plot

        # Connect view change signal to update y range function
        view = plot.getViewBox()
        view.sigXRangeChanged.connect(self._update_y_range)
        view.setMouseEnabled(x=True, y=False)

        # Set right axis
        right_axis = plot.getAxis('right')
        right_axis.setWidth(60)
        right_axis.tickFont = NORMAL_FONT

        # Connect x-axis link
        if self._plots:
            first_plot = list(self._plots.values())[0]
            plot.setXLink(first_plot)

        # Store plot object in dict
        self._plots[plot_name] = plot

    def add_item(
            self,
            item_class: Type[ChartItem],
            item_name: str,
            plot_name: str
    ):
        """
        Add chart item.
        """
        item = item_class(self._manager)
        self._items[item_name] = item

        plot = self._plots.get(plot_name)
        plot.addItem(item)
        self._item_plot_map[item] = plot

        self._layout.nextRow()
        self._layout.addItem(plot)

    def addMa(
        self,
        item: pg.GraphicsObject,
        item_name: str,
        plot_name: str
    ):
        """
        Add chart item.
        """
        #item = item_class(self._manager)
        self._items[item_name] = item

        plot = self._plots.get(plot_name)
        plot.addItem(item)

    def get_plot(self, plot_name: str) -> pg.PlotItem:
        """
        Get specific plot with its name.
        """
        return self._plots.get(plot_name, None)

    def get_all_plots(self) -> List[pg.PlotItem]:
        """
        Get all plot objects.
        """
        return self._plots.values()

    def clear_all(self) -> None:
        """
        Clear all data.
        """
        self._manager.clear_all()
        self.dt_ix_map.clear()
        self.trade_scatter.clear()
        for item_name,item in self._items.items():
            if item_name != "candle":
                candle = self.get_plot("candle")
                candle.removeItem(item)


        if self._cursor:
            self._cursor.clear_all()

    def update_history(self, history: List[BarData]) -> None:
        """
        Update a list of bar data.
        """
        self.updated = True
        self._manager.update_history(history)

        for item_name ,item in self._items.items():
            #
            # print(item.__name__)
            if item_name == "candle":
                item.update_history(history)

        self._update_plot_limits()
        for ix, bar in enumerate(history):
            self.dt_ix_map[bar.datetime] = ix


    def update_bar(self, bar: BarData) -> None:
        """
        Update single bar data.
        """
        self._manager.update_bar(bar)

        for item_name ,item in self._items.items():
            #
            # print(item.__name__)
            if item_name == "candle":
                item.update_bar(bar)
        # for item in self._items.values():
        #     item.update_bar(bar)

        self._update_plot_limits()

        if self._right_ix >= (self._manager.get_count() - self._bar_count / 2):
            self.move_to_right()


    def update_trades(self, scatter:{}):
        up = 5
        down = 5
        trade_data = []
        for k,v in scatter.items():

            scat = {
                    "pos": (int(k), float(v["price"])),
                    "data": 1,
                    "size": 13,
                    "pen": pg.mkPen((255, 255, 255))
                }


            if v["offset"] == Offset.OPEN and v["direction"] == Direction.LONG:
                scat["symbol"] = "t1"
                # 红色 多 向上 开多
                scat["brush"] = pg.mkBrush((255,0,0))
                scat["pen"] = pg.mkPen((255,0,0))
                scat["pos"] = (int(k), float(v["price"] - down * v["num"]))

            elif v["offset"] == Offset.OPEN and v["direction"] == Direction.SHORT:
                scat["symbol"] = "t1"
                # 绿色 空 向上 开空
                scat["brush"] = pg.mkBrush((0, 255, 0))
                scat["pen"] = pg.mkPen((0, 255, 0))
                scat["pos"] = (int(k), float(v["price"] - down * v["num"]))

            elif v["offset"] == Offset.CLOSE and v["direction"] == Direction.LONG:
                scat["symbol"] = "t"
                # 绿色 多 向下 平多
                scat["brush"] = pg.mkBrush((0, 0, 0))
                scat["pen"] = pg.mkPen((0, 255, 0))
                scat["pos"] = (int(k), float(v["price"] + up * v["num"]))

            elif v["offset"] == Offset.CLOSE and v["direction"] == Direction.SHORT:
                scat["symbol"] = "t"
                # 红色 空 向下 平空
                scat["brush"] = pg.mkBrush((0, 0, 0))
                scat["pen"] = pg.mkPen((255, 0, 0))
                scat["pos"] = (int(k), float(v["price"] + up * v["num"]))

            trade_data.append(scat)
            up = 5
            down = 5
        self.trade_scatter.setData(trade_data)



    def _update_plot_limits(self) -> None:
        """
        Update the limit of plots.
        """
        for item, plot in self._item_plot_map.items():
            min_value, max_value = item.get_y_range()

            plot.setLimits(
                xMin=-1,
                xMax=self._manager.get_count(),
                yMin=min_value,
                yMax=max_value
            )

    def _update_x_range(self) -> None:
        """
        Update the x-axis range of plots.
        """
        max_ix = self._right_ix
        min_ix = self._right_ix - self._bar_count

        for plot in self._plots.values():
            plot.setRange(xRange=(min_ix, max_ix), padding=0)

    def _update_y_range(self) -> None:
        """
        Update the y-axis range of plots.
        """
        view = self._first_plot.getViewBox()
        view_range = view.viewRange()

        min_ix = max(0, int(view_range[0][0]))
        max_ix = min(self._manager.get_count(), int(view_range[0][1]))

        # Update limit for y-axis
        for item, plot in self._item_plot_map.items():
            y_range = item.get_y_range(min_ix, max_ix)
            plot.setRange(yRange=y_range)

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        """
        Reimplement this method of parent to update current max_ix value.
        """
        view = self._first_plot.getViewBox()
        view_range = view.viewRange()
        self._right_ix = max(0, view_range[0][1])

        super().paintEvent(event)

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        """
        Reimplement this method of parent to move chart horizontally and zoom in/out.
        """
        if event.key() == QtCore.Qt.Key_Left:
            self._on_key_left()
        elif event.key() == QtCore.Qt.Key_Right:
            self._on_key_right()
        elif event.key() == QtCore.Qt.Key_Up:
            self._on_key_up()
        elif event.key() == QtCore.Qt.Key_Down:
            self._on_key_down()

    def wheelEvent(self, event: QtGui.QWheelEvent) -> None:
        """
        Reimplement this method of parent to zoom in/out.
        """
        delta = event.angleDelta()

        if delta.y() > 0:
            self._on_key_up()
        elif delta.y() < 0:
            self._on_key_down()

    def _on_key_left(self) -> None:
        """
        Move chart to left.
        """
        self._right_ix -= 1
        self._right_ix = max(self._right_ix, self._bar_count)

        self._update_x_range()
        self._cursor.move_left()
        self._cursor.update_info()

    def _on_key_right(self) -> None:
        """
        Move chart to right.
        """
        self._right_ix += 1
        self._right_ix = min(self._right_ix, self._manager.get_count())

        self._update_x_range()
        self._cursor.move_right()
        self._cursor.update_info()

    def _on_key_down(self) -> None:
        """
        Zoom out the chart.
        """
        self._bar_count *= 1.2
        self._bar_count = min(int(self._bar_count), self._manager.get_count())

        self._update_x_range()
        self._cursor.update_info()

    def _on_key_up(self) -> None:
        """
        Zoom in the chart.
        """
        self._bar_count /= 1.2
        self._bar_count = max(int(self._bar_count), self.MIN_BAR_COUNT)

        self._update_x_range()
        self._cursor.update_info()

    def move_to_right(self) -> None:
        """
        Move chart to the most right.
        """
        self._right_ix = self._manager.get_count()
        self._update_x_range()
        #self._cursor.update_info()


class ChartCursor(QtCore.QObject):
    """"""
    def __init__(
            self,
            widget: ChartWidget,
            manager: BarManager,
            plots: Dict[str, pg.GraphicsObject],
            item_plot_map: Dict[ChartItem, pg.GraphicsObject],
            event_engine: EventEngine,
            #items: Dict[str, pg.GraphicsObject],

    ):
        """"""
        super().__init__()

        self._widget: ChartWidget = widget
        self._manager: BarManager = manager
        self._plots: Dict[str, pg.GraphicsObject] = plots
        self._item_plot_map: Dict[ChartItem, pg.GraphicsObject] = item_plot_map

        self._x: int = 0
        self._y: int = 0
        self._plot_name: str = ""

        self.current_interval = "1m"
        self.event_engine = event_engine


        self._init_ui()
        self._connect_signal()
        # 2019-12-15 lwh
        #self.items = items
        self.dt_ix = {}
        self.info_item = Dict[str, pg.TextItem]
        for plot_name, plot in self._plots.items():

            #print(plot_name)
            self.inf = pg.TextItem(
                "info",
                color=CURSOR_COLOR,
                border=CURSOR_COLOR,
                fill=BLACK_COLOR
            )
            self.inf.hide()
            self.inf.setZValue(2)
            self.inf.setFont(NORMAL_FONT)
            plot.addItem(self.inf)  # , ignoreBounds=True)
        #plot = self._plots["candle"]
        # for item in self.items:
        #     inf = pg.TextItem(
        #         "info",
        #         color=CURSOR_COLOR,
        #         border=CURSOR_COLOR,
        #         fill=BLACK_COLOR
        #     )
        #     inf.hide()
        #     inf.setZValue(2)
        #     inf.setFont(NORMAL_FONT)
        #     plot.addItem(inf)  # , ignoreBounds=True)
        #     self.info_item[""]
        #     #print(plot_name)
        #     # self.inf = pg.TextItem(
        #     #     "info",
        #     #     color=CURSOR_COLOR,
        #     #     border=CURSOR_COLOR,
        #     #     fill=BLACK_COLOR
        #     # )
        #     # self.inf.hide()
        #     # self.inf.setZValue(2)
        #     # self.inf.setFont(NORMAL_FONT)
        #     # plot.addItem(self.inf)  # , ignoreBounds=True)


    def init_inf(self,dt_ix:{}):

        self.dt_ix = dt_ix

    # def clear_inf(self):
    #


    def process_current_interval(self, event):
        self.current_interval = event.data


    def _init_ui(self):
        """"""
        self._init_line()
        self._init_label()
        self._init_info()

    def _init_line(self) -> None:
        """
        Create line objects.
        """
        self._v_lines: Dict[str, pg.InfiniteLine] = {}
        self._h_lines: Dict[str, pg.InfiniteLine] = {}
        self._views: Dict[str, pg.ViewBox] = {}

        pen = pg.mkPen(WHITE_COLOR)

        for plot_name, plot in self._plots.items():
            v_line = pg.InfiniteLine(angle=90, movable=False, pen=pen)
            h_line = pg.InfiniteLine(angle=0, movable=False, pen=pen)
            view = plot.getViewBox()

            for line in [v_line, h_line]:
                line.setZValue(0)
                line.hide()
                view.addItem(line)

            self._v_lines[plot_name] = v_line
            self._h_lines[plot_name] = h_line
            self._views[plot_name] = view

    def _init_label(self) -> None:
        """
        Create label objects on axis.
        """
        self._y_labels: Dict[str, pg.TextItem] = {}
        for plot_name, plot in self._plots.items():
            label = pg.TextItem(
                plot_name, fill=CURSOR_COLOR, color=BLACK_COLOR)
            label.hide()
            label.setZValue(2)
            label.setFont(NORMAL_FONT)
            plot.addItem(label, ignoreBounds=True)
            self._y_labels[plot_name] = label

        self._x_label: pg.TextItem = pg.TextItem(
            "datetime", fill=CURSOR_COLOR, color=BLACK_COLOR)
        self._x_label.hide()
        self._x_label.setZValue(2)
        self._x_label.setFont(NORMAL_FONT)
        plot.addItem(self._x_label, ignoreBounds=True)

    def _init_info(self) -> None:
        """
        """
        self._infos: Dict[str, pg.TextItem] = {}
        for plot_name, plot in self._plots.items():
            info = pg.TextItem(
                "info",
                color=CURSOR_COLOR,
                border=CURSOR_COLOR,
                fill=BLACK_COLOR
            )
            info.hide()
            info.setZValue(2)
            info.setFont(NORMAL_FONT)
            plot.addItem(info)  # , ignoreBounds=True)
            self._infos[plot_name] = info



    def _connect_signal(self) -> None:
        """
        Connect mouse move signal to update function.
        """
        self._widget.scene().sigMouseMoved.connect(self._mouse_moved)

    def _mouse_moved(self, evt: tuple) -> None:
        """
        Callback function when mouse is moved.
        """
        if not self._manager.get_count():
            return

        # First get current mouse point
        pos = evt

        for plot_name, view in self._views.items():
            rect = view.sceneBoundingRect()

            if rect.contains(pos):
                mouse_point = view.mapSceneToView(pos)
                self._x = to_int(mouse_point.x())
                self._y = mouse_point.y()
                self._plot_name = plot_name
                break

        # Then update cursor component
        self._update_line()
        self._update_label()
        self.update_info()

        if self.dt_ix:
            #print(self.dt_ix)
            for plot_name, plot in self._plots.items():
                #info = self._infos[plot_name]
                # print(plot_info_text)
                try:
                    text = ""
                    for k,v in self.dt_ix.items():
                        text += k+":"+str(v[int(self._x)])+"\n"
                    self.inf.setText(text)
                    #self.inf.setText("bkhigh:"+self.dt_ix[int(self._x)])
                    self.inf.show()
                    #print(plot_name)
                    view = self._views[plot_name]
                    coodinate = QtCore.QPointF(100,0)
                #view = self._views["candle"]
                    top_left = view.mapSceneToView(view.sceneBoundingRect().topLeft()+coodinate)
                    # print(view.sceneBoundingRect())
                    # print(view.sceneBoundingRect().topLeft())
                    # print(top_left)
                    #print(self._x)

                    self.inf.setPos(top_left)
                except:
                    print("该K线无数据")

    def _update_line(self) -> None:
        """"""
        for v_line in self._v_lines.values():
            v_line.setPos(self._x)
            v_line.show()

        for plot_name, h_line in self._h_lines.items():
            if plot_name == self._plot_name:
                h_line.setPos(self._y)
                h_line.show()
            else:
                h_line.hide()

    def _update_label(self) -> None:
        """"""
        bottom_plot = list(self._plots.values())[-1]
        axis_width = bottom_plot.getAxis("right").width()
        axis_height = bottom_plot.getAxis("bottom").height()
        axis_offset = QtCore.QPointF(axis_width, axis_height)

        bottom_view = list(self._views.values())[-1]
        bottom_right = bottom_view.mapSceneToView(
            bottom_view.sceneBoundingRect().bottomRight() - axis_offset
        )
        # LWH 2019-10-30
        bottom_left = bottom_view.mapSceneToView(
            bottom_view.sceneBoundingRect().bottomLeft() + 3 * axis_offset
        )
        for plot_name, label in self._y_labels.items():
            if plot_name == self._plot_name:
                label.setText(str(self._y))
                label.show()
                label.setPos(bottom_right.x(), self._y)
            else:
                label.hide()

        dt = self._manager.get_datetime(self._x)
        if dt:
            self._x_label.setText(dt.strftime("%Y-%m-%d %H:%M:%S"))
            self._x_label.show()
            #self._x_label.setPos(self._x, bottom_right.y())
            self._x_label.setPos(bottom_left.x(), bottom_right.y())
            self._x_label.setAnchor((0, 0))

    def update_info(self) -> None:
        """"""
        buf = {}

        for item, plot in self._item_plot_map.items():
            item_info_text = item.get_info_text(self._x)

            if plot not in buf:
                buf[plot] = item_info_text
            else:
                if item_info_text:
                    buf[plot] += ("\n\n" + item_info_text)

        for plot_name, plot in self._plots.items():
            plot_info_text = buf[plot]
            info = self._infos[plot_name]
            info.setText(plot_info_text)
            info.show()

            view = self._views[plot_name]
            top_left = view.mapSceneToView(view.sceneBoundingRect().topLeft())
            info.setPos(top_left)

    def move_right(self) -> None:
        """
        Move cursor index to right by 1.
        """
        if self._x == self._manager.get_count() - 1:
            return
        self._x += 1

        self._update_after_move()

    def move_left(self) -> None:
        """
        Move cursor index to left by 1.
        """
        if self._x == 0:
            return
        self._x -= 1

        self._update_after_move()

    def _update_after_move(self) -> None:
        """
        Update cursor after moved by left/right.
        """
        bar = self._manager.get_bar(self._x)
        self._y = bar.close_price

        self._update_line()
        self._update_label()

    def clear_all(self) -> None:
        """
        Clear all data.
        """
        self._x = 0
        self._y = 0
        self._plot_name = ""

        for line in list(self._v_lines.values()) + list(self._h_lines.values()):
            line.hide()

        for label in list(self._y_labels.values()) + [self._x_label]:
            label.hide()


class MaItem(pg.GraphicsObject):
    def __init__(self, data,period):
        pg.GraphicsObject.__init__(self)
        self.data = data
        self.period = period
        self.generatePicture()

    def generatePicture(self):

        self.picture = QtGui.QPicture()
        p = QtGui.QPainter(self.picture)
        # 白色
        p.setPen(pg.mkPen('w'))
        prema5 = 0
        prema10 = 0
        prema20 = 0

        for m in self.data:

            if prema5 != 0 and self.period == 5:
                # 白色
                p.setPen(pg.mkPen('w'))
                p.setBrush(pg.mkBrush('w'))
                p.drawLine(QtCore.QPointF(m.t - 1, prema5), QtCore.QPointF(m.t, m.ma))
            prema5 = m.ma
            if prema10 != 0 and self.period == 10:
                # 青色
                p.setPen(pg.mkPen('c'))
                p.setBrush(pg.mkBrush('c'))
                p.drawLine(QtCore.QPointF(m.t - 1, prema10), QtCore.QPointF(m.t, m.ma))
            prema10 = m.ma
            if prema20 != 0 and self.period == 20:
                # 品色
                p.setPen(pg.mkPen('m'))
                p.setBrush(pg.mkBrush('m'))
                p.drawLine(QtCore.QPointF(m.t - 1, prema20), QtCore.QPointF(m.t, m.ma))
            prema20 = m.ma
        p.end()

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QtCore.QRectF(self.picture.boundingRect())
