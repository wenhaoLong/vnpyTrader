from McLanguage.Lexer import McLexer
from McLanguage.Token import *
from McLanguage.Handler import *
from McLanguage.Exception import *

from vnpy.event import EventEngine, Event


class Transfer(object):
    """
        麦语言到python的转换器
    """
    HANDLERS = [
        NoteHandler(),  # 注释处理器
        EqualHandler(),  # 等于判断处理器
        NewlineHandler(),  # 换行符
        NotEqualHandler(),  # 不等于
        IfHandler(),  # if
        ThenHandler(),  # then
        BeginHandler(),  # begin
        EndHandler(),  # end
        SemicolonHandler(),  # 分号 ;
        IdentifierHandler(),  # 标记符处理
        AssignHandler(),  # 赋值符处理
        AndHandler(),  # 运运算处理
        OrHandler(),  # 或运算处理
        VariableHandler(),  # variable关键字处理
        CommaHandler(),  # 逗号处理
        LSBRHandler(),  # 左小括号处理
        RSBRHandler(),    # 右小括号处理
        # 最后一个处理器，必须为BaseHandler，会将token词元的值原样输出
        BaseHandler(),
    ]

    def __init__(self, text: str):
        self.tokens = McLexer(text, ignore_case=True).lex()
        self.index = 0

    def python(self):
        # 重置常量
        BaseHandler.INDENT_COUNT = 0
        BaseHandler.ARG_STR_COUNT = 0
        BaseHandler.PARENT_COUNT = 0
        # 先处理唯一的特殊情况，即condition, action
        # 将其转换为if condition then begin action end的语法
        # 这样麦语言都可以转换为顺序判断
        # 声明一个新的tokens列表
        new_tokens = []
        # 遍历检查词元
        while self.index < len(self.tokens):
            token = self.tokens[self.index]
            # 如果该token是逗号
            if token.token_def.name == 'COMMA':
                # 如果该逗号在括号内，即为普通的分隔符
                if self.is_in_bracket(self.index):
                    new_tokens.append(token)
                else:   # 如果该逗号不在括号内
                    condition = []   # 情况列表
                    action = []  # 动作列表
                    # 得到condition列表:new_tokens 出栈直至为空或者遇到换行、分号
                    while new_tokens:
                        condition_token = new_tokens.pop()
                        # 如果是换行或者分号
                        if condition_token.token_def.name == 'SEMICOLON'\
                                or condition_token.token_def.name == 'NEWLINE':
                            new_tokens.append(condition_token)  # 将换行或者分号重新压入栈
                            # 退出循环
                            break
                        condition.insert(0, condition_token)
                    # 得到action列表:向后寻找，直至走到尾或者遇到换行
                    j = self.index + 1
                    while j < len(self.tokens):
                        # 得到第j个词元
                        action_token = self.tokens[j]
                        # 将其添加到动作列表中
                        action.append(action_token)
                        j += 1
                        # 如果是分号
                        if action_token.token_def.name == 'SEMICOLON':
                            # 退出循环
                            break
                    # 判断action列表最后一个是否为分号，如果不是抛出错误
                    if action and not action[len(action) - 1].value == ';':
                        raise NoSemicolonError()
                    # 更新下标i
                    self.index = j
                    #  if 词元
                    if_token = Token(TokenDef.TOKEN_DEFS['IF'], 'if', 0, 0)
                    # then 词元
                    then_token = Token(TokenDef.TOKEN_DEFS['THEN'], 'then', 0, 0)
                    # begin 词元
                    begin_token = Token(TokenDef.TOKEN_DEFS['BEGIN'], 'begin', 0, 0)
                    # end 词元
                    end_token = Token(TokenDef.TOKEN_DEFS['END'], 'end', 0, 0)
                    # 按语法按序加入到new_tokens中
                    new_tokens.append(if_token)
                    for t in condition:
                        new_tokens.append(t)
                    new_tokens.append(then_token)
                    new_tokens.append(begin_token)
                    for t in action:
                        new_tokens.append(t)
                    new_tokens.append(end_token)
                    continue
            else:   # 如果该token不是逗号
                new_tokens.append(token)
            # 下标移动
            self.index += 1
        # 更新词元列表
        self.tokens = new_tokens
        # 重置下标
        self.index = 0
        # 结果字符串
        result = ""
        while self.index < len(self.tokens):
            # 得到第index个词元
            token = self.tokens[self.index]
            # print(token)
            # 匹配处理器
            for handler in self.__class__.HANDLERS:
                if handler.is_match(token):
                    result += handler.to_python(self.tokens, self.index)
                    break
            self.index += 1
        return result

    # 判断某个位置的token在不在括号内
    def is_in_bracket(self, idx):
        b = c = d = 0
        for i in range(len(self.tokens)):
            if i == idx:
                break
            token = self.tokens[i]
            if token.value == '(':
                b += 1
            if token.value == ')':
                b -= 1
            if token.value == '{':
                c += 1
            if token.value == '}':
                c -= 1
            if token.value == '[':
                d += 1
            if token.value == ']':
                d -= 1
        if b == 0 and c == 0 and d == 0:
            return False
        return True
