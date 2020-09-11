# @Author : Wangyongchang
# @Time : 2019.09.27
from vnpy.event import EventEngine
from vnpy.trader.engine import MainEngine
from vnpy.trader.ui import QtWidgets

from .editor_box import EditorBox
from .mc_function_box import McFunctionBox
from .log_monitor_box import LogMonitorBox
from .saved_strategy_box import SavedStrategyBox

from ..engine import APP_NAME


class EditorManager(QtWidgets.QWidget):
    """"""
    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        """"""
        super().__init__()

        self.main_engine = main_engine
        self.editor_engine = main_engine.get_engine(APP_NAME)
        self.event_engine = event_engine

        # 定义对象变量
        self.editor_box = None  # 编辑器
        self.function_box = None    # 函数列表
        self.log_monitor_box = None # 日志框
        self.strategy_box = None    # 策略框

        self.init_ui()

    def init_ui(self):
        """"""
        self.setWindowTitle("函数编辑器")

        self.editor_box = EditorBox(self)
        self.function_box = McFunctionBox(self)
        hbox_1 = QtWidgets.QHBoxLayout()
        hbox_1.addLayout(self.editor_box)
        hbox_1.addLayout(self.function_box)
        # setStretch(int index, int stretch)
        # setStretch的第一个参数为索引，第二个参数为宽度
        # 第一列的宽度为3，第二列的宽度为1
        hbox_1.setStretch(0, 2)
        hbox_1.setStretch(1, 1)

        self.log_monitor_box = LogMonitorBox(self)
        self.strategy_box = SavedStrategyBox(self)
        hbox_2 = QtWidgets.QHBoxLayout()
        hbox_2.addLayout(self.log_monitor_box)
        hbox_2.addLayout(self.strategy_box)
        hbox_2.setStretch(0, 2)
        hbox_2.setStretch(1, 1)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(hbox_1)
        vbox.addLayout(hbox_2)
        self.setLayout(vbox)

    def show(self):
        """"""
        self.showMaximized()





