import ctypes
import platform
import sys
import traceback

import qdarkstyle
from PyQt5 import QtGui, QtWidgets, QtCore

from .mainwindow import MainWindow
from ..setting import SETTINGS
from ..utility import get_icon_path


def excepthook(exctype, value, tb):
    """
    Raise exception under debug mode, otherwise 
    show exception detail with QMessageBox.
    """
    sys.__excepthook__(exctype, value, tb)

    msg = "".join(traceback.format_exception(exctype, value, tb))
    QtWidgets.QMessageBox.critical(
        None, "Exception", msg, QtWidgets.QMessageBox.Ok
    )


def create_qapp(app_name: str = "VN Trader"):
    """
    Create Qt Application.
    """
    sys.excepthook = excepthook

    qapp = QtWidgets.QApplication([])
    qapp.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())

    font = QtGui.QFont(SETTINGS["font.family"], SETTINGS["font.size"])
    qapp.setFont(font)

    # @Time    : 2019-10-09
    # @Author  : Wang Yongchang
    # 为pyinstaller打包exe,改变静态文件查找路径方式
    icon = QtGui.QIcon(get_icon_path("vnpy.ico"))
    qapp.setWindowIcon(icon)

    if "Windows" in platform.uname():
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            app_name
        )

    return qapp
