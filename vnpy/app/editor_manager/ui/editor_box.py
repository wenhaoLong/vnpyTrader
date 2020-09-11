# @Author : Wangyongchang
# @Time : 2019.11.14

import os
import time
from datetime import datetime
import pickle
from pathlib import Path
from vnpy.event import EventEngine, Event
from vnpy.trader.ui import QtWidgets, QtCore
from vnpy.trader.utility import get_folder_path, pop_message_box
from vnpy.trader.event import EVENT_SAVED_STRATEGY

from .param_dialog import ParamDialog

from .script_template import script_template
from .highlighter import PythonHighlighter

from McLanguage.Transfer import Transfer
import McLanguage.myparse as myparse
from McLanguage.error import BaseError
from McLanguage import glo_var
from McLanguage.ScriptThread import ScriptThread
from MyLang.myinterpreter import interprete, execute, RunEnvironment

# 点击停止后清除k线绘图
from vnpy.trader.event import EVENT_CLEAN

from vnpy.app.editor_manager.ui.editor import CodeEditor, MyLangEditor


class EditorBox(QtWidgets.QVBoxLayout):
    """"""

    def __init__(self, editor_manager):
        """"""
        super().__init__()
        self.editor_manager = editor_manager
        self.editor_engine = editor_manager.editor_engine

        # 将自身的引用赋值到引擎中
        self.editor_engine.editor_box = self

        self.event_engine = editor_manager.event_engine

        self.editor_textarea = None
        self.current_strategy_name = ""
        self.highlighter = None

        self.script_folder = Path(get_folder_path("script"))
        self.script_template = script_template
        self.script_text = script_template
        self.insert_keyword = "# 麦语言脚本插入位置"
        self.insert_position = 0

        self.current_python_file = ""
        self.current_txt_file = ""
        self.new_txt_file = ""
        self.mc_code = ""

        self.param_dialog = None

        # 脚本线程
        self.script_thread = None

        self.init_ui()
        # self.event_engine.register(EVENT_REQ_COMISSION,self.process_deposit)

    def init_ui(self):
        # 编辑器的多行文本框
        # self.editor_textarea = QtWidgets.QTextEdit()
        self.editor_textarea = MyLangEditor()
        # self.editor_textarea = CodeEditor()
        # 设置editor背景颜色
        # self.editor_textarea.setStyleSheet("background:white")
        self.editor_textarea.textChanged.connect(self.handle_text_changed)
        # self.highlighter = PythonHighlighter(self.editor_textarea.document())
        editor_textarea_box = QtWidgets.QVBoxLayout()
        editor_textarea_box.addWidget(self.editor_textarea)

        save_button = QtWidgets.QPushButton("保存")
        save_button.clicked.connect(self.save_script)
        save_as_button = QtWidgets.QPushButton("另存为")
        save_as_button.clicked.connect(self.save_script_as)
        interprete_button = QtWidgets.QPushButton("编译")
        interprete_button.clicked.connect(self.interprete)
        start_button = QtWidgets.QPushButton("启动")
        start_button.clicked.connect(self.start_script)
        stop_button = QtWidgets.QPushButton("停止")
        stop_button.clicked.connect(self.stop_script)
        clear_button = QtWidgets.QPushButton("清空编辑器")
        clear_button.clicked.connect(self.editor_textarea.clear)

        button_box = QtWidgets.QHBoxLayout()
        button_box.addWidget(save_button)
        button_box.addWidget(save_as_button)
        button_box.addWidget(interprete_button)
        button_box.addWidget(start_button)
        button_box.addWidget(stop_button)
        button_box.addStretch()
        button_box.addWidget(clear_button)

        strategy_name_box = QtWidgets.QHBoxLayout()
        self.current_strategy_name = QtWidgets.QTextEdit()
        self.current_strategy_name.setReadOnly(True)
        self.current_strategy_name.setPlainText("策略名称：未保存策略")
        strategy_name_box.addWidget(self.current_strategy_name)

        self.addLayout(button_box)
        self.addLayout(strategy_name_box)
        self.addLayout(editor_textarea_box)
        self.setStretch(0, 1)
        self.setStretch(1, 1)
        self.setStretch(2, 18)

    def handle_text_changed(self):
        self.mc_code = self.editor_textarea.text()
        self.mc_code = self.mc_code.replace("（", "(")
        self.mc_code = self.mc_code.replace("）", ")")
        self.mc_code = self.mc_code.replace("，", ",")
        self.mc_code = self.mc_code.replace("：", ":")
        self.mc_code = self.mc_code.replace("；", ";")
        self.mc_code = self.mc_code.replace("。", ".")
        self.mc_code = self.mc_code.replace("》", ">")
        self.mc_code = self.mc_code.replace("《", "<")

    # 保存
    def save_script(self):
        current_strategy_name = self.editor_manager.strategy_box.current_strategy_name
        if current_strategy_name:
            path = self.script_folder.joinpath(current_strategy_name)
            with open(path, 'w', encoding='UTF-8') as file:
                file.write(self.mc_code)
            # 刷新列表
            self.editor_manager.strategy_box.update_list()
        else:
            self.save_script_as()

    # 另存为
    def save_script_as(self):
        value, ok = QtWidgets.QInputDialog.getText(self.editor_manager, "保存策略", "请输入策略名称:", QtWidgets.QLineEdit.Normal,
                                                   "")
        if ok:
            if not value:
                message = "\n请输入策略名称！"
                pop_message_box(message)
                return

            self.new_txt_file = value + ".myscript"
            new_txt_path = self.script_folder.joinpath(self.new_txt_file)
            if os.path.exists(new_txt_path):
                message = "\n文件名重复，策略“" + value + "”已经存在！"
                pop_message_box(message)
                self.new_txt_file = ""
                return
            with open(new_txt_path, 'w', encoding='UTF-8') as file:
                file.write(self.mc_code)
            # 更新策略标题名称
            self.current_strategy_name.setPlainText("策略名称：" + self.new_txt_file)
            # 更新当前选定策略名
            self.editor_manager.strategy_box.current_strategy_name = self.new_txt_file
            # 刷新右侧策略列表
            # event = Event(EVENT_SAVED_STRATEGY, value)
            # self.event_engine.put(event)
            self.editor_manager.strategy_box.update_list()

    def start_script(self):
        """"""
        if not self.mc_code:
            self.editor_engine.write_log("策略内容为空！", show_line=False)
            return

        # 检查配置文件夹是否存在，如果不存在则创建
        if not os.path.exists('.\\config'):
            os.mkdir('.\\config')

        # 引入参数设置框
        # 如果没有存储的参数框，则初始化一个新的
        if not os.path.exists('.\\config\\param_dialog.pkl'):
            self.param_dialog = ParamDialog(parent=self.editor_manager)
        # 如果有存储的参数筐，则加载
        else:
            with open('.\\config\\param_dialog.pkl', 'rb') as f:
                try:
                    self.param_dialog = pickle.load(f)
                    self.param_dialog.__init__(parent=self.editor_manager)
                except Exception:
                    self.param_dialog = ParamDialog(parent=self.editor_manager)

        # 如果参数框没有确认，则直接返回，不启动策略
        if not self.param_dialog.exec_():
            return

        # 判断各变量参数格式是否正确
        # 判断合约号
        if not self.param_dialog.contract_input.text() or len(self.param_dialog.contract_input.text()) == 0:
            self.editor_engine.write_log("错误：合约号不能为空", show_line=False)
            return

        # 设置全局参数
        try:
            # 资金量
            self.param_dialog.init_money = self.param_dialog.current_money = float(self.param_dialog.money_input.text())
            # 手续费
            self.param_dialog.commission = float(self.param_dialog.commission_input.text()) / 100.0
            # 手续费（绝对值）
            self.param_dialog.commission_abs = float(self.param_dialog.commission_abs_input.text())
            # 保证金率
            self.param_dialog.deposit = float(self.param_dialog.deposit_input.text()) / 100.0
            # 合约号
            self.param_dialog.contract = str(self.param_dialog.contract_input.text())
            # 周期
            self.param_dialog.period = int(self.param_dialog.period_input.text())
        except Exception as e:
            self.editor_engine.write_log("参数设置出错，请检查数据格式！错误原因如下:", show_line=False)
            self.editor_engine.write_log(str(e), show_line=False)
            return

        # 保存参数
        ParamDialog.init_money = float(self.param_dialog.money_input.text())
        ParamDialog.commission = float(self.param_dialog.commission_input.text())
        ParamDialog.commission_abs = float(self.param_dialog.commission_abs_input.text())
        ParamDialog.deposit = float(self.param_dialog.deposit_input.text())
        ParamDialog.contract = str(self.param_dialog.contract_input.text())
        ParamDialog.period = int(self.param_dialog.period_input.text())

        # 存储参数框
        with open('.\\config\\param_dialog.pkl', 'wb') as f:
            pickle.dump(self.param_dialog, f)

        # 将当前的合约号换成用户设置合约号
        self.editor_engine.current_contract = self.editor_engine.main_engine.get_contract(self.param_dialog.contract)
        # 将合约通过事件引擎推送
        event = Event("eCurrentContract.", self.editor_engine.current_contract, 20)
        self.event_engine.put(event)
        if self.editor_engine.current_contract is None:
            self.editor_engine.write_log("设置合约错误：输入的合约不存在，请检查配置及网络!", show_line=False)
            return

        self.editor_textarea.setText(self.mc_code)

        ''' 注释掉旧版的语法检查器以及转换器
        try:
            if self.new_txt_file:
                new_txt_path = self.script_folder.joinpath(self.new_txt_file)
                with open(new_txt_path, 'w', encoding='UTF-8') as file:
                    file.write(self.mc_code)
            else:
                current_txt_path = self.script_folder.joinpath(self.current_txt_file)
                with open(current_txt_path, 'w', encoding='UTF-8') as file:
                    file.write(self.mc_code)

        except Exception as e:
            self.editor_engine.write_log(str(e))
        finally:
            pass
            # file.close()

        
        # 接入语法检查
        try:
            p = myparse.parse(text=self.mc_code)
            print('parse: {}'.format(p))
        except BaseError as e:
            if e.error_msg == 'Synatax error at Eof':
                e.lexpos = len(self.mc_code) - 1
                e.lineno = 1
                e.lineno += self.mc_code.count('\n')
                e.lineno += self.mc_code.count('\r\n')
                e.value = self.mc_code[e.lexpos]
                e.error_msg = '{}: Error occurred near {!r} at line {}'.format(
                    e.__class__, e.value, e.lineno)
            self.editor_engine.write_log(e.error_msg)
            # self.editor_engine.write_log('错误位置: {}'.format(e.lexpos))
            # self.editor_engine.write_log('错误行数: {}'.format(e.lineno))
            # self.editor_engine.write_log('错误值: {}'.format(e.value))
            return

        # 得到python代码
        # @Time    : 2019-09-30
        # @Author  : Wang Yongchang
        # try ... except...捕捉异常，在LOG界面显示
        try:
            # 转换为python代码
            glo_var._init()  # 重置一些全局变量
            python_code = Transfer(text=self.mc_code).python()
            print(python_code)
            func_list = python_code.split("\n")
            indent_code = ""
            for ix, func in enumerate(func_list):
                indent_code += "\n"+16*" " + func

            try:
                second = datetime.now().strftime('%Y%m%d_%H%M%S')
                self.current_python_file = "ScriptThread_" + second + ".py"
                current_python_path = self.script_folder.joinpath(self.current_python_file)
                if not os.path.exists(current_python_path):
                    open(str(current_python_path), 'w')

                with open(current_python_path, 'w',  encoding='UTF-8') as file:
                    if self.insert_position != -1:
                        class_name = self.current_python_file.replace(".py", "")
                        self.script_text = self.script_template.replace("ScriptThread", class_name)
                        self.insert_position = self.script_text.find(self.insert_keyword)
                        content = self.script_text
                        position = self.insert_position
                        keyword = self.insert_keyword
                        # 接入实时行情的测试
                        # content = content[:position + len(keyword)] + indent_code
                        # 没有接入实时行情的测试
                        content = content[:position + len(keyword)] + indent_code + "\n"+16*" " + "time.sleep(5)"
                        file.write(content)
                        file.flush()
                        file.close()
                        # 执行脚本
                        self.editor_engine.start_strategy(str(current_python_path))

            except Exception as e:
                self.editor_engine.write_log(str(e))
            finally:
                pass

        except Exception as e:
            self.editor_engine.write_log("转换python代码出错，请检查麦语言代码")
            self.editor_engine.write_log(str(e))
            return
        '''
        current_bars = self.editor_engine.main_engine.get_current_bars()

        # @author hengxincheung
        # @time 2019-12-17
        # @note 接入麦语言解释器
        try:
            # 目前仅允许同一时刻运行一个策略脚本
            # 如果此时有脚本正在运行，则关闭并启动当前的新策略脚本
            if ScriptThread.script_running:
                self.stop_script()

            self.editor_engine.running_bar = current_bars[-1]
            # 启动新的策略
            self.editor_engine.write_log("正在启动策略......", show_line=False)
            self.script_thread = ScriptThread(self.editor_engine, self.mc_code)
            self.script_thread.start()

        except Exception as e:  # 日志框记录错误原因并退出
            self.editor_engine.write_log(str(e), show_line=False)
            return

    def stop_script(self):
        """"""

        self.editor_engine.stop_draw()
        # 关闭正在运行的策略
        if ScriptThread.script_running and self.script_thread:

            self.editor_engine.write_log("正在停止运行......", show_line=False)
            # 停止定时器自动更新running_bar
            self.editor_engine.lock_getNew()
            # 调用停止方法
            self.script_thread.stop()
            # 等待关闭,最多循环100次即10s
            for i in range(100):
                if not ScriptThread.script_running:
                    break
                time.sleep(0.1)
            if not ScriptThread.script_running:
                self.editor_engine.write_log("停止策略成功!", show_line=False)
            else:
                self.editor_engine.write_log("停止策略失败，建议关闭整个系统!", show_line=False)
        else:
            self.editor_engine.write_log("当前无运行的策略脚本", show_line=False)
        self.param_dialog = None
        self.script_thread = None

        event = Event(EVENT_CLEAN, "清空")
        self.event_engine.put(event)

    def interprete(self):
        try:
            interprete(self.editor_engine, self.mc_code)
            # 打印变量表
            # for key in RunEnvironment.run_vars.keys():
            #     self.editor_engine.write_log("{}:{}".format(key, str(RunEnvironment.run_vars[key])))
        except Exception as e:
            self.editor_engine.write_log(str(e), show_line=False)
            return
        self.editor_engine.write_log("编译成功!", show_line=False)
