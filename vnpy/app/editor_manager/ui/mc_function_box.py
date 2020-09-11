# @Author : Wangyongchang
# @Time : 2019.11.14

import sys
from pathlib import Path
from vnpy.trader.ui import QtWidgets, QtCore
from vnpy.trader.utility import FunctionLoader


class McFunctionBox(QtWidgets.QVBoxLayout):
    def __init__(self, editor_manager):
        super().__init__()

        self.editor_manager = editor_manager
        self.function_dict = []
        self.function_names = []
        self.function_textarea = None
        self.init_ui()

    def init_ui(self):
        # 函数加载器
        loader = FunctionLoader()
        # 得到并拼凑 function.xlsx 文件路径
        running_path = Path(sys.argv[0]).parent
        function_file = running_path.joinpath("function.xlsx")
        # 加载函数描述文件
        loader.load_excel(function_file)
        # 得到实际内容
        self.function_dict = loader.contents
        self.function_names = loader.names

        # 实例化列表视图
        # 头部标题
        title = QtWidgets.QTextEdit()
        title.setPlainText("函数列表")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setReadOnly(True)
        title_box = QtWidgets.QVBoxLayout()
        title_box.addWidget(title)

        # 初始化列表视图
        list_view = QtWidgets.QListView()
        # 修改双击触发器为空
        list_view.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        # 实例化列表模型，添加数据
        list_model = QtCore.QStringListModel()
        # 设置模型列表视图，加载数据列表
        list_model.setStringList(self.function_names)
        # 设置列表视图的模型
        list_view.setModel(list_model)
        # 连接鼠标单击信号到 set_function_textarea 函数
        list_view.clicked.connect(self.set_function_textarea)
        # 连接鼠标双击信号到具体事件
        list_view.doubleClicked.connect(self.doubleClickedEvent)

        # 设置函数列表和函数内容窗口
        func_content = QtWidgets.QHBoxLayout()
        func_list_box = QtWidgets.QHBoxLayout()
        func_list_box.addWidget(list_view)
        self.function_textarea = QtWidgets.QTextEdit()
        self.function_textarea.setReadOnly(True)

        # 设置启动的初始值
        detail_text = self.get_function_detail(0)
        self.function_textarea.setPlainText(detail_text)

        detail_box = QtWidgets.QHBoxLayout()
        detail_box.addWidget(self.function_textarea)
        func_content.addLayout(func_list_box)
        func_content.addLayout(detail_box)
        func_content.setStretch(0, 2)
        func_content.setStretch(1, 5)

        self.addLayout(title_box)
        self.addLayout(func_content)
        self.setStretch(0, 1)
        self.setStretch(1, 19)

    def set_function_textarea(self, QModelIndex):
        detail_text = self.get_function_detail(QModelIndex.row())
        self.function_textarea.setPlainText(detail_text)

    def get_function_detail(self, index):
        function_name = self.function_names[index]
        function = self.function_dict[function_name]

        if function["status"] is not None:
            status = function["status"]
        else:
            status = ""

        if function["description"] is not None:
            description = function["description"]
        else:
            description = ""

        if function["note"] is not None:
            note = function["note"]
        else:
            note = ""

        if function["example"] is not None:
            example = function["example"]
        else:
            example = ""

        if function["condition"] is not None:
            condition = "可用条件：\n" + function["condition"] + "\n\n"
        else:
            condition = ""

        detail = function_name + "\n\n" + "开发状态：\n" + status + "\n\n" + "描述：\n" + description + "\n\n" + "解释：\n" + note + "\n\n" + condition + "例子：\n" + example
        return detail

    def doubleClickedEvent(self, QModelIndex):
        # 得到选中的函数名
        function_name = self.function_names[QModelIndex.row()]
        # 添加到编辑器中,采用在光标处插入函数名
        self.editor_manager.editor_box.editor_textarea.insert(function_name)
        # 移动光标
        self.editor_manager.editor_box.editor_textarea.setCursorPosition(
            len(self.editor_manager.editor_box.mc_code), len(self.editor_manager.editor_box.mc_code)+1)
        # 将焦点移回编辑器中
        self.editor_manager.editor_box.editor_textarea.setFocus()