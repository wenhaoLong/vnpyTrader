"""
*@ my语言映射为python函数
*@ date 2019.9.27
*@ Leoliu
"""

# key为对应my语言的函数名称，value为对应的python语言的函数的名称

my_py_dic = {
    'H': 'high',
    'L': 'low',
    'O': 'open',
    'C': 'close',
    'V': 'volume',
    'LOG': 'log',
    'TEST': 'test_tt',
}

def my_py_map(dic_key):
    return my_py_dic[dic_key]
