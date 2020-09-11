import sys
import os
import datetime
import pickle
from rsa import PrivateKey, PublicKey
from rsa import common, transform, core
from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit,
    QGridLayout, QApplication, QPushButton,
    QFileDialog, QMessageBox,
)


class LicenseGenerator(QWidget):
    """license生成器"""
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
        self.end_date_label = QLabel("到期时间")
        self.end_date_edit = QLineEdit()
        self.file_chooser_label = QLabel("加密文件")
        self.file_chooser_btn = QPushButton(self)
        self.dir_chooser_label = QLabel("输出路径")
        self.dir_chooser_btn = QPushButton(self)
        self.submit_btn = QPushButton(self)

        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        # 设置界面抬头
        self.setWindowTitle("License生成器<云集工作室>")

        # 使用表格布局
        grid = QGridLayout()
        grid.setSpacing(10)

        # 表单内容
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
        # 过期日期 格式应该为 yyyy-MM-dd
        grid.addWidget(self.end_date_label, 5, 0)
        grid.addWidget(self.end_date_edit, 5, 1)
        # 加密文件
        self.file_chooser_btn.setText("点击选择")
        grid.addWidget(self.file_chooser_label, 6, 0)
        grid.addWidget(self.file_chooser_btn, 6, 1)
        # 输出文件夹
        self.dir_chooser_btn.setText("点击选择")
        grid.addWidget(self.dir_chooser_label, 7, 0)
        grid.addWidget(self.dir_chooser_btn, 7, 1)
        # 生成按钮
        self.submit_btn.setText("生成License")
        grid.addWidget(self.submit_btn, 8, 0)

        # 设置信号
        self.file_chooser_btn.clicked.connect(self.choose_file)
        self.dir_chooser_btn.clicked.connect(self.choose_dir)
        self.submit_btn.clicked.connect(self.submit)

        # 设置布局
        self.setLayout(grid)
        # 设置大小
        self.setFixedSize(480, 480)
        self.show()

    def choose_file(self):
        """选择文件"""
        file_name, file_type = QFileDialog.getOpenFileName(self, "选取文件",
                                                           self.cwd, "All Files (*)")
        if file_name == "":
            return
        # 将选择的文件显示到界面上
        self.file_chooser_btn.setText(file_name)

    def choose_dir(self):
        """选择文件夹"""
        directory = QFileDialog.getExistingDirectory(self, "选择文件夹", self.cwd)
        if directory == "":
            return
        # 将选择的文件夹显示到界面上
        self.dir_chooser_btn.setText(directory)

    def submit(self):
        try:
            # 生成license
            _license = self.__generate_license(
                self.mac_address_edit.text(), self.disk_serial_number_edit.text(),
                self.cpu_serial_number_edit.text(), self.board_serial_number_edit.text(),
                self.end_date_edit.text()
            )
            # 加载密钥
            with open(self.file_chooser_btn.text(), 'rb') as f:
                private_key = pickle.load(f)
            # 加密license
            cipher = self.__rsa_encrypt(_license, private_key)
            # 将license保存到指定路径下
            path = self.dir_chooser_btn.text() + "\\license"
            with open(path, 'wb') as f:
                f.write(cipher)
            self.info("License生成成功")
        except Exception as e:
            self.info(e.__str__())

    def info(self, message):
        """弹出消息框"""
        QMessageBox.about(self, '消息', message)

    def __rsa_encrypt(self, message, key):
        """加密方法"""
        # 判断密钥类型
        if isinstance(key, PublicKey):
            a = key.e
            b = key.n
        elif isinstance(key, PrivateKey):
            a = key.d
            b = key.n
        else:
            raise TypeError("'key' must be PublicKey or PrivateKey")

        key_length = common.byte_size(b)
        # 得到信息字节
        message_bytes = bytes(message, encoding='utf-8')
        padded = self.__pad_for_encrypt(message_bytes, key_length)
        num = transform.bytes2int(padded)
        decryto = core.encrypt_int(num, a, b)
        out = transform.int2bytes(decryto)
        return out

    @staticmethod
    def __pad_for_encrypt(message, target_length):
        """填充加密内容"""
        max_length = target_length - 11
        message_length = len(message)

        if message_length > max_length:
            raise OverflowError("%i bytes needed for message, but there is only space for %i"
                                % (message_length, max_length))

        padding = b""
        padding_length = target_length - message_length - 3

        while len(padding) < padding_length:
            needed_bytes = padding_length - len(padding)
            new_padding = os.urandom(needed_bytes + 5)
            new_padding = new_padding.replace(b"\x00", b"")
            padding = padding + new_padding[:needed_bytes]

        assert len(padding) == padding_length

        return b"".join([b"\x00\x02", padding, b"\x00", message])

    @staticmethod
    def __generate_license(mac_address, disk_serial_number, cpu_serial_number,
                           board_serial_number, end_date):
        """产生license"""
        _license = {}
        # 校验mac地址是否合法
        if len(mac_address) != 17:
            raise Exception("The length of mac-address must be 17!")
        if len(mac_address.split(':')) != 6:
            raise Exception("Format of mac-address error!")
        # 转换结束时间
        end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S").__str__()
        # 组装license
        _license["mac_address"] = mac_address
        _license["disk_serial_number"] = disk_serial_number
        _license["cpu_serial_number"] = cpu_serial_number
        _license["board_serial_number"] = board_serial_number
        _license["end_date"] = end_date
        # 返回license
        return _license.__str__()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    lg = LicenseGenerator()
    sys.exit(app.exec_())