# import sys
# from PyQt5.QtWidgets import *
#
#
# class MainWindow(QDialog):
#     def __init__(self, ):
#         super(QDialog, self).__init__()
#         self.number = 0
#
#
#
#         self.topFiller = QWidget()
#         self.topFiller.setMinimumSize(250, 1000)  #######设置滚动条的尺寸
#         for filename in range(20):
#             self.MapButton = QPushButton(self.topFiller)
#             self.MapButton.setText(str(filename))
#             self.MapButton.move(10, filename * 40)
#
#         ##创建一个滚动条
#         self.scroll = QScrollArea()
#         self.scroll.setWidget(self.topFiller)
#
#         self.vbox = QVBoxLayout()
#         self.vbox.addWidget(self.scroll)
#
#
#         self.setLayout(self.vbox)
#
#         self.resize(300, 500)
#
# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     mainwindow = MainWindow()
#     mainwindow.show()
#     sys.exit(app.exec_())

a = [1,2,3,4]
print(sum(a))