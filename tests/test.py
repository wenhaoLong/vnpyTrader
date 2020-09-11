import sys

from PyQt5 import QtCore
from PyQt5.QtWidgets import *

# 参数设置框
class ParamDialog(QDialog):
    # 报告生成时间
    time = 0
    # 资金分配量
    money_allocation = 0
    # 交易合约
    contract = ""
    # 周期
    period = 1
    # 单位
    unit = 0
    # 保证金
    commission = 0
    # 手续费
    deposit = 0
    # 模型名称
    model_name = ""
    # 参数
    parameter = ""
    # 测试天数
    test_day = 0
    # 周期数
    period_num = 0
    # 信号个数
    signal_num = 0
    # 最终权益
    final_balance = 0
    # 盈利率
    profitability = 0
    # 月化收益
    month_income = 0
    # 年化收益
    year_income = 0
    # 净利润
    net_profit = 0
    # 最大盈利
    max_profit = 0
    # 最大亏损
    max_loss = 0



    def __init__(self, parent=None):
        QDialog.__init__(self, parent)

        # 初始化资金
        self.time = self.__class__.time
            # 当前可用资金
        self.money_allocation  = self.money_allocation
        # 手续费
        self.contract  = self.__class__.contract
        # 手续费(绝对值)
        self.period  = self.__class__.period
        # 保证金
        self.unit  = self.__class__.unit
        # 合约号
        self.commission  = self.__class__.commission
        # k线周期 1min 3min 5min.....
        self.deposit = self.__class__.deposit
        self.model_name = self.__class__.model_name

        self.parameter  = self.__class__.parameter
        self.test_day  = self.__class__.test_day
        self.period_num   = self.__class__.period_num
        self.signal_num   = self.__class__.signal_num
        self.final_balance    = self.__class__.final_balance
        self.profitability     = self.__class__.profitability

        self.init_ui()

    def init_ui(self):
        self.resize(360, 1200)
        self.setWindowTitle("参数设置")

        # 表格布局
        grid = QGridLayout()
        # 资金量
        grid.addWidget(QLabel(u"使用资金", parent=self), 0, 0, 1, 1)
        self.money_input = QLineEdit(parent=self)
        # 设置为上一次的初始资金量值
        self.money_input.setText(str(self.time))
        grid.addWidget(self.money_input, 0, 1, 1, 1)
        # 手续费
        grid.addWidget(QLabel(u"手续费(%)", parent=self), 1, 0, 1, 1)
        self.commission_input = QLineEdit(parent=self)
        self.commission_input.setText(str(self.commission))
        grid.addWidget(self.commission_input, 1, 1, 1, 1)

        grid.addWidget(QLabel(u"手续费(%)", parent=self), 2, 0, 1, 1)
        self.commission_input = QLineEdit(parent=self)
        self.commission_input.setText(str(self.commission))
        grid.addWidget(self.commission_input, 2, 1, 1, 1)

        grid.addWidget(QLabel(u"手续费(%)", parent=self), 3, 0, 1, 1)
        self.commission_input = QLineEdit(parent=self)
        self.commission_input.setText(str(self.commission))
        grid.addWidget(self.commission_input, 3, 1, 1, 1)

        grid.addWidget(QLabel(u"手续费(%)", parent=self), 4, 0, 1, 1)
        self.commission_input = QLineEdit(parent=self)
        self.commission_input.setText(str(self.commission))
        grid.addWidget(self.commission_input, 4, 1, 1, 1)

        grid.addWidget(QLabel(u"手续费(%)", parent=self), 5, 0, 1, 1)
        self.commission_input = QLineEdit(parent=self)
        self.commission_input.setText(str(self.commission))
        grid.addWidget(self.commission_input, 5, 1, 1, 1)

        grid.addWidget(QLabel(u"手续费(%)", parent=self), 6, 0, 1, 1)
        self.commission_input = QLineEdit(parent=self)
        self.commission_input.setText(str(self.commission))
        grid.addWidget(self.commission_input, 6, 1, 1, 1)

        grid.addWidget(QLabel(u"手续费(%)", parent=self), 7, 0, 1, 1)
        self.commission_input = QLineEdit(parent=self)
        self.commission_input.setText(str(self.commission))
        grid.addWidget(self.commission_input, 7, 1, 1, 1)

        grid.addWidget(QLabel(u"手续费(%)", parent=self), 8, 0, 1, 1)
        self.commission_input = QLineEdit(parent=self)
        self.commission_input.setText(str(self.commission))
        grid.addWidget(self.commission_input, 8, 1, 1, 1)

        grid.addWidget(QLabel(u"手续费(%)", parent=self), 9, 0, 1, 1)
        self.commission_input = QLineEdit(parent=self)
        self.commission_input.setText(str(self.commission))
        grid.addWidget(self.commission_input, 9, 1, 1, 1)

        grid.addWidget(QLabel(u"手续费(%)", parent=self), 10, 0, 1, 1)
        self.commission_input = QLineEdit(parent=self)
        self.commission_input.setText(str(self.commission))
        grid.addWidget(self.commission_input, 10, 1, 1, 1)

        grid.addWidget(QLabel(u"手续费(%)", parent=self), 11, 0, 1, 1)
        self.commission_input = QLineEdit(parent=self)
        self.commission_input.setText(str(self.commission))
        grid.addWidget(self.commission_input, 11, 1, 1, 1)

        grid.addWidget(QLabel(u"手续费(%)", parent=self), 12, 0, 1, 1)
        self.commission_input = QLineEdit(parent=self)
        self.commission_input.setText(str(self.commission))
        grid.addWidget(self.commission_input, 12, 1, 1, 1)

        grid.addWidget(QLabel(u"手续费(%)", parent=self), 13, 0, 1, 1)
        self.commission_input = QLineEdit(parent=self)
        self.commission_input.setText(str(self.commission))
        grid.addWidget(self.commission_input, 13, 1, 1, 1)

        grid.addWidget(QLabel(u"手续费(%)", parent=self), 14, 0, 1, 1)
        self.commission_input = QLineEdit(parent=self)
        self.commission_input.setText(str(self.commission))
        grid.addWidget(self.commission_input, 14, 1, 1, 1)

        grid.addWidget(QLabel(u"手续费(%)", parent=self), 15, 0, 1, 1)
        self.commission_input = QLineEdit(parent=self)
        self.commission_input.setText(str(self.commission))
        grid.addWidget(self.commission_input, 15, 1, 1, 1)

        grid.addWidget(QLabel(u"手续费(%)", parent=self), 16, 0, 1, 1)
        self.commission_input = QLineEdit(parent=self)
        self.commission_input.setText(str(self.commission))
        grid.addWidget(self.commission_input, 16, 1, 1, 1)

        grid.addWidget(QLabel(u"手续费(%)", parent=self), 17, 0, 1, 1)
        self.commission_input = QLineEdit(parent=self)
        self.commission_input.setText(str(self.commission))
        grid.addWidget(self.commission_input, 17, 1, 1, 1)

        grid.addWidget(QLabel(u"手续费(%)", parent=self), 18, 0, 1, 1)
        self.commission_input = QLineEdit(parent=self)
        self.commission_input.setText(str(self.commission))
        grid.addWidget(self.commission_input, 18, 1, 1, 1)

        grid.addWidget(QLabel(u"手续费(%)", parent=self), 19, 0, 1, 1)
        self.commission_input = QLineEdit(parent=self)
        self.commission_input.setText(str(self.commission))
        grid.addWidget(self.commission_input, 19, 1, 1, 1)

        grid.addWidget(QLabel(u"手续费(%)", parent=self), 20, 0, 1, 1)
        self.commission_input = QLineEdit(parent=self)
        self.commission_input.setText(str(self.commission))
        grid.addWidget(self.commission_input, 20, 1, 1, 1)

        grid.addWidget(QLabel(u"手续费(%)", parent=self), 21, 0, 1, 1)
        self.commission_input = QLineEdit(parent=self)
        self.commission_input.setText(str(self.commission))
        grid.addWidget(self.commission_input, 21, 1, 1, 1)
        # 创建ButtonBox，用户确定和取消
        # buttonBox = QDialogButtonBox(parent=self)
        # buttonBox.setOrientation(QtCore.Qt.Horizontal)  # 设置为水平方向
        # buttonBox.setStandardButtons(
        #     QDialogButtonBox.Cancel | QDialogButtonBox.Ok
        # )  # 确定和取消两个按钮
        # # 连接信号和槽
        # buttonBox.accepted.connect(self.accept)  # 确定
        # buttonBox.rejected.connect(self.reject)  # 取消

        # 垂直布局，布局表格及按钮
        layout = QVBoxLayout()

        # 加入前面创建的表格布局
        layout.addLayout(grid)

        # 放一个间隔对象美化布局
        spacerItem = QSpacerItem(
            20, 48, QSizePolicy.Minimum, QSizePolicy.Expanding
        )
        layout.addItem(spacerItem)

        # ButtonBox
        #layout.addWidget(buttonBox)

        self.setLayout(layout)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    dialog = ParamDialog()
    dialog.exec_()
    sys.exit(app.exec_())