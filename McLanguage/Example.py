from McLanguage.Token import TokenDef, Token
from McLanguage.Lexer import McLexer, BaseLexer
from McLanguage.Transfer import Transfer


def close():
    print("正在执行close方法")
    return 5.0


def ref(a, b):
    print("正在执行ref方法")
    return 6.0


def high():
    print("正在执行high方法")
    return 14.0


def low():
    print("正在执行low方法")
    return 3.0


def open():
    print("正在执行open方法")
    return 4.0


def ifelse(condition, action1, action2):
    print("正在执行ifelse方法")
    if condition:
        return action1
    else:
        return action2


def sum(a, b):
    print("正在执行sum方法")
    return 100.0


def ma(a, b):
    import random
    print("正在执行ma方法")
    return random.random() * b


def count(a, b):
    print("正在执行count方法")
    return True


def select():
    print("正在执行select方法")


def cross(a, b):
    print("正在执行cross方法")
    return True


def bk(a):
    print("正在执行bk方法")

# def c():
#     print('c_test')

if __name__ == '__main__':
    mc_code = """
        // 模型1
        LC:=REF(CLOSE,1);//一个周期前的收盘价
        AA:=ABS(HIGH-LC);//最高价与一个周期前的收盘价的差值的绝对值
        BB:=ABS(LOW-LC);//最低价与一个周期前的收盘价的差值的绝对值
        CC:=ABS(HIGH-REF(LOW,1));//最高价与一个周期前的最低价的差值的绝对值
        DD:=ABS(LC-REF(OPEN,1));//一个周期前的收盘价与一个周期前的开盘价的差值的绝对值
        R:=IFELSE(AA>BB&&AA>CC,AA+BB/2+DD/4,IFELSE(BB>CC&&BB>AA,BB+AA/2+DD/4,CC+DD/4));//如果AA>BB&&AA>CC,R取值为AA+BB/2+DD/4,如果BB>CC&&BB>AA,R取值为BB+AA/2+DD/4,否则R取值为CC+DD/4
        X:=(CLOSE-LC+(CLOSE-OPEN)/2+LC-REF(OPEN,1));//最新价减去一个周期前的收盘价加上开盘价与最新价的二分之一，再加上一个周期前的收盘价与开盘价的差值
        SI:=16*X/R*MAX(AA,BB);
        ASI:SUM(SI,0);//从本地数据第一个数据开始求SI的总和

        // 模型2
        MA10^^MA(CLOSE,10);//定义10周期均线
        MA20^^MA(CLOSE,20);//定义20周期均线
        MA30^^MA(CLOSE,30);//定义30周期均线
        MA60^^MA(CLOSE,60);//定义60周期均线
        CROSS(MA10,MA20),BK(2);//10周期均线上穿20周期均线，买开仓2手
        CROSS(MA20,MA30),BK(1);//20周期均线上穿30周期均线，买开仓1手
        CROSS(MA30,MA60),BK(1);//30周期均线上穿60周期均线，买开仓1手 
    """
    print("-----麦语言程序如下-------------")
    print(mc_code)
    print("--------------------------------")

    print("----进行词元分析----------------")
    tokens = McLexer(mc_code).lex()
    for token in tokens:
        print(token)
    print("--------------------------------")

    print("---将麦语言转换为python语言------")
    python_code = Transfer(mc_code).python()
    print(python_code)
    print("---------------------------------")

    print("----执行转换出来的python语言-----")
    # exec(python_code)
    print("---------------------------------")
