import sys
from vnpy.app.editor_manager.ui.line_number_area import LineNumberArea
from vnpy.app.editor_manager.ui.lexer import Lexer
from vnpy.trader.ui import QtGui, QtWidgets, QtCore
from PyQt5 import Qsci
from PyQt5 import Qt


class CodeEditor(QtWidgets.QPlainTextEdit):
    def __init__(self):
        super().__init__()
        self.lineNumberArea = LineNumberArea(self)

        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)

    def updateLineNumberAreaWidth(self, _):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(),
                                       rect.height())

        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)

        cr = self.contentsRect();
        self.lineNumberArea.setGeometry(QtCore.QRect(cr.left(), cr.top(),
                                                     self.lineNumberAreaWidth(), cr.height()))

    def lineNumberAreaPaintEvent(self, event):
        mypainter = QtGui.QPainter(self.lineNumberArea)

        mypainter.fillRect(event.rect(), Qt.lightGray)

        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        # Just to make sure I use the right font
        height = self.fontMetrics().height()
        while block.isValid() and (top <= event.rect().bottom()):
            if block.isVisible() and (bottom >= event.rect().top()):
                number = str(blockNumber + 1)
                mypainter.setPen(Qt.black)
                mypainter.drawText(0, top, self.lineNumberArea.width(), height,
                                   Qt.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            blockNumber += 1

    def highlightCurrentLine(self):
        extraSelections = []

        if not self.isReadOnly():
            selection = QtWidgets.QTextEdit.ExtraSelection()

            lineColor = QtGui.QColor(Qt.yellow).lighter(160)

            selection.format.setBackground(lineColor)
            selection.format.setProperty(QtGui.QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)
        self.setExtraSelections(extraSelections)


class MyLangEditor(Qsci.QsciScintilla):
    def __init__(self, parent=None):
        super(MyLangEditor, self).__init__(parent=parent)
        # 默认字体
        self.font = QtGui.QFont("Courier", 16)

        # 词法解析器
        self.lexer = Lexer(parent=self)
        self.lexer.setFont(self.font)
        self.setLexer(self.lexer)

        # 标志内容是否发生改变
        self.text_change = False

        self.init_ui()

    def init_ui(self):
        # 设置编码格式为utf-8
        self.setUtf8(True)
        # 设置以'\n'换行
        self.setEolMode(self.SC_EOL_LF)
        # 设置自动换行
        self.setWrapMode(self.WrapWord)
        # 设置默认字体
        self.setFont(self.font)

        # 设置tab键功能
        self.setTabWidth(4)  # Tab等于4个空格
        self.setIndentationsUseTabs(True)   # 行首缩进采用Tab键，反向缩进是Shift+Tab
        self.setIndentationWidth(4)  # 行首缩进宽度为4个空格
        self.setIndentationGuides(True)  # 显示虚线垂直线的方式来指示缩进
        self.setAutoIndent(True)  # 插入新行时，自动缩进将光标推送到与前一个相同的缩进级别

        # 设置光标
        self.setCaretWidth(2)   # 光标宽度（以像素为单位），0表示不显示光标
        self.setCaretForegroundColor(QtGui.QColor("#ff0000ff"))  # 设置光标前景色
        self.setCaretLineVisible(True)  # 设置是否使用光标所在行背景色
        self.setCaretLineBackgroundColor(QtGui.QColor('#FFCFCF'))  # 光标所在行的底色

        # 设置页边，有3种Margin：0-行号; 1-改动标识; 2-代码折叠
        self.setMarginsFont(self.font)  # 行号字体
        self.setMarginLineNumbers(0, True)  # 设置标号为0的页边显示行号
        self.setMarginWidth(0, '000')  # 行号宽度
        # self.setMarginBackgroundColor() # 设置页边背景颜色，这个api不会用

        # 设置自动补全
        # self.setAutoCompletionSource(Qsci.QsciScintilla.AcsAll)  # 对于所有Ascii码补全
        # self.setAutoCompletionCaseSensitivity(False)  # 取消自动补全大小写敏感
        # self.setAutoCompletionThreshold(1)  # 输入1个字符，就出现自动补全提示

        # # 设置窗口大小
        # self.setFixedSize(1024, 760)

        # 设置文档窗口的标题
        self.setWindowTitle("MyEditor")
