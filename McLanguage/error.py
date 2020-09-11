class BaseError(Exception):
    def __init__(self, token, is_None = False):
        if is_None:
            self.error_msg = 'Synatax error at Eof'
            super(BaseError, self).__init__(self.error_msg)
        else:
            # 异常数据发生在整个文本的下标位置
            self.lexpos = token.lexer.lexpos
            # 异常数据所在行
            self.lineno = token.lineno
            # 异常数据
            self.value = token.value[0]
            self.error_msg = '{}: Error occurred near {!r} at line {}'.format(
                self.__class__, self.value, self.lineno)
            super(BaseError, self).__init__(self.error_msg)


# 标记化错误
class TokenizerError(BaseError):
    pass


# 文法错误
class SynataxError(BaseError):
    pass

# 未定义变量
class UndefinedVariableError(BaseError):
    pass
