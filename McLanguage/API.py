"""
    管理麦语言的函数和全局变量
"""

class FuncManager(object):
    """
        函数管理器
    """
    # key是函数名，全大写;value是参数是否字符串化
    # 注意:目前不允许在参数字符化的函数内再调用参数字符化的函数，否则会抛出语法错误
    FUNCTIONS = {
        'TEST': True,          # -1 测试函数
        'LOG': False,                 # 0 通用LOG
        'H': False,                   # 1
        'O': False,                   # 1
        'L': False,                   # 1
        'C': False,                   # 1
        'V': False,                   # 1
        'HIGH': False,                # 1
        'OPEN': False,                # 1
        'LOW': False,                 # 1
        'CLOSE': False,               # 1
        'VOL': False,                 # 1
        'ASK1': False,                # 2
        'ASK1VOL': False,             # 3
        'BID1': False,                # 4
        'BID1VOL': False,             # 5
        'BK': False,                  # 6
        'SK': False,                  # 7
        'BP': False,                  # 8
        'SP': False,                  # 9
        'ABS': False,                 # 10
        'AUTOFILTER': False,          # 11
        'AVAILABLE_OPI': False,       # 12
        'BARPOS': False,              # 13
        'BARSCOUNT': False,           # 14
        'BARSLAST': True,             # 15
        'BARSLASTCOUNT': True,        # 16
        'BARSSINCE': True,            # 17
        'BARSSINCEN': True,          # 18
        'BETWEEN': False,             # 19
        'BKHIGH': False,              # 20
        'BKLOW': False,               # 21
        'BKVOL1': False,              # 22
        'SKVOL1': False,              # 23
        'BKVOL': False,               # 24
        'SKVOL': False,               # 25
        'CLOSESEC': False,            # 26
        'CONDBARS': False,            # 27
        'COUNT': True,               # 28
        'COUNTSIG': False,            # 29
        'CROSSUP': True,              # 30
        'CROSSDOWN': True,            # 30
        'CROSS': False,  # 30
        'DAYBARPOS': False,           # 31
        'DAYTRADE': False,            # 32
        'ENTRYSIG_PLACE': True,      # 33
        'ENTRYSIG_PRICE': True,      # 34
        'ENTRYSIG_VOL': True,         # 35
        'EVERY': False,               # 36
        'EXIST': False,               # 37
        'EXITSIG_PLACE': True,       # 38
        'EXITSIG_PRICE': True,       # 39
        'EXITSIG_VOL': True,         # 40
        'FEE': False,                 # 41
        'FILTER': False,              # 42
        'HHV': True,                 # 43
        'HV': True,                  # 44
        'HHVBARS': True,             # 45
        'IFF':False,                       # 46,if为python关键词
        'INITMONEY': False,           # 47
        'INTPART': False,             # 48
        'ISLASTBAR': False,           # 49
        'ISLASTBK': False,            # 50
        'ISLASTSP': False,            # 51
        'ISLASTCLOSEOUT': False,      # 52
        'KLINESIG': False,            # 53
        'LAST': True,                # 54
        'LASTOFFSETPROFIT': False,    # 55
        'LASTSIG': False,             # 56
        'LLV': True,                 # 57
        'LV': True,                  # 58
        'LLVBARS': True,             # 59
        'LOOP2': False,               # 60
        'MAX': False,                 # 61
        'MA': True,                  # 62
        'MIN': False,                 # 63
        'MINUTE': False,              # 64
        'MINPRICED': False,           # 65
        'MONEY': False,               # 66
        'MONEYRATIO': False,          # 67
        'MONEYREAL': False,           # 68
        'MONEYTOT': False,            # 69
        'MULTSIG': False,             # 70
        # 'NOT',                      # 71，not 为python关键词
        'OFFSETPROFIT': False,        # 72
        'OPENMINUTE': False,          # 73
        'PROFIT': False,              # 74
        'PEAK ': False,               # 75
        'PEAKBARS': False,            # 76
        'REF': True,                 # 77
        # @author hengxincheung
        # @note 开启REFSIG_PLACE函数的参数字符化功能
        'REFSIG_PLACE': True,        # 78
        'REFSIG_PRICE': True,        # 79
        'REFSIG_VOL': True,          # 80
        'REFX': True,                # 81
        'ROUND': False,               # 82
        'STOCKDIVD': False,           # 83
        'SETEXPIREDATE': False,       # 84
        'SETTLE': False,              # 85
        'SETDEALPERCENT': False,      # 86
        'SIGNUM': False,              # 87
        'SIGVOL': False,              # 88
        'SUM': True,                 # 89
        'SUMBARS': True,             # 90
        'TIME': False,                # 91
        'TMAXWIN': False,             # 92
        'TMAXLOSS': False,            # 93
        'TMAXSEQLOSS': False,         # 94
        'TMAXSEQWIN': False,          # 95
        'TNUMSEQLOSS': False,         # 96
        'TNUMSEQWIN': False,          # 97
        'TRADE_AGAIN': False,         # 98
        'TRADE_REF': False,           # 99
        'TROUGHBARS': False,          # 100
        'TSEQLOSS': False,           # 101
        'TSEQWIN': False,             # 102
        'UNIT': False,                # 103
        'VALUEWHEN': False,           # 104
        'VOLMARGIN': False,           # 105
        'WAVEPEAK': False,            # 106
        'CALL': True,                # 107
        # 'IMPORT',              # 108 IMPORT 为python关键词
        'CALL_PLUS': False,           # 109
        'SLEEP': False, # 110
    }
