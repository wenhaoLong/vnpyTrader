"""词元解析模块"""

from MyLang.builtin import reserved, operator, delimiter, function
import ply.lex as lex
from MyLang.metadata import RunEnvironment

# 标记元组
tokens = reserved + operator + delimiter + (
    "ID",  # 标记符
    "INTEGER",  # 整数
    "FLOAT",  # 浮点数
    "SINGLE_STRING",  # 使用单引号的字符串
    "DOUBLE_STRING",  # 使用双引号的字符串
    "FUNCTION_NAME",  # 函数名
    "COMMENT",  # 注释
    "NEWLINE",  # 换行
)

# 忽略空白字符
t_ignore = '[ \f\t]'
# 注释
t_ignore_COMMENT = r'//.*'

# 运算符
t_PLUS = r'\+'  # 加
t_MINUS = r'-'  # 减
t_TIMES = r'\*'  # 乘
t_DIVIDE = r'/'  # 除
t_AND = r'&&'  # 与
t_OR = r'\|\|'  # 或
t_EQ = r'='  # equal, 等于
t_NE = r'<>'  # not equal, 不等于
t_ASSIGN = r':=|:|\^\^|\.\.'  # 赋值
t_LT = r'<'  # less than, 小于
t_GT = r'>'  # greater than, 大于
t_LE = r'<='  # less than and equal, 小于等于
t_GE = r'>='  # greater than and equal, 大于等于

# 限界符
t_COMMA = r'\,'  # 逗号
t_SEMI = r';'  # 分号
t_LPAREN = r'\('  # 左小括号: '('
t_RPAREN = r'\)'  # 右小括号: ')'

# 字符串
t_SINGLE_STRING = r'\'.*?\''
t_DOUBLE_STRING = r'\".*?\"'


# 换行符
def t_ignore_NEWLINE(t):
    r'\r?\n'
    t.lexer.lineno += 1


# 标记符
def t_ID(t):
    r'[_a-zA-Z][_a-zA-Z0-9]*'
    # 所有标记符转大写，麦语言标记符大小写不敏感
    t.value = t.value.upper()
    # 判断是否在保留字，转换类型
    if t.value in reserved:
        t.type = t.value
    elif t.value in function:
        t.type = 'FUNCTION_NAME'
        # 处理特殊的函数
        if t.value == 'IF':
            t.value = 'IFF'
        elif t.value == 'NOT':
            t.value = 'NOTT'
        elif t.value == 'TIME':
            t.value = 'TTIME'
        elif t.value == 'TRADE_AGAIN':  # 提前感知是否使用TRADE_AGAIN函数
            RunEnvironment.is_limit_trade_again = True
    # 处理特殊情况：AND
    elif t.value == 'AND':
        t.type = 'AND'
        t.value = '&&'
    # 处理特殊情况：OR
    elif t.value == 'OR':
        t.type = 'OR'
        t.value = '||'
    return t


# 整数
def t_INTEGER(t):
    r'(0[xX][\da-fA-F]+[lL]?|0[bB][01]+[lL]?|(0[oO][0-7]+)|(0[0-7]*)[lL]?|[1-9]\d*[lL]?)'
    t.value = int(t.value)
    return t


# 浮点数
def t_FLOAT(t):
    r'(\d*\.\d*\[\d+\]|(\d+\.\d*|\.\d+)([eE][-+]?\d+)?|\d+[eE][-+]?\d+)'
    t.value = float(t.value)
    return t

# 错误处理
def t_error(t):
    raise Exception("非法字符错误:第{}行,错误字符为{!r}".format(t.lineno, t.value[0]))

# 词元解析器
mylexer = lex.lex(debug=0)