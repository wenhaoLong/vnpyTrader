# 保留字
reserved = (
    "IF",
    "THEN",
    "BEGIN",
    "END",
    "VARIABLE",
)

# 系统变量
system_variable = (
    "O",    # 开盘价
    "C",    # 收盘价
    "H",    # 最高价
    "L",    # 最低价
    "V",
)

# 操作符
operator = (
    "PLUS",    # 加
    "MINUS",    # 减
    "TIMES",     # 乘
    "DIVIDE",   # 除
    "AND",  # 与
    "OR",   # 或
    "EQ",   # equal, 等于
    "NE",   # not equal, 不等于
    "ASSIGN",   # 赋值
    "LT",   # less than, 小于
    "GT",   # greater than, 大于
    "LE",   # less than and equal, 小于等于
    "GE",   # greater than and equal, 大于等于
)

# 限界符
delimiter = (
    "COMMA",  # 逗号：':'
    "SEMI",    # 分号：';'
    "PERIOD",  # 句号：'.'
    "COLON",    # 冒号：':'
    "LPAREN",   # 左小括号: '('
    "RPAREN",   # 右小括号: ')'
    "LBRACKET",  # 左中括号：'['
    "RBRACKET",  # 右中括号：']'
    "LBRACE",   # 左大括号：'{'
    "RBRACE",   # 右大括号：'}'
)

# 内置函数
function = (
    'TEST',          # -1 测试函数
    'LOG',                 # 0 通用LOG
    'HIGH',                # 1
    'OPEN',                # 1
    'LOW',                 # 1
    'CLOSE',               # 1
    'VOL',                 # 1
    'ASK1',                # 2
    'ASK1VOL',             # 3
    'BID1',                # 4
    'BID1VOL',             # 5
    'BK',                  # 6
    'SK',                  # 7
    'BP',                  # 8
    'SP',                  # 9
    'ABS',                 # 10
    'AUTOFILTER',          # 11
    'AVAILABLE_OPI',       # 12
    'BARPOS',              # 13
    'BARSCOUNT',           # 14
    'BARSLAST',            # 15
    'BARSLASTCOUNT',       # 16
    'BARSSINCE',           # 17
    'BARSSINCEN',          # 18
    'BETWEEN',             # 19
    'BKHIGH',              # 20
    'BKLOW',               # 21
    'BKVOL1',              # 22
    'SKVOL1',              # 23
    'BKVOL',               # 24
    'SKVOL',               # 25
    'CLOSESEC',            # 26
    'CONDBARS',            # 27
    'COUNT',               # 28
    'COUNTSIG',            # 29
    'CROSSUP',              # 30
    'CROSSDOWN',            # 30
    'DAYBARPOS',           # 31
    'DAYTRADE',            # 32
    'ENTRYSIG_PLACE',      # 33
    'ENTRYSIG_PRICE',      # 34
    'ENTRYSIG_VOL',         # 35
    'EVERY',               # 36
    'EXIST',               # 37
    'EXITSIG_PLACE',       # 38
    'EXITSIG_PRICE',       # 39
    'EXITSIG_VOL',         # 40
    'FEE',                 # 41
    'FILTER',              # 42
    'HHV',                 # 43
    'HV',                  # 44
    'HHVBARS',             # 45
    # 'IF',                       # 46,if为python关键词
    'INITMONEY',           # 47
    'INTPART',             # 48
    'ISLASTBAR',           # 49
    'ISLASTBK',            # 50
    'ISLASTSP',            # 51
    'ISLASTCLOSEOUT',      # 52
    'KLINESIG',            # 53
    'LAST',                # 54
    'LASTOFFSETPROFIT',    # 55
    'LASTSIG',             # 56
    'LLV',                 # 57
    'LV',                  # 58
    'LLVBARS',             # 59
    'LOOP2',               # 60
    'MAX',                 # 61
    'MA',                  # 62
    'MIN',                 # 63
    'MINUTE',              # 64
    'MINPRICED',           # 65
    'MONEY',               # 66
    'MONEYRATIO',          # 67
    'MONEYREAL',           # 68
    'MONEYTOT',            # 69
    'MULTSIG',             # 70
    # 'NOT',                 # 71，not 为python关键词
    'OFFSETPROFIT',        # 72
    'OPENMINUTE',          # 73
    'PROFIT',              # 74
    'PEAK ',               # 75
    'PEAKBARS',            # 76
    'REF',                 # 77
    'REFSIG_PLACE',        # 78
    'REFSIG_PRICE',        # 79
    'REFSIG_VOL',          # 80
    'REFX',                # 81
    'ROUND',               # 82
    'STOCKDIVD',           # 83
    'SETEXPIREDATE',       # 84
    'SETTLE',              # 85
    'SETDEALPERCENT',      # 86
    'SIGNUM',              # 87
    'SIGVOL',              # 88
    'SUM',                 # 89
    'SUMBARS',             # 90
    'TIME',                # 91
    'TMAXWIN',             # 92
    'TMAXLOSS',            # 93
    'TMAXSEQLOSS',         # 94
    'TMAXSEQWIN',          # 95
    'TNUMSEQLOSS',         # 96
    'TNUMSEQWIN',          # 97
    'TRADE_AGAIN',         # 98
    'TRADE_REF',           # 99
    'TROUGHBARS',          # 100
    'TSEQLOSS',           # 101
    'TSEQWIN',             # 102
    'UNIT',                # 103
    'VALUEWHEN',           # 104
    'VOLMARGIN',           # 105
    'WAVEPEAK',            # 106
    'CALL',                # 107
    # 'IMPORT',              # 108 IMPORT 为python关键词
    'CALL_PLUS',           # 109
    'SLEEP',    # 110
    'IFELSE',
    'NOT',
    'ISUP',
    'SELECT',
    'CROSS',
    'IFF' ,      # IF 的替代
    'NOTT',       # NOT的替代
    'STATE'
)
