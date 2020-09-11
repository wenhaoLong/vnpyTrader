from .Token import TokenDef, Token
from .Exception import *
from .API import *

# 匹配字符串 liuzhu
import re
# 统计麦语言中有多少个trade_again
from . import glo_var

# 处理基类
class BaseHandler(object):
    # 缩进常量, 定义为4个空格
    INDENT = '    '
    # 缩进计数器
    INDENT_COUNT = 0
    # 需要进行参数字符化的函数个数统计
    ARG_STR_COUNT = 0
    # 括号统计
    PARENT_COUNT = 0

    def __init__(self, token_def=None):
        self.token_def = token_def

    # 判断是否匹配
    def is_match(self, token):
        if self.token_def is None:
            return True
        return token.token_def.name == self.token_def.name

    # 转换为python方法，返回是字符串，子类需要重写该方法
    def to_python(self, tokens, index):
        return tokens[index].value + " "

    # 得到一个换行后带缩进的字符串
    def get_newline(self):
        result = "\n"
        result += self.INDENT_COUNT * self.INDENT
        return result


# 注释的处理
class NoteHandler(BaseHandler):
    def __init__(self):
        super(NoteHandler, self).__init__(TokenDef.TOKEN_DEFS['NOTE'])

    # 注释返回# + 原值
    def to_python(self, tokens, index):
        # @author hengxincheung
        # @date 2010-10-15
        # @note 修改为返回空值
        return ""


# 换行的处理
class NewlineHandler(BaseHandler):
    def __init__(self):
        super(NewlineHandler, self).__init__(TokenDef.TOKEN_DEFS['NEWLINE'])

    def to_python(self, tokens, index):
        return self.get_newline()


# 等于判断的处理
class EqualHandler(BaseHandler):
    def __init__(self):
        super(EqualHandler, self).__init__(TokenDef.TOKEN_DEFS['EQ'])

    # 返回 ==
    def to_python(self, tokens, index):
        return '== '


# 不等于判断的处理
class NotEqualHandler(BaseHandler):
    def __init__(self):
        super(NotEqualHandler, self).__init__(TokenDef.TOKEN_DEFS['NE'])

    # 返回 !=
    def to_python(self, tokens, index):
        return '!= '


# if的处理
class IfHandler(BaseHandler):
    def __init__(self):
        super(IfHandler, self).__init__(TokenDef.TOKEN_DEFS['IF'])

    # 返回 if + 空格
    def to_python(self, tokens, index):
        return 'if '


# then的处理
class ThenHandler(BaseHandler):
    def __init__(self):
        super(ThenHandler, self).__init__(TokenDef.TOKEN_DEFS['THEN'])

    def to_python(self, tokens, index):
        result = ':'
        # 缩进计数+1
        BaseHandler.INDENT_COUNT += 1
        # 增加缩进
        result += self.get_newline()
        return result


# begin的处理
class BeginHandler(BaseHandler):
    def __init__(self):
        super(BeginHandler, self).__init__(TokenDef.TOKEN_DEFS['BEGIN'])

    # 返回一个空字符
    def to_python(self, tokens, index):
        return ''


# end的处理
class EndHandler(BaseHandler):
    def __init__(self):
        super(EndHandler, self).__init__(TokenDef.TOKEN_DEFS['END'])

    # 返回一个换行
    def to_python(self, tokens, index):
        # 缩进计数减一
        BaseHandler.INDENT_COUNT -= 1
        return self.get_newline()


# 分号的处理
class SemicolonHandler(BaseHandler):
    def __init__(self):
        super(SemicolonHandler, self).__init__(TokenDef.TOKEN_DEFS['SEMICOLON'])

    # 返回一个空字符串
    def to_python(self, tokens, index):
        return ''


# 标记符的处理
class IdentifierHandler(BaseHandler):
    def __init__(self):
        super(IdentifierHandler, self).__init__(TokenDef.TOKEN_DEFS['IDENTIFIER'])

    def to_python(self, tokens, index):

        # 如果是函数：当前的判断标准是，在 FUNCTIONS 的 key 列表中
        if tokens[index].value.upper() in FuncManager.FUNCTIONS.keys():

            # @Time    : 2019-10-15
            # @Author  : hengxincheung
            # 修改函数处理逻辑，增加字符化参数的处理方法

            # 如果右边存在元素
            if tokens[index + 1]:
                # 如果右边是(，表示是标准的函数
                if tokens[index + 1].value is '(':
                    # 如果该函数的参数需要字符化
                    if FuncManager.FUNCTIONS[tokens[index].value.upper()]:
                        BaseHandler.ARG_STR_COUNT += 1
                    result = "    "
                    result += 'self.editor_engine.'
                    result += tokens[index].value
                    if result.__contains__("self.editor_engine.trade_again"):
                        glo_var.set_value('trade_again_round', glo_var.get_value('trade_again_round')+1)
                        str_replace = glo_var.get_value("trade_again_str").format(glo_var.get_value('trade_again_round'), tokens[index + 2].value, glo_var.get_value('trade_again_round')+1,
                                   glo_var.get_value('trade_again_round'), glo_var.get_value('trade_again_round')+1)
                        result = str_replace+result

                    return result

            result = "    "
            result += 'self.editor_engine.'
            result += tokens[index].value
            result += "()"

            return result

        # 否则，是变量，直接返回其值
        return tokens[index].value


# 赋值号的处理
class AssignHandler(BaseHandler):
    def __init__(self):
        super(AssignHandler, self).__init__(TokenDef.TOKEN_DEFS['ASSIGN'])

    def to_python(self, tokens, index):
        return '= '


# 与运算的处理
class AndHandler(BaseHandler):
    def __init__(self):
        super(AndHandler, self).__init__(TokenDef.TOKEN_DEFS['AND'])

    def to_python(self, tokens, index):
        return ' and '


# 或运算的处理
class OrHandler(BaseHandler):
    def __init__(self):
        super(OrHandler, self).__init__(TokenDef.TOKEN_DEFS['OR'])

    def to_python(self, tokens, index):
        return ' or '


# variable关键字处理
class VariableHandler(BaseHandler):
    def __init__(self):
        super(VariableHandler, self).__init__(TokenDef.TOKEN_DEFS['VARIABLE'])

    def to_python(self, tokens, index):
        return "global "


# 逗号的处理
class CommaHandler(BaseHandler):
    def __init__(self):
        super(CommaHandler, self).__init__(TokenDef.TOKEN_DEFS['COMMA'])

    def to_python(self, tokens, index):
        if BaseHandler.ARG_STR_COUNT == 1 and BaseHandler.ARG_STR_COUNT == BaseHandler.PARENT_COUNT:
            return "\", \""
        else:
            return ", "


# 左小括号的处理
class LSBRHandler(BaseHandler):
    def __init__(self):
        super(LSBRHandler, self).__init__(TokenDef.TOKEN_DEFS['LS_BR'])

    def to_python(self, tokens, index):
        if BaseHandler.ARG_STR_COUNT > 0:
            # 小括号数加一
            BaseHandler.PARENT_COUNT += 1
            if BaseHandler.ARG_STR_COUNT == 1 and BaseHandler.ARG_STR_COUNT == BaseHandler.PARENT_COUNT:
                return "(\""
        return "("


# 右小括号的处理
class RSBRHandler(BaseHandler):
    def __init__(self):
        super(RSBRHandler, self).__init__(TokenDef.TOKEN_DEFS['RS_BR'])

    def to_python(self, tokens, index):
        result = ""
        if BaseHandler.ARG_STR_COUNT > 0:
            if BaseHandler.ARG_STR_COUNT == 1 and BaseHandler.ARG_STR_COUNT == BaseHandler.PARENT_COUNT:
                result += "\")"
            # 表示一个字符化参数已经处理完毕，计数器减一
            BaseHandler.ARG_STR_COUNT -= 1
            # 小括号数减一
            BaseHandler.PARENT_COUNT -= 1
        if len(result) > 0:
            return result
        else:
            return ")"
