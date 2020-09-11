# 运行环境
class RunEnvironment(object):
    # 运行代码
    run_code = ''
    # 运行引擎
    run_engine = None
    # 语法树
    run_ast = None
    # 运行变量表
    run_vars = {}
    # 运行栈
    run_stack = []
    # 表达式历史栈
    run_history = []
    # 运行时的交易信号
    run_trade = []
    # 有无使用trade_again函数
    is_limit_trade_again = False
    # 运行时日志的值
    run_log_value = {}


# 得到当前运行的表达式
def get_current_expr():
    if len(RunEnvironment.run_stack) >= 1:
        return RunEnvironment.run_stack[-1]
    else:
        return None


class Expr(object):
    def __init__(self):
        self.type = None  # 表达式类型
        self.operator = None  # 运算符
        self.operands = None  # 操作数
        self.lineno = -1  # 表达式所在行数
        self.value = []  # 表达式的值

    # 执行方法
    def exec(self):
        # 加入运行栈中
        RunEnvironment.run_stack.append(self)
        # 调用执行方法
        value = self.eval()
        if len(self.value) >= 2:
            self.value.pop(0)
        self.value.append(value)
        # 限制一下历史栈的数据个数最多不超过2048，否则弹出一半数据销毁
        if len(RunEnvironment.run_history) >= 2048:
            [RunEnvironment.run_history.pop(0) for _ in range(1024)]
        # 从运行栈中弹出并添加进表达式历史栈中
        RunEnvironment.run_history.append(RunEnvironment.run_stack.pop())
        return value

    # 计算方法，会返回表达式的值
    def eval(self):
        pass

    # 重写字符串方法，返回表达式的标准字符串形式
    def __str__(self):
        pass


# 数字表达式
class Number(Expr):
    def eval(self):
        return self.operands[0]

    def __str__(self):
        return str(self.operands[0])


# 字符串表达式
class String(Expr):
    def eval(self):
        return self.operands[0]

    def __str__(self):
        return "\'" + str(self.operands[0]) + "\'"


# unary表达式
class Unary(Expr):
    def eval(self):
        if self.operator == '+':
            return self.operands[0].exec()
        elif self.operator == '-':
            return -self.operands[0].exec()

    def __str__(self):
        if self.operator == '+':
            return str(self.operands[0])
        elif self.operator == '-':
            return '-' + str(self.operands[0])


class Group(Expr):
    def eval(self):
        return self.operands[0].exec()

    def __str__(self):
        return '(' + str(self.operands[0]) + ')'


# 四则运算表达式
class Binop(Expr):
    def eval(self):
        value_left = self.operands[0].exec()
        value1_right = self.operands[1].exec()
        if self.operator == '+':
            return value_left + value1_right
        elif self.operator == '-':
            return value_left - value1_right
        elif self.operator == '*':
            return value_left * value1_right
        elif self.operator == '/':
            if value1_right == 0 or value1_right == None:
                raise Exception('除数不能为0或None')
            return value_left / value1_right

    def __str__(self):
        return str(self.operands[0]) + self.operator + str(self.operands[1])


# 关系表达式运算
class Relation(Expr):
    def eval(self):
        value_left = self.operands[0].exec()
        value_right = self.operands[1].exec()
        if self.operator == '&&':
            return value_left and value_right
        elif self.operator == '||':
            return value_left or value_right
        elif self.operator == '>':
            return value_left > value_right
        elif self.operator == '<':
            return value_left < value_right
        elif self.operator == '>=':
            return value_left >= value_right
        elif self.operator == '<=':
            return value_left <= value_right
        elif self.operator == '<>':
            return value_left != value_right
        elif self.operator == '=':
            return value_left == value_right

    def __str__(self):
        return str(self.operands[0]) + self.operator + str(self.operands[1])


class Function(Expr):
    def eval(self):
        # args = []
        kwargs = {}
        # 遍历执行得到参数值
        # for expr in self.operands:
        #     args.append(expr.exec())
        # 通过引擎调用相关函数
        return eval("RunEnvironment.run_engine." + self.operator.lower())(*self.operands, **kwargs)

    def __str__(self):
        result = self.operator + '('
        for arg in self.operands:
            result = result + str(arg)
            result = result + ','
        if len(self.operands) > 0:
            result = result[0:len(result) - 1]
        result = result + ")"
        return result


class IfThenStatement(Expr):
    def eval(self):
        if self.operands[0].exec():
            return self.operands[1].exec()

    def __str__(self):
        return "IF " + str(self.operands[0]) + " THEN\nBEGIN\n" + str(self.operands[1]) + "END"


class ExprStatement(Expr):
    def eval(self):
        return self.operands[0].exec()

    def __str__(self):
        return str(self.operands[0]) + ";"


class IfCommaStatement(Expr):
    def eval(self):
        if self.operands[0].exec():
            return self.operands[1].exec()

    def __str__(self):
        return str(self.operands[0]) + "," + str(self.operands[1]) + ";"


class Variable(Expr):
    def __init__(self):
        super(Variable, self).__init__()
        self.name = None  # 变量名
        self.qualifier = ''  # 修饰符

    def eval(self):
        return self.operands[0].exec()

    def __str__(self):
        result = ''
        if len(self.qualifier) > 0:
            result = self.qualifier + ' '
        # return result + self.name + self.operator + str(self.operands[0]) + ";"
        return str(self.operands[0])


class Program(Expr):
    def eval(self):
        for expr in self.operands:
            expr.exec()

    def __str__(self):
        result = ''
        for expr in self.operands:
            result = result + str(expr) + '\n'
        return result
