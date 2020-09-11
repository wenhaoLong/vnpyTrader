"""
Implements main window of VN Trader.
"""
import webbrowser
from functools import partial
from importlib import import_module
from typing import Callable

from PyQt5 import QtCore, QtGui, QtWidgets

from vnpy.event import Event, EventEngine
from ..event import EVENT_CURRENT_INTERVAL,EVENT_CLEAN, EVENT_POSITION
from ..constant import Interval

from .widget import (
    TickMonitor,
    OrderMonitor,
    TradeMonitor,
    PositionMonitor,
    AccountMonitor,
    LogMonitor,
    ActiveOrderMonitor,
    ConnectDialog,
    ContractManager,
    TradingWidget,
    AboutDialog,
    GlobalDialog
)
from vnpy.app.editor_manager.ui import EditorManager
from vnpy.app.script_trader.ui import ScriptManager
from vnpy.app.cta_backtester.ui import BacktesterManager
from vnpy.app.cta_strategy.ui import CtaManager


from .widget_k_line import KLineMonitor

from ..engine import MainEngine
from ..utility import get_icon_path, TRADER_DIR


class MainWindow(QtWidgets.QMainWindow):
    """
    Main window of VN Trader.
    """

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        """"""
        super(MainWindow, self).__init__()
        self.main_engine = main_engine
        self.event_engine = event_engine
        self.desktop = None
        self.screen_width = 0
        self.screen_height = 0
        self.window_title = f"CCLOUDSET [{TRADER_DIR}]"

        self.connect_dialogs = {}
        self.widgets = {}

        self.init_ui()

    def init_ui(self):
        """"""
        # @Time    : 2019-09-12
        # @Author  : Wang Yongchang
        self.desktop = QtWidgets.QDesktopWidget()
        self.screen_width = self.desktop.screenGeometry().width()
        self.screen_height = self.desktop.screenGeometry().height()

        self.btn_min = QtGui.QPushButton('1m')
        self.btn_5min = QtGui.QPushButton('5m')
        self.btn_15min = QtGui.QPushButton('15m')
        self.btn_hour = QtGui.QPushButton('1h')
        self.btn_day = QtGui.QPushButton('d')
        self.btn_clean = QtGui.QPushButton('清空')

        self.setWindowTitle(self.window_title)
        self.init_dock()
        self.init_toolbar()
        self.init_menu()
        self.load_window_setting("custom")

    def init_dock(self):
        """"""
        self.trading_widget, trading_dock = self.create_dock(
            TradingWidget, "交易", QtCore.Qt.LeftDockWidgetArea
        )
        tick_widget, tick_dock = self.create_dock(
            TickMonitor, "行情", QtCore.Qt.RightDockWidgetArea
        )

        bar_widget, bar_dock = self.create_k_dock(
            KLineMonitor, "K线", QtCore.Qt.RightDockWidgetArea
        )
        order_widget, order_dock = self.create_dock(
            OrderMonitor, "委托（双击撤单）", QtCore.Qt.RightDockWidgetArea
        )
        active_widget, active_dock = self.create_dock(
            ActiveOrderMonitor, "活动", QtCore.Qt.RightDockWidgetArea
        )
        trade_widget, trade_dock = self.create_dock(
            TradeMonitor, "成交", QtCore.Qt.RightDockWidgetArea
        )
        log_widget, log_dock = self.create_dock(
            LogMonitor, "日志", QtCore.Qt.LeftDockWidgetArea
        )
        account_widget, account_dock = self.create_dock(
            AccountMonitor, "资金", QtCore.Qt.BottomDockWidgetArea
        )
        position_widget, position_dock = self.create_dock(
            PositionMonitor, "持仓", QtCore.Qt.BottomDockWidgetArea
        )

        self.tabifyDockWidget(active_dock, order_dock)

        self.save_window_setting("default")

    def init_menu(self):
        """"""
        bar = self.menuBar()

        # System menu
        sys_menu = bar.addMenu("系统")

        gateway_names = self.main_engine.get_all_gateway_names()
        for name in gateway_names:
            func = partial(self.connect, name)
            self.add_menu_action(sys_menu, f"连接{name}", "connect.ico", func)

        sys_menu.addSeparator()

        self.add_menu_action(sys_menu, "退出", "exit.ico", self.close)

        # @Time    : 2019-10-08
        # @Author  : Wang Yongchang
        # 侧边栏功能APP
        # 由于使用import_module方法获得的类在pyinstaller打包成exe时后获取不到
        # 报错:类似找不到"vnpy.app.editor_manager.ui"
        # 在这里直接import所需类进来使用，例如EditorManager

        self.add_toolbar_action(
            "函数编辑",
            "editor.ico",
            partial(self.open_widget, EditorManager, "EditorEngine")
        )
        self.add_toolbar_action(
            "脚本策略",
            "script.ico",
            partial(self.open_widget, ScriptManager, "ScriptEngine")
        )
        self.add_toolbar_action(
            "CTA策略",
            "connect.ico",
            partial(self.open_widget, CtaManager, "CtaEngine")
        )
        #
        self.add_toolbar_action(
            "CTA回测",
            "backtester.ico",
            partial(self.open_widget, BacktesterManager, "BacktesterEngine")
        )
        #
        # self.add_toolbar_action(
        #     "查询合约",
        #     "contract.ico",
        #     partial(self.open_widget, ContractManager, "contract")
        # )
        #
        # self.add_toolbar_action(
        #     "社区论坛", "forum.ico", self.open_forum
        # )

        # Global setting editor
        action = QtWidgets.QAction("配置", self)
        action.triggered.connect(self.edit_global_setting)
        bar.addAction(action)

        # Help menu
        help_menu = bar.addMenu("帮助")

        self.add_menu_action(
            help_menu,
            "查询合约",
            "contract.ico",
            partial(self.open_widget, ContractManager, "contract"),
        )

        self.add_menu_action(
            help_menu, "还原窗口", "restore.ico", self.restore_window_setting
        )

        # self.add_menu_action(
        #     help_menu, "测试邮件", "email.ico", self.send_test_email
        # )

    def init_toolbar(self):
        """"""
        self.toolbar = QtWidgets.QToolBar(self)
        self.toolbar.setObjectName("工具栏")
        self.toolbar.setFloatable(False)
        self.toolbar.setMovable(False)

        # Set button size
        w = 40
        size = QtCore.QSize(w, w)
        self.toolbar.setIconSize(size)

        # Set button spacing
        self.toolbar.layout().setSpacing(10)

        self.addToolBar(QtCore.Qt.LeftToolBarArea, self.toolbar)

    def add_menu_action(
        self,
        menu: QtWidgets.QMenu,
        action_name: str,
        icon_name: str,
        func: Callable,
    ):
        """"""
        # @Time    : 2019-10-09
        # @Author  : Wang Yongchang
        # 为pyinstaller打包exe,改变静态文件查找路径方式
        icon = QtGui.QIcon(get_icon_path(icon_name))

        action = QtWidgets.QAction(action_name, self)
        action.triggered.connect(func)
        action.setIcon(icon)

        menu.addAction(action)

    def add_toolbar_action(
        self,
        action_name: str,
        icon_name: str,
        func: Callable,
    ):
        """"""
        # @Time    : 2019-10-09
        # @Author  : Wang Yongchang
        # 为pyinstaller打包exe,改变静态文件查找路径方式
        icon = QtGui.QIcon(get_icon_path(icon_name))

        action = QtWidgets.QAction(action_name, self)
        action.triggered.connect(func)
        action.setIcon(icon)

        self.toolbar.addAction(action)

    def create_dock(
        self, widget_class: QtWidgets.QWidget, name: str, area: int
    ):
        """
        Initialize a dock widget.
        """
        widget = widget_class(self.main_engine, self.event_engine)
        dock = QtWidgets.QDockWidget(name)
        dock.setWidget(widget)
        dock.setObjectName(name)
        dock.setFeatures(dock.DockWidgetFloatable | dock.DockWidgetMovable)

        # @Time    : 2019-09-12
        # @Author  : Wang Yongchang

        if name == "交易":
            dock.setFixedHeight(self.screen_height * 0.60)

        self.addDockWidget(area, dock)
        return widget, dock

    # @Time    : 2019-09-24
    # @Author  : Long WenHao
    def create_k_dock(
            self, widget_class: QtWidgets.QWidget, name: str, area: int
    ):
        widget = widget_class(self.main_engine, self.event_engine)
        w = QtGui.QWidget()


        # @Time    : 2019-09-26
        # @Author  : Long WenHao

        self.btn_day.clicked.connect(self.connect_k_line)
        self.btn_min.clicked.connect(self.connect_k_line)
        self.btn_5min.clicked.connect(self.connect_k_line)
        self.btn_15min.clicked.connect(self.connect_k_line)
        self.btn_clean.clicked.connect(self.connect_k_line)
        # self.btn_hour.clicked.connect(self.connect_k_line)

        layout = QtGui.QGridLayout()
        w.setLayout(layout)
        layout.addWidget(self.btn_min, 0, 0)  # button goes in upper-left
        layout.addWidget(self.btn_5min, 1, 0)  # button goes in upper-left
        layout.addWidget(self.btn_15min, 2, 0)  # button goes in upper-left
        layout.addWidget(self.btn_day, 3, 0)  # button goes in upper-left
        layout.addWidget(self.btn_clean, 4, 0)  # button goes in upper-left

        layout.addWidget(widget, 0, 1, 6, 1)  # plot goes on right side, spanning 3 rows
        dock = QtWidgets.QDockWidget(name)
        dock.setWidget(w)
        dock.setObjectName(name)
        dock.setBaseSize(self.screen_width * 0.5, self.screen_height * 0.5)
        dock.setFeatures(dock.DockWidgetFloatable | dock.DockWidgetMovable)
        self.addDockWidget(area, dock)
        return widget, dock

    # @Time    : 2019-09-26
    # @Author  : Long WenHao
    # 发送EVENT_CURRENT_INTERVAL事件

    def connect_k_line(self):
        sender = self.sender()

        if sender.text() == "d":
            self.btn_day.setStyleSheet("color:red")
            self.btn_5min.setStyleSheet("color:white")
            self.btn_15min.setStyleSheet("color:white")
            self.btn_min.setStyleSheet("color:white")
            self.btn_hour.setStyleSheet("color:white")
            self.btn_clean.setStyleSheet("color:white")
            event = Event(EVENT_CURRENT_INTERVAL, sender.text())
        elif sender.text() == "1h":
            self.btn_hour.setStyleSheet("color:red")
            self.btn_5min.setStyleSheet("color:white")
            self.btn_15min.setStyleSheet("color:white")
            self.btn_min.setStyleSheet("color:white")
            self.btn_day.setStyleSheet("color:white")
            self.btn_clean.setStyleSheet("color:white")
            event = Event(EVENT_CURRENT_INTERVAL, sender.text())
        elif sender.text() == "1m":
            self.btn_min.setStyleSheet("color:red")
            self.btn_5min.setStyleSheet("color:white")
            self.btn_15min.setStyleSheet("color:white")
            self.btn_hour.setStyleSheet("color:white")
            self.btn_day.setStyleSheet("color:white")
            self.btn_clean.setStyleSheet("color:white")
            event = Event(EVENT_CURRENT_INTERVAL, sender.text())
        elif sender.text() == "5m":
            self.btn_5min.setStyleSheet("color:red")
            self.btn_min.setStyleSheet("color:white")
            self.btn_15min.setStyleSheet("color:white")
            self.btn_hour.setStyleSheet("color:white")
            self.btn_day.setStyleSheet("color:white")
            self.btn_clean.setStyleSheet("color:white")
            event = Event(EVENT_CURRENT_INTERVAL, sender.text())
        elif sender.text() == "15m":
            self.btn_15min.setStyleSheet("color:red")
            self.btn_min.setStyleSheet("color:white")
            self.btn_5min.setStyleSheet("color:white")
            self.btn_hour.setStyleSheet("color:white")
            self.btn_day.setStyleSheet("color:white")
            self.btn_clean.setStyleSheet("color:white")
            event = Event(EVENT_CURRENT_INTERVAL, sender.text())
        elif sender.text() == "清空":
            self.btn_clean.setStyleSheet("color:red")
            self.btn_15min.setStyleSheet("color:white")
            self.btn_min.setStyleSheet("color:white")
            self.btn_5min.setStyleSheet("color:white")
            self.btn_hour.setStyleSheet("color:white")
            self.btn_day.setStyleSheet("color:white")
            event = Event(EVENT_CLEAN, sender.text())
        self.event_engine.put(event)

    def connect(self, gateway_name: str):
        """
        Open connect dialog for gateway connection.
        """
        dialog = self.connect_dialogs.get(gateway_name, None)
        if not dialog:
            dialog = ConnectDialog(self.main_engine, gateway_name)

        dialog.exec_()

    def closeEvent(self, event):
        """
        Call main engine close function before exit.
        """
        reply = QtWidgets.QMessageBox.question(
            self,
            "退出",
            "确认退出？",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No,
        )

        if reply == QtWidgets.QMessageBox.Yes:
            for widget in self.widgets.values():
                widget.close()
            self.save_window_setting("custom")

            self.main_engine.close()

            event.accept()
        else:
            event.ignore()

    def open_widget(self, widget_class: QtWidgets.QWidget, name: str):
        """
        Open contract manager.
        """
        widget = self.widgets.get(name, None)
        if not widget:
            widget = widget_class(self.main_engine, self.event_engine)
            self.widgets[name] = widget

        if isinstance(widget, QtWidgets.QDialog):
            widget.exec_()
        else:
            widget.show()

    def save_window_setting(self, name: str):
        """
        Save current window size and state by trader path and setting name.
        """
        settings = QtCore.QSettings(self.window_title, name)
        settings.setValue("state", self.saveState())
        settings.setValue("geometry", self.saveGeometry())

    def load_window_setting(self, name: str):
        """
        Load previous window size and state by trader path and setting name.
        """
        settings = QtCore.QSettings(self.window_title, name)
        state = settings.value("state")
        geometry = settings.value("geometry")

        if isinstance(state, QtCore.QByteArray):
            self.restoreState(state)
            self.restoreGeometry(geometry)

    def restore_window_setting(self):
        """
        Restore window to default setting.
        """
        self.load_window_setting("default")
        self.showMaximized()

    def send_test_email(self):
        """
        Sending a test email.
        """
        self.main_engine.send_email("VN Trader", "testing")

    def open_forum(self):
        """
        """
        webbrowser.open("https://www.vnpy.com/forum/")

    def edit_global_setting(self):
        """
        """
        dialog = GlobalDialog()
        dialog.exec_()
