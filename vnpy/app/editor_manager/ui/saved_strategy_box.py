# @Author : Wangyongchang
# @Time : 2019.11.14

import os
from pathlib import Path
from vnpy.trader.ui import QtWidgets, QtCore, QtGui
from vnpy.trader.utility import get_folder_path, pop_message_box
from vnpy.event import EventEngine, Event
from vnpy.trader.event import EVENT_SAVED_STRATEGY



class SavedStrategyBox(QtWidgets.QVBoxLayout):
    signal_saved_strategy = QtCore.pyqtSignal(Event)

    def __init__(self, editor_manager):
        super().__init__()
        self.editor_manager = editor_manager
        self.event_engine = editor_manager.event_engine
        self.script_folder = Path(get_folder_path("script"))
        self.strategy_list_view = None
        self.strategy_list_model = None
        self.script_textarea = None
        self.saved_strategy_list = []

        # 当前策略文件名
        self.current_strategy_name = None

        self.register_event()
        self.init_ui()

    def init_ui(self):
        # 实例化列表视图
        title = QtWidgets.QTextEdit()
        title.setPlainText("已存策略")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setReadOnly(True)
        title_box = QtWidgets.QVBoxLayout()
        title_box.addWidget(title)

        self.strategy_list_view = ListView()
        # 实例化列表模型，添加数据
        self.strategy_list_model = QtCore.QStringListModel()
        # item 单击事件
        self.strategy_list_view.clicked.connect(self.set_script_textarea)
        # item 双击事件
        self.strategy_list_view.doubleClicked.connect(self.double_clicked_event)
        # 取消双击触发器
        self.strategy_list_view.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        # 连接删除动作
        self.strategy_list_view.connect_delete_action(self.delete_action)
        # 连接重命名动作
        self.strategy_list_view.connect_rename_action(self.rename_action)

        # 初始化策略列表
        self.update_list()

        # 设置列表和内容窗口
        file_content = QtWidgets.QHBoxLayout()
        file_list_box = QtWidgets.QHBoxLayout()
        file_list_box.addWidget(self.strategy_list_view)
        self.script_textarea = QtWidgets.QTextEdit()
        self.script_textarea.setReadOnly(True)

        # 设置启动的初始值
        script_content = self.get_script_content(0)
        self.script_textarea.setPlainText(script_content)

        detail_box = QtWidgets.QHBoxLayout()
        detail_box.addWidget(self.script_textarea)

        file_content.addLayout(file_list_box)
        file_content.addLayout(detail_box)
        file_content.setStretch(0, 2)
        file_content.setStretch(1, 5)

        self.addLayout(title_box)
        self.addLayout(file_content)
        self.setStretch(0, 1)
        self.setStretch(1, 19)

    def register_event(self):
        """"""
        self.signal_saved_strategy.connect(self.process_saved_strategy_event)
        self.event_engine.register(EVENT_SAVED_STRATEGY, self.signal_saved_strategy.emit)


    # 更新策略列表
    def update_list(self):
        # 得到保存策略
        self.get_saved_strategy()
        # 设置模型列表视图，加载数据列表
        self.strategy_list_model.setStringList(self.saved_strategy_list)
        # 设置列表视图的模型
        self.strategy_list_view.setModel(self.strategy_list_model)

    def process_saved_strategy_event(self, event: Event):
        """"""
        strategy = event.data
        # 刷新保存的策略列表
        self.saved_strategy_list.insert(0, strategy)
        self.strategy_list_model.setStringList(self.saved_strategy_list)
        # 设置列表视图的模型
        self.strategy_list_view.setModel(self.strategy_list_model)

    def set_script_textarea(self, QModelIndex):
        detail_text = self.get_script_content(QModelIndex.row())
        self.script_textarea.setPlainText(detail_text)

    def get_script_content(self, index):
        if self.saved_strategy_list:
            # 得到选定的文件名
            filename = self.saved_strategy_list[index]
            # 得到选定文件名的绝对路径
            path = self.script_folder.joinpath(filename)
            # 如果文件不存在,返回空
            if not os.path.exists(path):
                return ""
            with open(path, 'r', encoding='UTF-8') as file:
                return file.read()
        else:
            return ""

    def get_saved_strategy(self):
        # 清空策略列表
        self.saved_strategy_list = []
        files = os.listdir(self.script_folder)
        # 按时间排序
        files = sorted(files, key=lambda x: os.path.getmtime(os.path.join(self.script_folder, x)))
        for file_name in files:
            if file_name.endswith(".myscript"):
                # 将策略文件名添加到列表中
                self.saved_strategy_list.append(file_name)
        self.saved_strategy_list = list(reversed(self.saved_strategy_list))

    def double_clicked_event(self, QModelIndex):
        index = QModelIndex.row()
        # 记录当前选定的策略名
        self.current_strategy_name = self.saved_strategy_list[index]
        # 修改显示的策略名称
        self.editor_manager.editor_box.current_strategy_name.setPlainText("策略名称：" + self.current_strategy_name)
        # 修改编辑器中的内容
        self.editor_manager.editor_box.editor_textarea.setText(self.get_script_content(index))
        # 将焦点移回编辑器中
        # self.editor_manager.editor_box.editor_textarea.setFocus()
        self.strategy_list_view.setFocus()

    def delete_action(self):
        index = self.strategy_list_view.currentIndex().row()
        filename = self.script_folder.joinpath( self.saved_strategy_list[index])
        os.remove(filename)
        # 更新列表
        self.update_list()
        self.current_strategy_name = ""
        # 修改显示的策略名称
        self.editor_manager.editor_box.current_strategy_name.setPlainText("策略名称：未保存策略")
        # 修改编辑器中的内容
        self.editor_manager.editor_box.editor_textarea.setPlainText("")

    def rename_action(self):
        index = self.strategy_list_view.currentIndex().row()
        text, ok = QtWidgets.QInputDialog.getText(self.editor_manager, '策略重命名', '输入策略名称:')
        if ok:
            if os.path.exists(self.script_folder.joinpath(text).joinpath(".myscript")):
                pop_message_box("该文件名已存在")
                return
            self.current_strategy_name = text + ".myscript"
            os.rename(self.script_folder.joinpath(self.saved_strategy_list[index]), self.script_folder.joinpath(self.current_strategy_name))
            # 更新列表
            self.update_list()
            # 修改显示的策略名称
            self.editor_manager.editor_box.current_strategy_name.setPlainText("策略名称：" + self.current_strategy_name)
            # 修改编辑器中的内容
            self.editor_manager.editor_box.editor_textarea.setPlainText(self.get_script_content(index))


# 自定义的QListView类,主要为了实现右键菜单功能
class ListView(QtWidgets.QListView):
    def __init__(self):
        super().__init__()
        # 定义菜单
        self.menu = QtWidgets.QMenu(self)
        # 删除操作
        self.delete_item = QtWidgets.QAction("删除", self.menu)
        self.menu.addAction(self.delete_item)
        # 重命名操作
        self.rename_item = QtWidgets.QAction("重命名", self.menu)
        self.menu.addAction(self.rename_item)

    def contextMenuEvent(self, event):
        hitIndex = self.indexAt(event.pos()).column()
        if hitIndex > -1:
            self.menu.popup(self.mapToGlobal(event.pos()))


    def connect_delete_action(self, action):
        self.delete_item.triggered.connect(action)

    def connect_rename_action(self, action):
        self.rename_item.triggered.connect(action)
