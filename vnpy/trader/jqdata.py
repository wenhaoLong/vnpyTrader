
from datetime import datetime, timedelta
from typing import List
from math import isnan

from urllib3.exceptions import InsecureRequestWarning

from .constant import Exchange, Interval
from .object import BarData, HistoryRequest

from pathlib import Path
from vnpy.trader.utility import CTPLoader

from vnpy.trader.setting import SETTINGS
import time
import requests,json
import sys
import pandas as pd
from io import StringIO


INTERVAL_VT2RQ = {
    Interval.MINUTE: "1m",
    Interval.FIVEMINUTE: "5m",
    Interval.FIFTEENMINUTE: "15m",
    Interval.HOUR: "60m",
    Interval.DAILY: "d",
    Interval.WEEKLY: "1w",
}

INTERVAL_ADJUSTMENT_MAP = {
    Interval.MINUTE: timedelta(minutes=1),
    Interval.HOUR: timedelta(hours=1),
    Interval.DAILY: timedelta()         # no need to adjust for daily bar
}
url="https://dataapi.joinquant.com/apis"

class JqdataClient:

    def __init__(self):
        self.certificate()
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        self.nowBar = None

    def certificate(self):
        account = SETTINGS["jqdata_account"]
        password = SETTINGS["jqdata_password"]


        # auth('15680977680', '977680')  # ID是申请时所填写的手机号；Password为聚宽官网登录密码，新申请用户默认为手机号后6位
        try:
            self.token = self.get_token(account,password)  # ID是申请时所填写的手机号；Password为聚宽官网登录密码，新申请用户默认为手机号后6位
            print(account)
            print(password)
        except:
            if account == None or password == None:
                print("未输入jqdata账号和密码")
            else:
                print("jqdata账号或密码错误")
        finally:
            self.token = self.get_token('15680977680','977680')
        print("用户jqdata凭证标识号为"+self.token+"，当天有效")


    def to_jq_symbol(self, symbol: str, exchange: Exchange):
        """
        CZCE product of RQData has symbol like "TA1905" while
        vt symbol is "TA905.CZCE" so need to add "1" in symbol.
        """

        if exchange == Exchange.CFFEX:
            jq_symbol = f"{symbol}.CCFX"
        elif exchange == Exchange.SHFE:
            jq_symbol = f"{symbol}.XSGE"
        elif exchange == Exchange.DCE:
            jq_symbol = f"{symbol}.XDCE"
        elif exchange == Exchange.INE:
            jq_symbol = f"{symbol}.XINE"
        elif exchange == Exchange.CZCE:
            for count, word in enumerate(symbol):
                if word.isdigit():
                    break

            # Check for index symbol
            time_str = symbol[count:]
            if time_str in ["88", "888", "99"]:
                return f"{symbol}.XZCE"

            # noinspection PyUnboundLocalVariable
            product = symbol[:count]
            year = symbol[count]
            month = symbol[count + 1:]

            if year == "9":
                year = "1" + year
            else:
                year = "2" + year

            return f"{product}{year}{month}.XZCE"

        return jq_symbol.upper()

    def query_history(self, req: HistoryRequest):
        symbol = req.symbol
        exchange = req.exchange
        interval = req.interval
        count = req.count

        end = datetime.now()
        try:
            self.token = self.get_token(SETTINGS["jqdata_account"], SETTINGS["jqdata_password"])
        except:
            self.token = self.get_token('15680977680', '977680')
        jq_symbol = self.to_jq_symbol(symbol, exchange)
        jq_interval = INTERVAL_VT2RQ.get(interval)
        if not jq_interval:
            return None
        if jq_interval == "d":
            jq_interval = "1d"
        body = {
            "method": "get_bars",
            "token": self.token,
            "code": jq_symbol,
            "count": count,
            "unit": jq_interval,
        }

        num_body = {
            "method": "get_query_count",
            "token":self.token
        }
        #print(self.get_data(requests.post(url, data=json.dumps(num_body))))

        bars_df = self.get_data(requests.post(url, data=json.dumps(body)))

        # bars_df = self.get_bars_by_http(jq_symbol, count=count, unit=jq_interval,
        #                    fields=['date', 'open', 'close', 'high', 'low', 'volume', 'money', 'open_interest'],
        #                    include_now=True, end_dt=end)
        bar_list: List[BarData] = []
        self.time = time.strftime('%H:%M:%S', time.localtime(time.time()))
        # 保持与trade.datetime格式一致，因为需要比较
        self.strategy_start_time = time.strftime('%Y%m%d %H:%M:%S', time.localtime(time.time()))
        if bars_df is not None:
            for ix, row in bars_df.iterrows():

                if row["date"] < self.strategy_start_time:
                    if jq_interval == '1d' or jq_interval == '1w' or jq_interval == '1M':
                        row['date'] = datetime.strptime(str(row['date']) + " 00:00:00", "%Y-%m-%d\n%H:%M:%S")
                    else:
                        row['date'] = datetime.strptime(str(row['date']) + ":00", "%Y-%m-%d\n%H:%M:%S")
                    # @Time    : 2019-10-25
                    # @Author  : Wangyongchang
                    # 1m的datetime字段为pandas的Timestamp类型
                    # 存入数据库报错
                    # row["date"].to_pydatetime()转为datetime类型
                    bar = BarData(
                        symbol=symbol,
                        exchange=exchange,
                        interval=interval,
                        datetime=row["date"] if(row["date"].__class__ == datetime) else row["date"].to_pydatetime(),
                        open_price=row["open"],
                        high_price=row["high"],
                        low_price=row["low"],
                        close_price=row["close"],
                        volume=row["volume"],
                        gateway_name="JQ"
                    )
                    bar_list.append(bar)
        #self.nowBar = bar_list[-2]
        #bar_list = bar_list[:-1]
        #print(bars_df[-1])
        #print(bars_df)
        return bar_list, bars_df

    # def query_history_kline(self, req: HistoryRequest):
    #     """
    #     Query history bar data from RQData.
    #     """
    #     symbol = req.symbol
    #     exchange = req.exchange
    #     interval = req.interval
    #     count = req.count
    #     end = datetime.now()
    #
    #     jq_symbol = self.to_jq_symbol(symbol, exchange)
    #     jq_interval = INTERVAL_VT2RQ.get(interval)
    #     if not jq_interval:
    #         return None
    #     if jq_interval == "d":
    #         jq_interval = "1d"
    #     bars_df = get_bars(jq_symbol, count=count, unit=jq_interval, fields=['date', 'open', 'close', 'high', 'low', 'volume', 'money', 'open_interest'], include_now=True, end_dt=end)
    #     bar_list: List[BarData] = []
    #
    #     if bars_df is not None:
    #         for ix, row in bars_df.iterrows():
    #             if jq_interval == '1d' or jq_interval == '1w' or jq_interval == '1M':
    #                 row['date'] = datetime.strptime(str(row['date']) + " 00:00:00", "%Y-%m-%d\n%H:%M:%S")
    #
    #             # @Time    : 2019-10-25
    #             # @Author  : Wangyongchang
    #             # 1m的datetime字段为pandas的Timestamp类型
    #             # 存入数据库报错
    #             # row["date"].to_pydatetime()转为datetime类型
    #             bar = BarData(
    #                 symbol=symbol,
    #                 exchange=exchange,
    #                 interval=interval,
    #                 datetime=row["date"] if(row["date"].__class__ == datetime) else row["date"].to_pydatetime(),
    #                 open_price=row["open"],
    #                 high_price=row["high"],
    #                 low_price=row["low"],
    #                 close_price=row["close"],
    #                 volume=row["volume"],
    #                 gateway_name="JQ"
    #             )
    #             bar_list.append(bar)
    #     return bar_list, bars_df

    def get_token(self,mob,pwd):
        body = {
            "method": "get_token",
            "mob": mob,  # mob是申请JQData时所填写的手机号
            "pwd": pwd,  # Password为聚宽官网登录密码，新申请用户默认为手机号后6位
        }
        return requests.post(url, data=json.dumps(body)).text




    # @Time    : 2019-10-25
    # @Author  : Wangyongchang
    # 回测的独立的数据接口，有开始时间和结束时间

    def query_history_cta(self, req: HistoryRequest):
        """
        Query history bar data from RQData.
        """
        symbol = req.symbol
        exchange = req.exchange
        interval = req.interval
        count = req.count
        start = req.start.strftime('%Y-%m-%d %H:%M:%S')

        end = req.end.strftime('%Y-%m-%d %H:%M:%S')


        try:
            self.token = self.get_token(SETTINGS["jqdata_account"], SETTINGS["jqdata_password"])
        except:
            self.token = self.get_token('15680977680', '977680')
        jq_symbol = self.to_jq_symbol(symbol, exchange)
        jq_interval = INTERVAL_VT2RQ.get(interval)
        if not jq_interval:
            return None
        if jq_interval == "d":
            jq_interval = "1d"
        body = {
            "method": "get_bars_period",
            "token": self.token,
            "code": jq_symbol,
            "date": start,
            "end_date": end,
            "unit": jq_interval,
        }


        #print(self.get_data(requests.post(url, data=json.dumps(body))))

        bars_df = self.get_data(requests.post(url, data=json.dumps(body)))

        data: List[BarData] = []
        if bars_df is not None:
            for ix, row in bars_df.iterrows():

                # if jq_interval == '1d' or jq_interval == '1w' or jq_interval == '1M':
                #     row['date'] = datetime.strptime(str(row['date']) + " 00:00:00", "%Y-%m-%d\n%H:%M:%S")
                # else:
                #     row['date'] = datetime.strptime(str(row['date']) + ":00", "%Y-%m-%d\n%H:%M:%S")
                # 过滤空值
                if not (isnan(row["open"]) or isnan(row["high"]) or isnan(row["low"]) or isnan(row["close"]) or isnan(row["volume"])):
                    bar = BarData(
                        symbol=symbol,
                        exchange=exchange,
                        interval=interval,
                        datetime=row["date"] if(row["date"].__class__ == datetime) else datetime.strptime(row["date"],'%Y-%m-%d %H:%M'),
                        open_price=row["open"],
                        high_price=row["high"],
                        low_price=row["low"],
                        close_price=row["close"],
                        volume=row["volume"],
                        gateway_name="JQ"
                    )
                    data.append(bar)

        return data

    def get_data(self, response):  # 数据处理函数,处理csv字符串函数
        '''格式化数据为DataFrame'''
        return pd.read_csv(StringIO(response.text))

class readCTP:
    def __int__(self):
        super().__init__()

    def readFile(self,symbol):
        #print(symbol)
        # 吨数加载器
        loader = CTPLoader()
        running_path = Path(sys.argv[0]).parent
        function_file = running_path.joinpath("CTP.xlsx")
        # 加载函数描述文件
        loader.load_excel(function_file)
        # 得到实际内容
        self.function_dict = loader.contents
        self.function_names = loader.names
        #print(self.function_dict[symbol]["VolumeMultiple"])
        return self.function_dict[symbol]["VolumeMultiple"]



jqdata_client = JqdataClient()