# 当词元定义的正则表达式匹配到空字符串抛出的错误
class TokenMatchesEmptyStringError(Exception):
    '''
        @param regexp, str, 正则表达式字符串
    '''
    def __init__(self, regexp):
        message = 'token {!r} match the empty string'.format(regexp)
        super(TokenMatchesEmptyStringError, self).__init__(message)


# 当Lexer不能匹配到任何一个词元定义时抛出的错误
class NoMatchingTokenFoundError(Exception):
    '''
        @param line_num, int 行号
        @param line_pos, int 下标
        @param data, str, 匹配的字符串
    '''
    def __init__(self, line_num, line_pos, data):
        message = ('No token definition matched @ line {} position {}: {!r}'
                   .format(line_num, line_pos, data + '...'))
        super(NoMatchingTokenFoundError, self).__init__(message)

# 缺少分号的时候抛出的错误
class NoSemicolonError(Exception):
    def __init__(self):
        super(NoSemicolonError, self).__init__('Absence of a semicolon')


# 函数体错误
class FunctionStructureError(Exception):
    def __init__(self):
        super(FunctionStructureError, self).__init__('Parse the structure of function going wrong')

