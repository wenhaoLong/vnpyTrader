import ply.yacc as yacc
import McLanguage.mylex as mylex
from McLanguage.error import SynataxError, UndefinedVariableError
from McLanguage.builtin import system_variable

# 变量集合
vars = set()

# 得到定义的标记列表
tokens = mylex.tokens

# 定义操作符优先级
precedence = (
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE'),
    # ('left', 'POWER'),
    ('right', 'UPLUS', 'UMINUS')
)

def p_program(p):
    '''program : program statement
               | statement'''
    if len(p) == 2:
        p[0] = ('program', [p[1]])
    elif len(p) == 3:
        p[0] = p[1]
        p[0][1].append(p[2])

def p_statement_assign(p):
    '''statement : ID ASSIGN expr SEMI'''
    p[0] = ('statement_assign', p[1], p[3])
    # 将定义过的变量加入集合
    vars.add(str(p[1]))

def p_statement_expr(p):
    '''statement : expr SEMI'''
    p[0] = ('statement_expr', p[1])

def p_statement_ifthen(p):
    '''statement : IF expr THEN BEGIN program END'''
    p[0] = ('statement_ifthen', p[2], p[5])

def p_statement_ifcomma(p):
    '''statement : expr COMMA expr SEMI'''
    p[0] = ('statement_ifcomma', p[1], p[3])

def p_expr_unary(p):
    '''expr : MINUS expr %prec UMINUS
            | PLUS expr %prec UPLUS'''
    p[0] = ('unary', p[1], p[2])

def p_expr_binop(p):
    '''expr : expr PLUS expr
            | expr MINUS expr
            | expr TIMES expr
            | expr DIVIDE expr'''
    p[0] = ('binop', p[2], p[1], p[3])

def p_expr_relation(p):
    '''expr : expr LT expr
            | expr LE expr
            | expr GT expr
            | expr GE expr
            | expr EQ expr
            | expr NE expr
            | expr AND expr
            | expr OR expr'''
    p[0] = ('relation', p[2], p[1], p[3])

def p_expr_group(p):
    '''expr : LPAREN expr RPAREN'''
    p[0] = ('group', p[2])

def p_expr_id(p):
    '''expr : ID'''
    p[0] = ('id', p[1])
    # warning信息:判断变量之前有无定义
    if p[1] not in vars:
        raise UndefinedVariableError(p.slice[1])

def p_expr_number(p):
    '''expr : number'''
    p[0] = ('number', p[1])

def p_expr_str(p):
    '''expr : str'''
    p[0] = ('str', p[1])

def p_expr_function(p):
    '''expr : function'''
    p[0] = ('function', p[1])

def p_function(p):
    '''function : FUNCTION_NAME LPAREN args RPAREN
                | FUNCTION_NAME
                | FUNCTION_NAME LPAREN RPAREN
    '''
    if len(p) == 5:
        p[0] = (p[1], tuple(p[3]))
    elif len(p) == 2 or len(p) == 4:
        p[0] = (p[1])

def p_args(p):
    '''args : args COMMA expr
            | expr
    '''
    if len(p) == 2:
        p[0] = [p[1]]
    elif len(p) == 4:
        p[0] = p[1]
        p[0].append(p[3])

def p_number(p):
    '''number : INTEGER
              | FLOAT
              | INTEGER FLOAT
    '''
    if len(p) == 2:
        p[0] = p[1]
    elif len(p) == 3:
        p[0] = p[1] + p[2]

def p_str(p):
    '''str : SINGLE_STRING
           | DOUBLE_STRING'''
    # 去除引号
    p[0] = (p[1][1:len(p[1])-1])

def p_error(p):
    if p:
        raise SynataxError(p)
    else:
        raise SynataxError(None, True)


# 文法解析
def parse(text):
    # 重置行数
    mylex.mylexer.lineno = 1
    # 重置下标
    mylex.mylexer.lexpos = 0
    # 文法解析器
    parser = yacc.yacc(debug=0)
    # 重置变量集合
    vars.clear()
    for var in system_variable:
        vars.add(var)
    # 解析代码
    p = parser.parse(text)
    # print(vars)
    return p
