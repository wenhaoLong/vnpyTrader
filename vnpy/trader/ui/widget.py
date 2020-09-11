"""
Basic widgets for VN Trader.
"""
import socket
import csv
import time
import threading
from enum import Enum
from typing import Any
from copy import copy

from PyQt5 import QtCore, QtGui, QtWidgets
from vnpy.trader.event import EVENT_TIMER
from vnpy.event import Event, EventEngine
from ..constant import Direction, Exchange, Offset, OrderType
from ..engine import MainEngine
from ..event import (
    EVENT_TICK,
    EVENT_TRADE,
    EVENT_ORDER,
    EVENT_POSITION,
    EVENT_ACCOUNT,
    EVENT_CONTRACT,
    EVENT_CURRENT_CONTRACT,
    EVENT_CURRENT_POSITION,
    EVENT_CURRENT_TRADE,
    EVENT_CURRENT_SYMBOL,
    EVENT_LOG
)
from ..object import (
    TickData,
    AccountData,
    PositionData,
    OrderData,
    TradeData,
    OrderRequest,
    SubscribeRequest
)
from ..utility import load_json, save_json
from ..setting import SETTING_FILENAME, SETTINGS

# 2020-5-12 lwh
from vnpy.trader.database.initialize import init
from vnpy.trader.setting import get_settings

COLOR_LONG = QtGui.QColor("red")
COLOR_SHORT = QtGui.QColor("green")
COLOR_BID = QtGui.QColor(255, 174, 201)
COLOR_ASK = QtGui.QColor(160, 255, 160)
COLOR_BLACK = QtGui.QColor("black")


class BaseCell(QtWidgets.QTableWidgetItem):
    """
    General cell used in tablewidgets.
    """

    def __init__(self, content: Any, data: Any):
        """"""
        super(BaseCell, self).__init__()
        self.setTextAlignment(QtCore.Qt.AlignCenter)
        self.set_content(content, data)

    def set_content(self, content: Any, data: Any):
        """
        Set text content.
        """
        self.setText(str(content))
        self._data = data

    def get_data(self):
        """
        Get data object.
        """
        return self._data


class EnumCell(BaseCell):
    """
    Cell used for showing enum data.
    """

    def __init__(self, content: str, data: Any):
        """"""
        super(EnumCell, self).__init__(content, data)

    def set_content(self, content: Any, data: Any):
        """
        Set text using enum.constant.value.
        """
        if content:
            super(EnumCell, self).set_content(content.value, data)


class DirectionCell(EnumCell):
    """
    Cell used for showing direction data.
    """

    def __init__(self, content: str, data: Any):
        """"""
        super(DirectionCell, self).__init__(content, data)

    def set_content(self, content: Any, data: Any):
        """
        Cell color is set according to direction.
        """
        super(DirectionCell, self).set_content(content, data)

        if content is Direction.SHORT:
            self.setForeground(COLOR_SHORT)
        else:
            self.setForeground(COLOR_LONG)


class BidCell(BaseCell):
    """
    Cell used for showing bid price and volume.
    """

    def __init__(self, content: Any, data: Any):
        """"""
        super(BidCell, self).__init__(content, data)

        self.setForeground(COLOR_BLACK)
        self.setForeground(COLOR_BID)


class AskCell(BaseCell):
    """
    Cell used for showing ask price and volume.
    """

    def __init__(self, content: Any, data: Any):
        """"""
        super(AskCell, self).__init__(content, data)

        self.setForeground(COLOR_BLACK)
        self.setForeground(COLOR_ASK)


class PnlCell(BaseCell):
    """
    Cell used for showing pnl data.
    """

    def __init__(self, content: Any, data: Any):
        """"""
        super(PnlCell, self).__init__(content, data)

    def set_content(self, content: Any, data: Any):
        """
        Cell color is set based on whether pnl is 
        positive or negative.
        """
        super(PnlCell, self).set_content(content, data)

        if str(content).startswith("-"):
            self.setForeground(COLOR_SHORT)
        else:
            self.setForeground(COLOR_LONG)


class TimeCell(BaseCell):
    """
    Cell used for showing time string from datetime object.
    """

    def __init__(self, content: Any, data: Any):
        """"""
        super(TimeCell, self).__init__(content, data)

    def set_content(self, content: Any, data: Any):
        """
        Time format is 12:12:12.5
        """
        timestamp = content.strftime("%H:%M:%S")

        millisecond = int(content.microsecond / 1000)
        if millisecond:
            timestamp = f"{timestamp}.{millisecond}"

        self.setText(timestamp)
        self._data = data


class MsgCell(BaseCell):
    """
    Cell used for showing msg data.
    """

    def __init__(self, content: str, data: Any):
        """"""
        super(MsgCell, self).__init__(content, data)
        self.setTextAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)


class BaseMonitor(QtWidgets.QTableWidget):
    """
    Monitor data update in VN Trader.
    """

    event_type = ""
    data_key = ""
    sorting = False
    headers = {}

    signal = QtCore.pyqtSignal(Event)

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        """"""
        super(BaseMonitor, self).__init__()

        self.main_engine = main_engine
        self.event_engine = event_engine
        self.cells = {}

        self.init_ui()
        self.register_event()

    def init_ui(self):
        """"""
        self.init_table()
        self.init_menu()

    def init_table(self):
        """
        Initialize table.
        """

        # @Time    : 2019-09-12
        # @Author  : Wang Yongchang
        desktop = QtWidgets.QDesktopWidget()
        self.screen_width = desktop.screenGeometry().width()
        self.screen_height = desktop.screenGeometry().height()

        self.setFixedHeight(self.screen_height * 0.185)

        self.setColumnCount(len(self.headers))

        labels = [d["display"] for d in self.headers.values()]
        self.setHorizontalHeaderLabels(labels)

        self.verticalHeader().setVisible(False)
        self.setEditTriggers(self.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(self.sorting)

    def init_menu(self):
        """
        Create right click menu.
        """
        self.menu = QtWidgets.QMenu(self)

        resize_action = QtWidgets.QAction("调整列宽", self)
        resize_action.triggered.connect(self.resize_columns)
        self.menu.addAction(resize_action)

        save_action = QtWidgets.QAction("保存数据", self)
        save_action.triggered.connect(self.save_csv)
        self.menu.addAction(save_action)

    def register_event(self):
        """
        Register event handler into event engine.
        """
        if self.event_type:
            self.signal.connect(self.process_event)
            self.event_engine.register(self.event_type, self.signal.emit)

    def process_event(self, event):
        """
        Process new data from event and update into table.
        """
        # Disable sorting to prevent unwanted error.
        if self.sorting:
            self.setSortingEnabled(False)

        # Update data into table.
        data = event.data
        print(data)
        # @Time    : 2019-09-23
        # @Author  : Wang Yongchang
        # 在点击委托之后没有accountid，加上accountid

        if isinstance(data, OrderData) or isinstance(data, TradeData):
            if not data.accountid:
                account = self.main_engine.get_current_account()
                data.accountid = account.accountid

        if not self.data_key:
            self.insert_new_row(data)
        else:
            key = data.__getattribute__(self.data_key)

            if key in self.cells:
                self.update_old_row(data)
            else:
                self.insert_new_row(data)

        # Enable sorting
        if self.sorting:
            self.setSortingEnabled(True)

    def insert_new_row(self, data):

        """
        Insert a new row at the top of table.
        """
        self.insertRow(0)

        row_cells = {}
        for column, header in enumerate(self.headers.keys()):
            setting = self.headers[header]

            content = data.__getattribute__(header)
            cell = setting["cell"](content, data)
            self.setItem(0, column, cell)

            if setting["update"]:
                row_cells[header] = cell

        if self.data_key:
            key = data.__getattribute__(self.data_key)
            self.cells[key] = row_cells

    def update_old_row(self, data):

        """
        Update an old row in table.
        """
        key = data.__getattribute__(self.data_key)
        row_cells = self.cells[key]

        for header, cell in row_cells.items():
            content = data.__getattribute__(header)
            cell.set_content(content, data)

    def remove_row(self,row):
        self.removeRow(row)


    def resize_columns(self):
        """
        Resize all columns according to contents.
        """
        self.horizontalHeader().resizeSections(QtWidgets.QHeaderView.ResizeToContents)

    def save_csv(self):
        """
        Save table data into a csv file
        """
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "保存数据", "", "CSV(*.csv)")

        if not path:
            return

        with open(path, "w") as f:
            writer = csv.writer(f, lineterminator="\n")

            writer.writerow(self.headers.keys())

            for row in range(self.rowCount()):
                row_data = []
                for column in range(self.columnCount()):
                    item = self.item(row, column)
                    if item:
                        row_data.append(str(item.text()))
                    else:
                        row_data.append("")
                writer.writerow(row_data)

    def contextMenuEvent(self, event):
        """
        Show menu with right click.
        """
        self.menu.popup(QtGui.QCursor.pos())


class TickMonitor(BaseMonitor):
    """
    Monitor for tick data.
    """

    event_type = EVENT_TICK
    #data_key = "vt_symbol"
    data_key = "symbol"
    sorting = True

    headers = {
        "symbol": {"display": "代码", "cell": BaseCell, "update": True},
        "exchange": {"display": "交易所", "cell": EnumCell, "update": True},
        "name": {"display": "名称", "cell": BaseCell, "update": True},
        "last_price": {"display": "最新价", "cell": BaseCell, "update": True},
        "volume": {"display": "成交量", "cell": BaseCell, "update": True},
        "open_price": {"display": "开盘价", "cell": BaseCell, "update": True},
        "high_price": {"display": "最高价", "cell": BaseCell, "update": True},
        "low_price": {"display": "最低价", "cell": BaseCell, "update": True},
        "bid_price_1": {"display": "买1价", "cell": BidCell, "update": True},
        "bid_volume_1": {"display": "买1量", "cell": BidCell, "update": True},
        "ask_price_1": {"display": "卖1价", "cell": AskCell, "update": True},
        "ask_volume_1": {"display": "卖1量", "cell": AskCell, "update": True},
        "datetime": {"display": "时间", "cell": TimeCell, "update": True},
        "gateway_name": {"display": "接口", "cell": BaseCell, "update": False},
    }

    # @Time    : 2019-09-16
    # @Author  : Wang Yongchang
    # 点击当前数据行，注册事件，向事件总线发送当前合约

    def init_ui(self):
        """
        Connect signal.
        """
        super(TickMonitor, self).init_ui()
        self.itemDoubleClicked.connect(self.connect_tick)

    def connect_tick(self, cell):
        event = Event(EVENT_CURRENT_CONTRACT, cell.get_data())
        self.event_engine.put(event)


class LogMonitor(BaseMonitor):
    """
    Monitor for log data.
    """
    event_type = EVENT_LOG
    data_key = ""
    sorting = False

    headers = {
        "time": {"display": "时间", "cell": TimeCell, "update": False},
        "msg": {"display": "信息", "cell": MsgCell, "update": False},
        "gateway_name": {"display": "接口", "cell": BaseCell, "update": False},
    }


class TradeMonitor(BaseMonitor):
    """
    Monitor for trade data.
    """
    event_type = EVENT_TRADE
    data_key = ""
    sorting = True

    headers = {
        # @Time    : 2019-09-19
        # @Author  : Wang Yongchang
        # 增加账号accountid，区分多账号

        "accountid": {"display": "账号", "cell": BaseCell, "update": False},
        "tradeid": {"display": "成交号 ", "cell": BaseCell, "update": False},
        "orderid": {"display": "委托号", "cell": BaseCell, "update": False},
        "symbol": {"display": "代码", "cell": BaseCell, "update": False},
        "exchange": {"display": "交易所", "cell": EnumCell, "update": False},
        "direction": {"display": "方向", "cell": DirectionCell, "update": False},
        "offset": {"display": "开平", "cell": EnumCell, "update": False},
        "price": {"display": "价格", "cell": BaseCell, "update": False},
        "volume": {"display": "数量", "cell": BaseCell, "update": False},
        "datetime": {"display": "时间", "cell": BaseCell, "update": False},
        "gateway_name": {"display": "接口", "cell": BaseCell, "update": False},
    }

    # @Time    : 2019-09-17
    # @Author  : Wang Yongchang
    # 点击当前数据行，注册事件，向事件总线发送当前成交

    def init_ui(self):
        """
        Connect signal.
        """
        super(TradeMonitor, self).init_ui()
        self.itemDoubleClicked.connect(self.connect_trade)

    def connect_trade(self, cell):
        # print(cell.get_data().symbol)
        event = Event(EVENT_CURRENT_TRADE, cell.get_data())
        self.event_engine.put(event)


class OrderMonitor(BaseMonitor):
    """
    Monitor for order data.
    """

    event_type = EVENT_ORDER
    data_key = "vt_orderid"
    sorting = True

    headers = {
        # @Time    : 2019-09-19
        # @Author  : Wang Yongchang
        # 增加账号accountid，区分多账号

        "accountid": {"display": "账号", "cell": BaseCell, "update": False},
        "orderid": {"display": "委托号", "cell": BaseCell, "update": False},
        "symbol": {"display": "代码", "cell": BaseCell, "update": False},
        "exchange": {"display": "交易所", "cell": EnumCell, "update": False},
        "type": {"display": "类型", "cell": EnumCell, "update": False},
        "direction": {"display": "方向", "cell": DirectionCell, "update": False},
        "offset": {"display": "开平", "cell": EnumCell, "update": False},
        "price": {"display": "价格", "cell": BaseCell, "update": False},
        "volume": {"display": "总数量", "cell": BaseCell, "update": True},
        "traded": {"display": "已成交", "cell": BaseCell, "update": True},
        "status": {"display": "状态", "cell": EnumCell, "update": True},
        "time": {"display": "时间", "cell": BaseCell, "update": True},
        "gateway_name": {"display": "接口", "cell": BaseCell, "update": False},
    }

    def init_ui(self):
        """
        Connect signal.
        """
        super(OrderMonitor, self).init_ui()

        self.setToolTip("双击单元格撤单")
        self.itemDoubleClicked.connect(self.cancel_order)
        self.count = 1
        self.event_engine.register(EVENT_TIMER, self.process_timer_event)





    def cancel_order(self, cell):
        """
        Cancel order if cell double clicked.
        """
        order = cell.get_data()
        req = order.create_cancel_request()
        self.main_engine.cancel_order(req, order.gateway_name)





    def process_timer_event(self,event):
        self.count += 1
        if self.count % 6 == 0:
            self.count = 1
            items = []
            for k in list(self.cells.keys()):
                if self.cells[k]["status"].text() == "提交中":
                    items = self.findItems(self.cells[k]["status"].text(), QtCore.Qt.MatchEndsWith)
                    del self.cells[k]
                    continue
                    # settings = get_settings("database.")
                    # database_manager: "BaseDatabaseManager" = init(settings=settings)
                    # trade = database_manager.load_trades_by_orderid(k[4:])
                    # print(trade)
                    # if not trade:
                    #     items = self.findItems(self.cells[k]["status"].text(), QtCore.Qt.MatchEndsWith)
                    #     del self.cells[k]
                    #     continue
            if len(items)>0:
                for i in items:
                    self.remove_row(i.row())


class PositionMonitor(BaseMonitor):
    """
    Monitor for position data.
    """

    event_type = EVENT_POSITION
    data_key = "vt_positionid"
    sorting = True

    headers = {

        # @Time    : 2019-09-18
        # @Author  : Wang Yongchang
        # 增加账号accountid，区分多账号

        "accountid": {"display": "账号", "cell": BaseCell, "update": False},
        "symbol": {"display": "代码", "cell": BaseCell, "update": False},
        "exchange": {"display": "交易所", "cell": EnumCell, "update": False},
        "direction": {"display": "方向", "cell": DirectionCell, "update": True},
        "volume": {"display": "数量", "cell": BaseCell, "update": True},
        "yd_volume": {"display": "昨仓", "cell": BaseCell, "update": True},
        "frozen": {"display": "冻结", "cell": BaseCell, "update": True},
        "price": {"display": "均价", "cell": BaseCell, "update": True},
        "pnl": {"display": "盈亏", "cell": PnlCell, "update": True},
        "gateway_name": {"display": "接口", "cell": BaseCell, "update": True},
    }

    # @Time    : 2019-09-18
    # @Author  : Wang Yongchang
    # 点击当前数据行，注册事件，向事件总线发送当前持仓

    def init_ui(self):
        """
        Connect signal.
        """
        super(PositionMonitor, self).init_ui()
        self.itemDoubleClicked.connect(self.connect_position)

    def connect_position(self, cell):
        # print(cell.get_data().symbol)
        event = Event(EVENT_CURRENT_POSITION, cell.get_data())
        # print(event.data)
        self.event_engine.put(event)


class AccountMonitor(BaseMonitor):
    """
    Monitor for account data.
    """

    event_type = EVENT_ACCOUNT
    data_key = "vt_accountid"
    sorting = True

    headers = {
        "accountid": {"display": "账号", "cell": BaseCell, "update": False},
        "balance": {"display": "余额", "cell": BaseCell, "update": True},
        "frozen": {"display": "冻结", "cell": BaseCell, "update": True},
        "deposit": {"display": "持仓保证金", "cell": BaseCell, "update": True},
        "floatPnl": {"display": "浮动盈亏", "cell": BaseCell, "update": True},
        "closePnl": {"display": "平仓盈亏", "cell": BaseCell, "update": True},
        "commission": {"display": "手续费", "cell": BaseCell, "update": True},
        "available": {"display": "可用", "cell": BaseCell, "update": True},
        "gateway_name": {"display": "接口", "cell": BaseCell, "update": False},
    }


class ConnectDialog(QtWidgets.QDialog):
    """
    Start connection of a certain gateway.
    """

    def __init__(self, main_engine: MainEngine, gateway_name: str):
        """"""
        super(ConnectDialog, self).__init__()

        self.main_engine = main_engine
        self.gateway_name = gateway_name
        self.filename = f"connect_{gateway_name.lower()}.json"

        self.widgets = {}

        self.init_ui()

    def init_ui(self):
        """"""
        self.setWindowTitle(f"连接{self.gateway_name}")

        # Default setting provides field name, field data type and field default value.
        default_setting = self.main_engine.get_default_setting(
            self.gateway_name)

        # Saved setting provides field data used last time.
        loaded_setting = load_json(self.filename)

        # Initialize line edits and form layout based on setting.
        form = QtWidgets.QFormLayout()

        for field_name, field_value in default_setting.items():
            field_type = type(field_value)

            if field_type == list:
                widget = QtWidgets.QComboBox()
                # widget.addItems(field_value)

                if field_name in loaded_setting:
                    saved_value = loaded_setting[field_name]
                    widget.addItems(saved_value)
            else:
                # widget = QtWidgets.QLineEdit(str(field_value))
                widget = QtWidgets.QLineEdit()

                if field_name in loaded_setting:
                    saved_value = loaded_setting[field_name]
                    widget.setText(str(saved_value))

            # box = QtWidgets.QHBoxLayout()
            # box.addWidget(widget)
            # box.setStretchFactor(widget, 4)
            # if "服务器" in field_name:
            #     btn = QtWidgets.QPushButton("添加")
            #     box.addWidget(btn)
            #     box.setStretchFactor(btn, 1)
            #
            # form.addRow(f"{field_name} <{field_type.__name__}>", box)
            form.addRow(f"{field_name} <{field_type.__name__}>", widget)
            self.widgets[field_name] = (widget, field_type)

        add_server_button = QtWidgets.QPushButton("添加服务器")
        add_server_button.clicked.connect(self.add_server)
        form.addRow(add_server_button)

        delete_server_button = QtWidgets.QPushButton("删除服务器")
        delete_server_button.clicked.connect(self.delete_server)
        form.addRow(delete_server_button)

        server_test_button = QtWidgets.QPushButton("服务器测试")
        server_test_button.clicked.connect(self.server_test)
        form.addRow(server_test_button)

        button = QtWidgets.QPushButton("连接")
        button.clicked.connect(self.connect)
        form.addRow(button)

        self.setLayout(form)
        self.setFixedSize(600, 360)

    def add_server(self):
        class AddServerDialog(QtWidgets.QDialog):
            def __init__(self, parent=None):
                super(AddServerDialog, self).__init__(parent)
                form = QtWidgets.QFormLayout()

                self.type_combox = QtWidgets.QComboBox()
                self.type_combox.addItem("行情服务器")
                self.type_combox.addItem("交易服务器")
                form.addRow("类型", self.type_combox)

                self.address_edit = QtWidgets.QLineEdit()
                form.addRow("地址", self.address_edit)

                accept_btn = QtWidgets.QPushButton("确定")
                accept_btn.clicked.connect(self.accept)
                form.addRow(accept_btn)

                reject_btn = QtWidgets.QPushButton("取消")
                reject_btn.clicked.connect(self.reject)
                form.addRow(reject_btn)

                self.setLayout(form)
                self.setWindowTitle("增加服务器")
                self.setFixedSize(360, 150)

        dialog = AddServerDialog()
        if dialog.exec_():
            combox = self.widgets[dialog.type_combox.currentText()][0]
            combox.addItem(dialog.address_edit.text())

    def delete_server(self):
        _self = self

        class DeleteServerDialog(QtWidgets.QDialog):
            def __init__(self, parent=None):
                super(DeleteServerDialog, self).__init__(parent)
                form = QtWidgets.QFormLayout()

                self.type_combox = QtWidgets.QComboBox()
                self.type_combox.addItem("行情服务器")
                self.type_combox.addItem("交易服务器")
                self.type_combox.currentTextChanged.connect(self.type_change)
                form.addRow("类型", self.type_combox)

                self.address_combobox = QtWidgets.QComboBox()
                combox = _self.widgets[self.type_combox.currentText()][0]
                for i in range(combox.count()):
                    item = combox.itemText(i)
                    self.address_combobox.addItem(item)
                form.addRow("地址", self.address_combobox)

                accept_btn = QtWidgets.QPushButton("删除")
                accept_btn.clicked.connect(self.accept)
                form.addRow(accept_btn)

                reject_btn = QtWidgets.QPushButton("取消")
                reject_btn.clicked.connect(self.reject)
                form.addRow(reject_btn)

                self.setLayout(form)
                self.setWindowTitle("删除服务器")
                self.setFixedSize(360, 150)

            def type_change(self):
                self.address_combobox.clear()
                combox = _self.widgets[self.type_combox.currentText()][0]
                for i in range(combox.count()):
                    item = combox.itemText(i)
                    self.address_combobox.addItem(item)

        dialog = DeleteServerDialog()
        if dialog.exec_():
            type = dialog.type_combox.currentText()
            index = dialog.address_combobox.currentIndex()
            self.widgets[type][0].removeItem(index)

    def server_test(self):
        for field_name in self.widgets.keys():
            if "服务器" not in field_name:
                continue
            combox = self.widgets[field_name][0]

            # 初始化时延表
            delays = []
            for i in range(combox.count()):
                delays.append(65535)

            for i in range(combox.count()):
                item = combox.itemText(i)
                print(item)
                # 分割成ip和port
                try:
                    item_split = item.split(":", 1)
                    ip = item_split[0]
                    port = int(item_split[1])
                except Exception as e:
                    QtWidgets.QMessageBox.information(None, "错误", "{!r}: 服务器地址格式错误".format(
                        item))
                    continue
                # 尝试连接服务器
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    start = time.time()
                    sock.connect((ip, port))
                    end = time.time()
                    sock.close()
                    # 计算时延
                    delay = int(round((end - start) * 1000))
                    # 设置时延
                    delays[i] = delay
                except Exception as e:
                    # QtWidgets.QMessageBox.information(None, "错误", "{!r}: 无法连接服务器".format(
                    #     item))
                    continue
            try:
                idx = delays.index(min(delays))
                combox.setCurrentIndex(idx)
                QtWidgets.QMessageBox.information(None, "消息", "选用 {!r} 服务器, 时延为 {}ms".format(
                    combox.currentText(), delays[idx]))
            except Exception as e:
                continue

    def connect(self):
        """
        Get setting value from line edits and connect the gateway.
        """
        self.server_test()
        setting = {}
        for field_name, tp in self.widgets.items():
            widget, field_type = tp
            if field_type == list:
                field_value = str(widget.currentText())
            else:
                field_value = field_type(widget.text())
            setting[field_name] = field_value

        save_setting = {}
        for field_name, tp in self.widgets.items():
            widget, field_type = tp
            if field_type == list:
                field_value = []
                for i in range(widget.count()):
                    field_value.append(widget.itemText(i))
            else:
                field_value = field_type(widget.text())
            save_setting[field_name] = field_value

        save_json(self.filename, save_setting)

        self.main_engine.connect(setting, self.gateway_name)

        self.accept()


class TradingWidget(QtWidgets.QWidget):
    """
    General manual trading widget.
    """

    signal_tick = QtCore.pyqtSignal(Event)
    signal_contract = QtCore.pyqtSignal(Event)
    signal_current_contract = QtCore.pyqtSignal(Event)
    signal_current_position = QtCore.pyqtSignal(Event)
    signal_current_trade = QtCore.pyqtSignal(Event)

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        """"""
        super(TradingWidget, self).__init__()

        self.main_engine = main_engine
        self.event_engine = event_engine

        self.vt_symbol = ""
        self.contracts = []
        self.current_contract = None

        self.exchanges = self.main_engine.get_all_exchanges()
        self.filtered_symbols = []
        self.filtered_names = []
        self.init_ui()
        self.register_event()

    def init_ui(self):
        """"""
        # @Time    : 2019-09-12
        # @Author  : Wang Yongchang
        desktop = QtWidgets.QDesktopWidget()
        self.screen_width = desktop.screenGeometry().width()
        self.screen_height = desktop.screenGeometry().height()

        self.setFixedWidth(self.screen_width * 0.15)

        # Trading function area
        self.exchange_combo = QtWidgets.QComboBox()
        self.exchange_combo.addItems([exchange.value for exchange in self.exchanges])
        self.exchange_combo.currentIndexChanged.connect(self.select_exchange)

        self.name_combo = QtWidgets.QComboBox()
        self.name_combo.currentIndexChanged.connect(self.select_name)

        self.symbol_line = QtWidgets.QLineEdit()
        # self.symbol_line.setReadOnly(True)
        self.symbol_line.returnPressed.connect(self.set_symbol_input)

        self.direction_combo = QtWidgets.QComboBox()
        self.direction_combo.addItems(
            [Direction.LONG.value, Direction.SHORT.value])

        self.offset_combo = QtWidgets.QComboBox()
        self.offset_combo.addItems([offset.value for offset in Offset])

        self.order_type_combo = QtWidgets.QComboBox()
        self.order_type_combo.addItems(
            [order_type.value for order_type in OrderType])

        double_validator = QtGui.QDoubleValidator()
        double_validator.setBottom(0)

        self.price_line = QtWidgets.QLineEdit()
        self.price_line.setValidator(double_validator)

        self.volume_line = QtWidgets.QLineEdit()
        self.volume_line.setValidator(double_validator)

        self.gateway_combo = QtWidgets.QComboBox()
        self.gateway_combo.addItems(self.main_engine.get_all_gateway_names())

        send_button = QtWidgets.QPushButton("委托")
        send_button.clicked.connect(self.send_order)

        cancel_button = QtWidgets.QPushButton("全撤")
        cancel_button.clicked.connect(self.cancel_all)

        form1 = QtWidgets.QFormLayout()

        form1.addRow("交易所", self.exchange_combo)
        form1.addRow("名称", self.name_combo)
        form1.addRow("代码", self.symbol_line)
        form1.addRow("方向", self.direction_combo)
        form1.addRow("开平", self.offset_combo)
        form1.addRow("类型", self.order_type_combo)
        form1.addRow("价格", self.price_line)
        form1.addRow("数量", self.volume_line)
        form1.addRow("接口", self.gateway_combo)
        form1.addRow(send_button)
        form1.addRow(cancel_button)

        # Market depth display area
        bid_color = "rgb(255,174,201)"
        ask_color = "rgb(100,100,255)"

        self.bp1_label = self.create_label(bid_color)
        self.bp2_label = self.create_label(bid_color)
        self.bp3_label = self.create_label(bid_color)
        self.bp4_label = self.create_label(bid_color)
        self.bp5_label = self.create_label(bid_color)

        self.bv1_label = self.create_label(
            bid_color, alignment=QtCore.Qt.AlignRight)
        self.bv2_label = self.create_label(
            bid_color, alignment=QtCore.Qt.AlignRight)
        self.bv3_label = self.create_label(
            bid_color, alignment=QtCore.Qt.AlignRight)
        self.bv4_label = self.create_label(
            bid_color, alignment=QtCore.Qt.AlignRight)
        self.bv5_label = self.create_label(
            bid_color, alignment=QtCore.Qt.AlignRight)

        self.ap1_label = self.create_label(ask_color)
        self.ap2_label = self.create_label(ask_color)
        self.ap3_label = self.create_label(ask_color)
        self.ap4_label = self.create_label(ask_color)
        self.ap5_label = self.create_label(ask_color)

        self.av1_label = self.create_label(
            ask_color, alignment=QtCore.Qt.AlignRight)
        self.av2_label = self.create_label(
            ask_color, alignment=QtCore.Qt.AlignRight)
        self.av3_label = self.create_label(
            ask_color, alignment=QtCore.Qt.AlignRight)
        self.av4_label = self.create_label(
            ask_color, alignment=QtCore.Qt.AlignRight)
        self.av5_label = self.create_label(
            ask_color, alignment=QtCore.Qt.AlignRight)

        self.lp_label = self.create_label()
        self.return_label = self.create_label(alignment=QtCore.Qt.AlignRight)

        form2 = QtWidgets.QFormLayout()
        form2.addRow(self.lp_label, self.return_label)
        form2.addRow(self.ap5_label, self.av5_label)
        form2.addRow(self.ap4_label, self.av4_label)
        form2.addRow(self.ap3_label, self.av3_label)
        form2.addRow(self.ap2_label, self.av2_label)
        form2.addRow(self.ap1_label, self.av1_label)
        form2.addRow(self.bp1_label, self.bv1_label)
        form2.addRow(self.bp2_label, self.bv2_label)
        form2.addRow(self.bp3_label, self.bv3_label)
        form2.addRow(self.bp4_label, self.bv4_label)
        form2.addRow(self.bp5_label, self.bv5_label)

        # Overall layout
        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(form1)
        vbox.addLayout(form2)
        self.setLayout(vbox)

    def create_label(self, color: str = "", alignment: int = QtCore.Qt.AlignLeft):
        """
        Create label with certain font color.
        """
        label = QtWidgets.QLabel()
        if color:
            label.setStyleSheet(f"color:{color}")
        label.setAlignment(alignment)
        return label

    # @Time    : 2019-09-17
    # @Author  : Wang Yongchang
    # 初始化合约名称下拉列表

    def init_name_combo(self):
        self.filtered_names = []
        for contract in self.contracts:
            if contract.exchange.value == self.exchange_combo.currentText():
                self.filtered_names.append(contract.name)
        self.name_combo.addItems(self.filtered_names)

    # @Time    : 2019-09-17
    # @Author  : Wang Yongchang
    # 交易所下拉菜单触发事件

    def select_exchange(self, i):
        self.name_combo.clear()
        self.symbol_line.clear()
        current_exchange = self.exchanges[i].value
        self.filtered_names = []

        for contract in self.contracts:
            if contract.exchange.value == current_exchange:
                self.filtered_symbols.append(contract.symbol)
                self.filtered_names.append(contract.name)
        self.name_combo.addItems(self.filtered_names)

    # @Time    : 2019-09-17
    # @Author  : Wang Yongchang
    # 合约名称下拉菜单触发事件

    def select_name(self, i):
        if i < 0:
            return
        current_name = self.filtered_names[i]

        for contract in self.contracts:
            if contract.name == current_name:
                self.vt_symbol = contract.symbol
                self.symbol_line.setText(contract.symbol)

                # @Time    : 2019-09-19
                # @Author  : Wang Yongchang
                # 合约名称下拉菜单选择，发送EVENT_CURRENT_SYMBOL事件
                event = Event(EVENT_CURRENT_SYMBOL, contract)
                self.event_engine.put(event)

        # 清理五档行情
        self.clear_label_text()

    def register_event(self):
        """"""
        # @Time    : 2019-09-17
        # @Author  : Wang Yongchang
        # 注册EVENT_CONTRACT事件,使用信号槽发送到处理函数
        self.signal_contract.connect(self.set_contract)
        self.event_engine.register(EVENT_CONTRACT, self.signal_contract.emit)

        # @Time    : 2019-09-17
        # @Author  : Wang Yongchang
        # 注册EVENT_CURRENT_CONTRACT事件,使用信号槽发送到处理函数

        self.signal_current_contract.connect(self.set_current_contract)
        self.event_engine.register(EVENT_CURRENT_CONTRACT, self.signal_current_contract.emit)

        # @Time    : 2019-09-19
        # @Author  : Wang Yongchang
        # 注册EVENT_CURRENT_TRADE事件,使用信号槽发送到处理函数

        self.signal_current_position.connect(self.set_current_position_trade)
        self.event_engine.register(EVENT_CURRENT_POSITION, self.signal_current_position.emit)

        # @Time    : 2019-09-19
        # @Author  : Wang Yongchang
        # 注册EVENT_CURRENT_TRADE事件,使用信号槽发送到处理函数

        self.signal_current_trade.connect(self.set_current_position_trade)
        self.event_engine.register(EVENT_CURRENT_TRADE, self.signal_current_trade.emit)

        self.signal_tick.connect(self.process_tick_event)
        self.event_engine.register(EVENT_TICK, self.signal_tick.emit)

    # @Time    : 2019-09-17
    # @Author  : Wang Yongchang
    # 处理EVENT_CONTRACT事件

    def set_contract(self, event: Event):
        contract = event.data
        self.contracts.append(contract)

        # @Time    : 2019-10-10
        # @Author  : Wang Yongchang
        # 按照订阅合约添加交易所

        # if contract.exchange not in self.exchanges:
        #     self.exchanges.append(contract.exchange)
        # if len(self.contracts) == 540:
        #     self.init_name_combo()

    # @Time    : 2019-09-17
    # @Author  : Wang Yongchang
    # 处理EVENT_CURRENT_CONTRACT事件，设置交易所/合约编号/合约名称的联动关系

    def set_current_contract(self, event: Event):
        tick = event.data
        self.price_line.setText("")
        self.volume_line.setText("")

        for ix, exchange in enumerate(self.exchanges):
            if exchange == tick.exchange:
                self.exchange_combo.setCurrentIndex(ix)
                time.sleep(0.01)
                for idx, name in enumerate(self.filtered_names):
                    if name == tick.name:
                        self.name_combo.setCurrentIndex(idx)

    # @Time    : 2019-09-19
    # @Author  : Wang Yongchang
    # 处理EVENT_CURRENT_POSITION,TRADE事件，设置交易所/合约编号/合约名称的联动关系

    def set_current_position_trade(self, event: Event):
        current = event.data

        current_bars = self.main_engine.get_current_bars()

        if current.direction == Direction.LONG:
            self.direction_combo.setCurrentText(Direction.SHORT.value)
        else:
            self.direction_combo.setCurrentText(Direction.LONG.value)
        self.offset_combo.setCurrentText(Offset.CLOSE.value)

        self.price_line.setText("")
        self.volume_line.setText("")
        # self.name_combo.setCurrentText(current.symbol)
        self.symbol_line.setText(current.symbol)

        for ix, exchange in enumerate(self.exchanges):
            if exchange == current.exchange:
                self.exchange_combo.setCurrentIndex(ix)
                # self.exchange_combo.setCurrentText(current.exchange.value)
                # time.sleep(0.01)
                # print(self.filtered_names)
                for idx, name in enumerate(self.filtered_names):
                    if self.filtered_symbols[idx] == current.symbol:
                        self.name_combo.setCurrentIndex(idx)
                        # self.name_combo.setCurrentText(current.symbol)

    def process_tick_event(self, event: Event):
        """"""
        tick = event.data
        if tick.symbol != self.vt_symbol:
            return

        self.lp_label.setText(str(tick.last_price))
        self.bp1_label.setText(str(tick.bid_price_1))
        self.bv1_label.setText(str(tick.bid_volume_1))
        self.ap1_label.setText(str(tick.ask_price_1))
        self.av1_label.setText(str(tick.ask_volume_1))

        if tick.pre_close:
            r = (tick.last_price / tick.pre_close - 1) * 100
            self.return_label.setText(f"{r:.2f}%")

        if tick.bid_price_2:
            self.bp2_label.setText(str(tick.bid_price_2))
            self.bv2_label.setText(str(tick.bid_volume_2))
            self.ap2_label.setText(str(tick.ask_price_2))
            self.av2_label.setText(str(tick.ask_volume_2))

            self.bp3_label.setText(str(tick.bid_price_3))
            self.bv3_label.setText(str(tick.bid_volume_3))
            self.ap3_label.setText(str(tick.ask_price_3))
            self.av3_label.setText(str(tick.ask_volume_3))

            self.bp4_label.setText(str(tick.bid_price_4))
            self.bv4_label.setText(str(tick.bid_volume_4))
            self.ap4_label.setText(str(tick.ask_price_4))
            self.av4_label.setText(str(tick.ask_volume_4))

            self.bp5_label.setText(str(tick.bid_price_5))
            self.bv5_label.setText(str(tick.bid_volume_5))
            self.ap5_label.setText(str(tick.ask_price_5))
            self.av5_label.setText(str(tick.ask_volume_5))

    def set_symbol_input(self):
        """
        Set the exchange and contract name by input symbol.
        """
        symbol = str(self.symbol_line.text())

        if not symbol:
            return

        contract = self.main_engine.get_contract(symbol)
        if contract:
            for ix, exchange in enumerate(self.exchanges):
                if exchange == contract.exchange:
                    self.exchange_combo.setCurrentIndex(ix)
                    time.sleep(0.01)
                    for idx, name in enumerate(self.filtered_names):
                        if self.filtered_symbols:
                            if self.filtered_symbols[idx] == symbol:
                                self.name_combo.setCurrentIndex(idx)

        self.clear_label_text()

    def clear_label_text(self):
        """
        Clear text on all labels.
        """
        self.lp_label.setText("")
        self.return_label.setText("")

        self.bv1_label.setText("")
        self.bv2_label.setText("")
        self.bv3_label.setText("")
        self.bv4_label.setText("")
        self.bv5_label.setText("")

        self.av1_label.setText("")
        self.av2_label.setText("")
        self.av3_label.setText("")
        self.av4_label.setText("")
        self.av5_label.setText("")

        self.bp1_label.setText("")
        self.bp2_label.setText("")
        self.bp3_label.setText("")
        self.bp4_label.setText("")
        self.bp5_label.setText("")

        self.ap1_label.setText("")
        self.ap2_label.setText("")
        self.ap3_label.setText("")
        self.ap4_label.setText("")
        self.ap5_label.setText("")

    def send_order(self):
        """
        Send new order manually.
        """
        symbol = str(self.symbol_line.text())
        if not symbol:
            QtWidgets.QMessageBox.critical(self, "委托失败", "请输入合约代码")
            return

        volume_text = str(self.volume_line.text())
        if not volume_text:
            QtWidgets.QMessageBox.critical(self, "委托失败", "请输入委托数量")
            return
        volume = float(volume_text)

        price_text = str(self.price_line.text())
        if not price_text:
            price = 0
        else:
            price = float(price_text)

        req = OrderRequest(
            symbol=symbol,
            exchange=Exchange(str(self.exchange_combo.currentText())),
            direction=Direction(str(self.direction_combo.currentText())),
            type=OrderType(str(self.order_type_combo.currentText())),
            volume=volume,
            price=price,
            offset=Offset(str(self.offset_combo.currentText())),
        )

        gateway_name = str(self.gateway_combo.currentText())

        self.main_engine.send_order(req, gateway_name)

    def cancel_all(self):
        """
        Cancel all active orders.
        """
        order_list = self.main_engine.get_all_active_orders()
        for order in order_list:
            req = order.create_cancel_request()
            self.main_engine.cancel_order(req, order.gateway_name)


class ActiveOrderMonitor(OrderMonitor):
    """
    Monitor which shows active order only.
    """

    def process_event(self, event):
        """
        Hides the row if order is not active.
        """
        super(ActiveOrderMonitor, self).process_event(event)

        order = event.data
        row_cells = self.cells[order.vt_orderid]
        row = self.row(row_cells["volume"])

        if order.is_active():
            self.showRow(row)
        else:
            self.hideRow(row)


class ContractManager(QtWidgets.QWidget):
    """
    Query contract data available to trade in system.
    """

    headers = {
        "vt_symbol": "本地代码",
        "symbol": "代码",
        "exchange": "交易所",
        "name": "名称",
        "product": "合约分类",
        "size": "合约乘数",
        "pricetick": "价格跳动",
        "min_volume": "最小委托量",
        "gateway_name": "交易接口",
    }

    def __init__(self, main_engine, event_engine):
        super(ContractManager, self).__init__()

        self.main_engine = main_engine
        self.event_engine = event_engine

        self.init_ui()

    def init_ui(self):
        """"""
        self.setWindowTitle("合约查询")
        self.resize(1000, 600)

        self.filter_line = QtWidgets.QLineEdit()
        self.filter_line.setPlaceholderText("输入合约代码或者交易所，留空则查询所有合约")

        self.button_show = QtWidgets.QPushButton("查询")
        self.button_show.clicked.connect(self.show_contracts)

        labels = []
        for name, display in self.headers.items():
            label = f"{display}\n{name}"
            labels.append(label)

        self.contract_table = QtWidgets.QTableWidget()
        self.contract_table.setColumnCount(len(self.headers))
        self.contract_table.setHorizontalHeaderLabels(labels)
        self.contract_table.verticalHeader().setVisible(False)
        self.contract_table.setEditTriggers(self.contract_table.NoEditTriggers)
        self.contract_table.setAlternatingRowColors(True)

        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.filter_line)
        hbox.addWidget(self.button_show)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addWidget(self.contract_table)

        self.setLayout(vbox)

    def show_contracts(self):
        """
        Show contracts by symbol
        """
        flt = str(self.filter_line.text())

        all_contracts = self.main_engine.get_all_contracts()
        if flt:
            contracts = [
                contract for contract in all_contracts if flt in contract.vt_symbol
            ]
        else:
            contracts = all_contracts

        self.contract_table.clearContents()
        self.contract_table.setRowCount(len(contracts))

        for row, contract in enumerate(contracts):
            for column, name in enumerate(self.headers.keys()):
                value = getattr(contract, name)
                if isinstance(value, Enum):
                    cell = EnumCell(value, contract)
                else:
                    cell = BaseCell(value, contract)
                self.contract_table.setItem(row, column, cell)

        self.contract_table.resizeColumnsToContents()


class AboutDialog(QtWidgets.QDialog):
    """
    About VN Trader.
    """

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        """"""
        super(AboutDialog, self).__init__()

        self.main_engine = main_engine
        self.event_engine = event_engine

        self.init_ui()

    def init_ui(self):
        """"""
        self.setWindowTitle(f"关于VN Trader")

        text = """
            Developed by Traders, for Traders.
            License：MIT
            
            Website：www.vnpy.com
            Github：www.github.com/vnpy/vnpy

            """

        label = QtWidgets.QLabel()
        label.setText(text)
        label.setMinimumWidth(500)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(label)
        self.setLayout(vbox)


class GlobalDialog(QtWidgets.QDialog):
    """
    Start connection of a certain gateway.
    """

    def __init__(self):
        """"""
        super().__init__()

        self.widgets = {}

        self.init_ui()

    def init_ui(self):
        """"""
        self.setWindowTitle("全局配置")
        self.setMinimumWidth(800)

        settings = copy(SETTINGS)
        settings.update(load_json(SETTING_FILENAME))

        # Initialize line edits and form layout based on setting.
        form = QtWidgets.QFormLayout()

        for field_name, field_value in settings.items():
            field_type = type(field_value)
            widget = QtWidgets.QLineEdit(str(field_value))

            form.addRow(f"{field_name} <{field_type.__name__}>", widget)
            self.widgets[field_name] = (widget, field_type)

        button = QtWidgets.QPushButton("确定")
        button.clicked.connect(self.update_setting)
        form.addRow(button)

        self.setLayout(form)

    def update_setting(self):
        """
        Get setting value from line edits and update global setting file.
        """
        settings = {}
        for field_name, tp in self.widgets.items():
            widget, field_type = tp
            value_text = widget.text()

            if field_type == bool:
                if value_text == "True":
                    field_value = True
                else:
                    field_value = False
            else:
                field_value = field_type(value_text)

            settings[field_name] = field_value

        QtWidgets.QMessageBox.information(
            self,
            "注意",
            "全局配置的修改需要重启VN Trader后才会生效！",
            QtWidgets.QMessageBox.Ok
        )

        save_json(SETTING_FILENAME, settings)
        self.accept()
