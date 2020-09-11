import sys
import os
import wmi
import uuid
from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit,
    QGridLayout, QApplication,
)


def get_mac_address():
    """得到本机的 MAC 地址"""
    mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
    return ":".join([mac[e:e + 2] for e in range(0, 11, 2)])


def get_disk_serial_number():
    """得到硬盘序列号"""
    c = wmi.WMI()
    for physical_disk in c.Win32_DiskDrive():
        return physical_disk.SerialNumber
    return "error"


def get_cpu_serial_number():
    """获取cpu序列号"""
    c = wmi.WMI()
    for cpu in c.Win32_Processor():
        return cpu.ProcessorId.strip()
    return "error"


def get_board_serial_number():
    """获取主板序列号"""
    c = wmi.WMI()
    for board in c.Win32_BaseBoard():
        return board.SerialNumber
    return "error"


class ComputerChecker(QWidget):
    """电脑硬件信息查看器"""
    def __init__(self):
        super().__init__()
        # 获取当前程序文件位置
        self.cwd = os.getcwd()

        # 定义ui中的元素
        self.mac_address_label = QLabel("MAC地址")
        self.mac_address_edit = QLineEdit()
        self.disk_serial_number_label = QLabel("硬盘序列号")
        self.disk_serial_number_edit = QLineEdit()
        self.cpu_serial_number_label = QLabel("cpu序列号")
        self.cpu_serial_number_edit = QLineEdit()
        self.board_serial_number_label = QLabel("主板序列号")
        self.board_serial_number_edit = QLineEdit()

        self.init_ui()

    def init_ui(self):
        # 设置界面抬头
        self.setWindowTitle("电脑硬件信息查看器<云集工作室>")

        # 表单内容
        self.mac_address_edit.setText(get_mac_address())
        self.mac_address_edit.setReadOnly(True)
        self.disk_serial_number_edit.setText(get_disk_serial_number())
        self.disk_serial_number_edit.setReadOnly(True)
        self.cpu_serial_number_edit.setText(get_cpu_serial_number())
        self.cpu_serial_number_edit.setReadOnly(True)
        self.board_serial_number_edit.setText(get_board_serial_number())
        self.board_serial_number_edit.setReadOnly(True)

        # 使用表格布局
        grid = QGridLayout()
        grid.setSpacing(10)
        # 布局设置
        # mac地址表
        grid.addWidget(self.mac_address_label, 1, 0)
        grid.addWidget(self.mac_address_edit, 1, 1)
        # 硬盘序列号
        grid.addWidget(self.disk_serial_number_label, 2, 0)
        grid.addWidget(self.disk_serial_number_edit, 2, 1)
        # cpu序列号
        grid.addWidget(self.cpu_serial_number_label, 3, 0)
        grid.addWidget(self.cpu_serial_number_edit, 3, 1)
        # 主板序列号
        grid.addWidget(self.board_serial_number_label, 4, 0)
        grid.addWidget(self.board_serial_number_edit, 4, 1)

        # 设置布局
        self.setLayout(grid)
        # 设置大小
        self.setFixedSize(480, 320)
        self.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    lg = ComputerChecker()
    sys.exit(app.exec_())
