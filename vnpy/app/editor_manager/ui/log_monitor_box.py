# @Author : Wangyongchang
# @Time : 2019.11.14

from vnpy.trader.ui import QtWidgets, QtCore
from vnpy.event import Event
from ..engine import EVENT_EDITOR_LOG


class LogMonitorBox(QtWidgets.QVBoxLayout):
    signal_log = QtCore.pyqtSignal(Event)

    def __init__(self, editor_manager):
        super().__init__()
        self.event_engine = editor_manager.event_engine
        self.log_monitor = None

        self.register_event()
        self.init_ui()

    def init_ui(self):

        self.log_monitor = QtWidgets.QTextEdit()
        self.log_monitor.setReadOnly(True)
        clear_button = QtWidgets.QPushButton("清空日志")
        clear_button.clicked.connect(self.log_monitor.clear)

        self.addWidget(self.log_monitor)
        self.addWidget(clear_button)

    def register_event(self):
        """"""
        self.signal_log.connect(self.process_log_event)
        self.event_engine.register(EVENT_EDITOR_LOG, self.signal_log.emit)

    def process_log_event(self, event: Event):
        """"""
        log = event.data
        msg = f"{log.time}\t{log.msg}"
        self.log_monitor.append(msg)