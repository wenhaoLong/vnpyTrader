from PyQt5.QtWidgets import QDialog
from PyQt5 import QtCore, QtGui


# 参数设置框
class ParamDialog(QDialog):
    # 用来记录上一次的设置值
    init_money = 0
    commission = 0
    commission_abs = 0
    deposit = 0
    contract = ''
    period = 1

    def __init__(self, parent=None):
        QDialog.__init__(self, parent)

        # 初始化资金
        self.init_money = self.__class__.init_money
        # 当前可用资金
        self.current_money = self.init_money
        # 手续费
        self.commission = self.__class__.commission
        # 手续费(绝对值)
        self.commission_abs = self.__class__.commission_abs
        # 保证金
        self.deposit = self.__class__.deposit
        # 合约号
        self.contract = self.__class__.contract
        # k线周期 1min 3min 5min.....
        self.period = self.__class__.period

        self.init_ui()

    def init_ui(self):
        self.resize(360, 200)
        self.setWindowTitle('参数设置')

        # 表格布局
        grid = QtGui.QGridLayout()
        # 资金量
        grid.addWidget(QtGui.QLabel(u'使用资金', parent=self), 0, 0, 1, 1)
        self.money_input = QtGui.QLineEdit(parent=self)
        # 设置为上一次的初始资金量值
        self.money_input.setText(str(self.init_money))
        grid.addWidget(self.money_input, 0, 1, 1, 1)
        # 手续费
        grid.addWidget(QtGui.QLabel(u'手续费(%)', parent=self), 1, 0, 1, 1)
        self.commission_input = QtGui.QLineEdit(parent=self)
        self.commission_input.setText(str(self.commission))
        grid.addWidget(self.commission_input, 1, 1, 1, 1)
        # 手续费（绝对值）
        grid.addWidget(QtGui.QLabel(u'手续费(绝对值)', parent=self), 2, 0, 1, 1)
        self.commission_abs_input = QtGui.QLineEdit(parent=self)
        self.commission_abs_input.setText(str(self.commission_abs))
        grid.addWidget(self.commission_abs_input, 2, 1, 1, 1)
        # 保证金
        grid.addWidget(QtGui.QLabel(u'保证金(%)', parent=self), 3, 0, 1, 1)
        self.deposit_input = QtGui.QLineEdit(parent=self)
        self.deposit_input.setText(str(self.deposit))
        grid.addWidget(self.deposit_input, 3, 1, 1, 1)
        # 合约号
        grid.addWidget(QtGui.QLabel(u'合约号', parent=self), 4, 0, 1, 1)
        self.contract_input = QtGui.QLineEdit(parent=self)
        self.contract_input.setText(str(self.contract))
        grid.addWidget(self.contract_input, 4, 1, 1, 1)
        # k线周期
        grid.addWidget(QtGui.QLabel(u'K线周期', parent=self), 5, 0, 1, 1)
        self.period_input = QtGui.QLineEdit(parent=self)
        self.period_input.setText(str(self.period))
        grid.addWidget(self.period_input, 5, 1, 1, 1)

        # 创建ButtonBox，用户确定和取消
        buttonBox = QtGui.QDialogButtonBox(parent=self)
        buttonBox.setOrientation(QtCore.Qt.Horizontal)  # 设置为水平方向
        buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel | QtGui.QDialogButtonBox.Ok)  # 确定和取消两个按钮
        # 连接信号和槽
        buttonBox.accepted.connect(self.accept)  # 确定
        buttonBox.rejected.connect(self.reject)  # 取消

        # 垂直布局，布局表格及按钮
        layout = QtGui.QVBoxLayout()

        # 加入前面创建的表格布局
        layout.addLayout(grid)

        # 放一个间隔对象美化布局
        spacerItem = QtGui.QSpacerItem(20, 48, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        layout.addItem(spacerItem)

        # ButtonBox
        layout.addWidget(buttonBox)

        self.setLayout(layout)

    def __getstate__(self):
        return self.__class__.init_money, self.__class__.commission, self.__class__.commission_abs,\
               self.__class__.deposit, self.__class__.contract, self.__class__.period

    def __setstate__(self, state):
        init_money, commission, commission_abs, deposit, contract, period = state

        self.init_money = self.current_money = self.__class__.init_money = init_money
        self.commission = self.__class__.commission = commission
        self.commission_abs = self.__class__.commission_abs = commission_abs
        self.deposit = self.__class__.deposit = deposit
        self.contract = self.__class__.contract = contract
        self.period = self.__class__.period = period
