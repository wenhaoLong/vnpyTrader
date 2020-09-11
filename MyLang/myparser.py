"""文法解析器"""
import ply.yacc as yacc
import MyLang.mylex as mylex
from MyLang.mylex import tokens
from MyLang.metadata import (RunEnvironment, String, Number, Binop, Relation, Group, Unary, Function,
                                  IfThenStatement, IfCommaStatement, ExprStatement, Variable, Program)


# 定义操作符优先级
precedence = (
    ('left', 'AND', 'OR'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE'),
    # ('left', 'POWER'),
    ('left', 'EQ', 'NE', 'LT', 'GT', 'LE', 'GE'),
    ('right', 'UPLUS', 'UMINUS'),
)

def p_program(p):
    '''program : program statement
               | statement'''
    if len(p) == 2:
        p[0] = Program()
        p[0].type = 'Program'
        p[0].operands = [p[1]]
    elif len(p) == 3:
        p[0] = p[1]
        p[0].operands.append(p[2])

def p_statement_assign(p):
    '''statement : ID ASSIGN expr SEMI
                 | VARIABLE ID ASSIGN expr SEMI'''
    p[0] = Variable()
    p[0].type = 'Variable'
    if len(p) == 5:
        p[0].operator = p[2]
        p[0].operands = [p[3]]
        p[0].name = p[1]
        p[0].lineno = p.lineno(1)
        RunEnvironment.run_vars[p[1]] = p[0]
    elif len(p) == 6:
        p[0].operator = p[3]
        p[0].operands = [p[4]]
        p[0].name = p[2]
        p[0].lineno = p.lineno(2)
        p[0].qualifier = p[1]
        RunEnvironment.run_vars[p[2]] = p[0]

def p_statement_expr(p):
    '''statement : expr SEMI'''
    p[0] = ExprStatement()
    p[0].type = 'ExprStatement'
    p[0].operands = [p[1]]

def p_statement_ifthen(p):
    '''statement : IF expr THEN BEGIN program END'''
    p[0] = IfThenStatement()
    p[0].type = 'IfThenStatement'
    p[0].operands = [p[2], p[5]]

def p_statement_ifcomma(p):
    '''statement : expr COMMA expr SEMI'''
    p[0] = IfCommaStatement()
    p[0].type = 'IfCommaStatement'
    p[0].operands = [p[1], p[3]]

def p_expr_unary(p):
    '''expr : MINUS expr %prec UMINUS
            | PLUS expr %prec UPLUS'''
    p[0] = Unary()
    p[0].type = 'Unary'
    p[0].operator = p[1]
    p[0].operands = [p[2]]
    p[0].lieno = p[2].lineno

def p_expr_binop(p):
    '''expr : expr PLUS expr
            | expr MINUS expr
            | expr TIMES expr
            | expr DIVIDE expr'''
    p[0] = Binop()
    p[0].type = 'Binop'
    p[0].operator = p[2]
    p[0].operands = [p[1], p[3]]
    p[0].lineno = p[1].lineno

def p_expr_relation(p):
    '''expr : expr LT expr
            | expr LE expr
            | expr GT expr
            | expr GE expr
            | expr EQ expr
            | expr NE expr
            | expr AND expr
            | expr OR expr'''
    p[0] = Relation()
    p[0].type = 'Relation'
    p[0].operator = p[2]
    p[0].operands = [p[1], p[3]]
    p[0].lineno = p[1].lineno

def p_expr_group(p):
    '''expr : LPAREN expr RPAREN'''
    p[0] = Group()
    p[0].type = 'Group'
    p[0].operator = '()'
    p[0].operands = [p[2]]
    p[0].lineno = p[2].lineno

def p_expr_id(p):
    '''expr : ID'''
    if p[1] not in RunEnvironment.run_vars.keys():
        raise Exception("未定义变量错误：在运行变量表中找不到{}".format(p[1]))
    p[0] = RunEnvironment.run_vars[p[1]]

def p_expr_number(p):
    '''expr : number'''
    p[0] = Number()
    p[0].type = 'Number'
    p[0].operands = [p[1]]
    p[0].lineno = p.lineno(1)

def p_expr_str(p):
    '''expr : str'''
    p[0] = String()
    p[0].type = 'String'
    p[0].operands = [p[1]]
    p[0].lineno = p.lineno(1)

def p_expr_function(p):
    '''expr : FUNCTION_NAME LPAREN args RPAREN
            | FUNCTION_NAME LPAREN RPAREN
            | FUNCTION_NAME
    '''
    p[0] = Function()
    p[0].type = 'function'
    p[0].operator = p[1]
    p[0].lineno = p.lineno(1)
    if len(p) == 5:
        p[0].operands = p[3]
    elif len(p) == 4 or len(p) == 2:
        p[0].operands = []

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
    p[0] = p[1][1:len(p[1])-1]

def p_error(p):
    if p:
        raise Exception("语法错误：出现在第{}行，字符{!r}附近.".format(p.lineno, p.value[0]))
    else:
        raise Exception("语法错误：出现在程序末尾.")


# 文法解析
def parse(code):
    # 重置词元解析器行数
    mylex.mylexer.lineno = 1
    # 重置词元解析下标
    mylex.mylexer.lexpos = 0
    # 文法解析器
    parser = yacc.yacc(debug=0)
    # 解析代码
    p = parser.parse(code)
    return p
