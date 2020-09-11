import re
from .Token import Token, TokenDef
from .Exception import NoMatchingTokenFoundError

__author__ = 'hengxincheung'


class BaseLexer(object):
    """
        词元分析器基类
    """
    # 类变量:词元定义列表
    TOKEN_DEFS = []

    def __init__(self, text, ignore_case=False):
        # 需要分析的文本
        if ignore_case:
            self.text = text.lower()
        else:
            self.text = text
        # 当前的总下标
        self.text_pos = 0
        # 当前的所在行
        self.line_num = 1
        # 当前在所在行中的下标
        self.line_pos = 1

    # 词元分析方法
    def lex(self):
        # 声明词元列表
        tokens = []
        # 当还有词元时
        while self.more_token():
            # 词元列表加入下一个词元
            token = self.get_next_token()
            if token is not None:
                # 更新下标
                self.text_pos += len(token)
                self.line_pos += len(token)
                tokens.append(token)
        # 返回词元列表
        return tokens

    # 判断是否仍有词元的方法
    def more_token(self):
        if self.text_pos < len(self.text):
            return True
        return False

    # 得到下一个词元方法
    def get_next_token(self):
        # 寻找能与词元定义匹配的词元
        token = self.match_token()
        if (token is not None) and (not token.token_def.ignore):
            return token
        return None


    # 匹配词元方法
    def match_token(self):
        # 得到词元定义列表
        token_defs = self.__class__.TOKEN_DEFS
        # 匹配到的词元列表
        matches = []
        # 遍历匹配
        for token_def in token_defs:
            # 如果与词元定义匹配成功则返回
            match = token_def.regexp.match(self.text, self.text_pos)
            if match:
                # 创建词元
                token = Token(token_def, match.group(0), self.line_num, self.line_pos)
                # 将词元加入到匹配列表中
                matches.append(token)

        # 如果匹配列表中存在词元
        if matches:
            # 取得最长的词元
            token = max(matches, key=len)
            if token.token_def.name == 'NEWLINE':
                self.line_num += 1
                self.line_pos = 0
            return token

        # 判断是不是空白字符
        if self.text[self.text_pos] == ' ' or self.text[self.text_pos] == '\f'\
                or self.text[self.text_pos] == '\t':
            self.text_pos += 1
            self.line_pos += 1
            return None

        # 抛出无匹配的定义词元异常
        raise NoMatchingTokenFoundError(
            self.line_num,
            self.line_pos,
            self.text[self.text_pos:self.text_pos + 10],
        )


class McLexer(BaseLexer):
    TOKEN_DEFS = [
        # 关键字
        TokenDef('IF', r'if'),  # if 关键字
        TokenDef('THEN', r'then'),  # then 关键字
        TokenDef('BEGIN', r'begin'),    # begin 关键字
        TokenDef('END', r'end'),    # end 关键字
        TokenDef('VARIABLE', r'variable'),  # variable 关键字
        # 系统变量
        # TokenDef('O', r'o'),    # 系统变量O，表示open(开盘价)
        # TokenDef('H', r'h'),    # 系统变量H
        # TokenDef('L', r'l'),    # 系统变量L
        # TokenDef('C', r'c'),    # 系统变量C，表示close(收盘价)
        # 限界符
        TokenDef('LS_BR', r'\('),   # 左小括号
        TokenDef('RS_BR', r'\)'),   # 右小括号
        TokenDef('LM_BR', r'\['),  # 左中括号
        TokenDef('RM_BR', r'\]'),  # 右中括号
        TokenDef('LB_BR', r'\{'),  # 左大括号
        TokenDef('RB_BR', r'\}'),  # 右大括号
        TokenDef('COMMA', r','),    # 逗号
        TokenDef('SEMICOLON', r';'),    # 分号
        # 运算符
        TokenDef('ADD', r'\+'), # 加
        TokenDef('SUB', r'-'),  # 减
        TokenDef('MUL', r'\*'), # 乘
        TokenDef('DIV', r'\/'), # 除
        TokenDef('AND', r'&&|and'), # 与
        TokenDef('OR', r'\|\||or'), # 或
        TokenDef('GR', r'>'),  # 大于
        TokenDef('GE', r'>='), # 大于等于
        TokenDef('LS', r'<'), # 小于
        TokenDef('LE', r'<='), # 小于等于
        TokenDef('NE', r'<>'),  # 不等于
        TokenDef('EQ', r'='), # 等于
        TokenDef('ASSIGN', r':=|:|\^\^|\.\.'),  # 赋值号
        # 其他
        # @author hengxincheung
        # @date 2019-10-15
        # @note 修改字符串识别规则为非贪婪，即可以在存在多余的引号抛出错误
        TokenDef('STR', r'\'.*?\'|\".*?\"'),   # 字符串
        TokenDef('NUMERIAL', r'[\+-]?[0-9]+\.?[0-9]*'), # 数字
        TokenDef('IDENTIFIER', r'[a-zA-Z_][0-9a-zA-Z_]*'),    # 标识符
        TokenDef('NOTE', r'//.*'),   # 注释
        TokenDef('NEWLINE', r'\r?\n'),  # 换行
    ]
