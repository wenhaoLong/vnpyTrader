# 导入正则库
import re
# 导入异常类
from .Exception import TokenMatchesEmptyStringError

__author__ = 'hengxincheung'


class TokenDef(object):
    # 类变量:已定义的词元定义字典
    TOKEN_DEFS = {}
    """
        词元定义
        @:param name:词元定义的名字
        @:param pattern:词元的正则表达式（字符串）
        @:param ignore:扫描时是否忽略，即是否生成对应的词元
    """
    def __init__(self, name, pattern, ignore=False):
        self.name = name
        self.pattern = pattern
        self.ignore = ignore
        # 编译正则表达式
        self.regexp = re.compile(self.pattern, re.UNICODE)

        # 确保正则表达式不会匹配到空字符串
        if self.regexp.match(''):
            raise TokenMatchesEmptyStringError(self.pattern)

        # 添加当前词元定义到字典中
        self.__class__.TOKEN_DEFS[self.name] = self

    # 重写__str__方法
    def __str__(self):
        return 'name:{}, pattern:{}, ignore:{}'.format(
            self.name, self.pattern, self.ignore)


class Token(object):
    """
        词元
        @:param type:词元的类型，即词元定义
        @:param value:当前词元的值，即匹配到的字符串
        @:param line_num:当前词元所在行
        @:param line_pos:当前词元在行里的开始下标
    """
    def __init__(self, token_def, value, line_num, line_pos):
        self.token_def = token_def
        self.value = value
        self.line_num = line_num
        self.line_pos = line_pos

    # 重写__str__方法
    def __str__(self):
        return 'name:{}, value:{} @ <line {}, col {}>'.format(
            self.token_def.name, repr(self.value), self.line_num, self.line_pos)

    # 重写__len__方法
    def __len__(self):
        return len(self.value)
