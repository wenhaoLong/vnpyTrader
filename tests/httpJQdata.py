import requests,json
import sys
import pandas as pd
from io import StringIO
import numpy as np
from datetime import datetime, timedelta
url="https://dataapi.joinquant.com/apis"

def get_token():
    # body={
    #     "method": "get_token",
    #     "mob": "15680977680",  #mob是申请JQData时所填写的手机号
    #     "pwd": "977680",  #Password为聚宽官网登录密码，新申请用户默认为手机号后6位
    # }
    body={
        "method": "get_token",
        "mob": "15680977680",  #mob是申请JQData时所填写的手机号
        "pwd": "977680",  #Password为聚宽官网登录密码，新申请用户默认为手机号后6位
    }
    return requests.post(url, data = json.dumps(body)).text

def get_data(response):   # 数据处理函数,处理csv字符串函数
    '''格式化数据为DataFrame'''
    return pd.read_csv(StringIO(response.text))

token = get_token()

# def http_get_bars():
#     body = {
#     "method": "get_bars",
#     "token": token,
#     "code": "600000.XSHG",
#     "count": 10,
#     "unit": "5m",
#     }
#     return  get_data(requests.post(url, data = json.dumps(body)))#.set_index('code')

def http_get_query_count():
    body = {
        "method": "get_query_count",
        "token": token,

    }
    return get_data(requests.post(url, data=json.dumps(body)))  # .set_index('code')

def http_get_security_info():
    body = {
        "method": "get_security_info",
        "token": token,
        "code": "502050.XSHG"
    }
    return get_data(requests.post(url, data=json.dumps(body)))  # .set_index('code')

# data = http_get_bars()
# np_data = np.array(data)
# data_list = np_data.tolist()
# for ix,row in data.iterrows():
#     print((row["date"]))
    #row['date'] = datetime.strptime(str(row['date']) + ":00", "%Y-%m-%d\n%H:%M:%S")

info = http_get_security_info()
print(info)

count = http_get_query_count()
print(count)