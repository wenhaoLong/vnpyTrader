import datetime
from vnpy.trader.object import TickData
from vnpy.trader.constant import Exchange,Interval
from pandas import DataFrame

tick_list = [TickData(gateway_name='CTP', symbol='T2003', exchange=Exchange('CFFEX'), datetime=datetime.datetime(2019, 9, 25, 14, 40, 30), name='10年国债2003', volume=196, open_interest=2247.0, last_price=98.16, last_volume=0, limit_up=100.045, limit_down=96.125, open_price=98.15, high_price=98.18, low_price=98.03, pre_close=98.085, bid_price_1=98.145, bid_price_2=0, bid_price_3=0, bid_price_4=0, bid_price_5=0, ask_price_1=98.165, ask_price_2=0, ask_price_3=0, ask_price_4=0, ask_price_5=0, bid_volume_1=7, bid_volume_2=0, bid_volume_3=0, bid_volume_4=0, bid_volume_5=0, ask_volume_1=2, ask_volume_2=0, ask_volume_3=0, ask_volume_4=0, ask_volume_5=0),
TickData(gateway_name='CTP', symbol='T2003', exchange=Exchange('CFFEX'), datetime=datetime.datetime(2019, 9, 25, 14, 40, 41), name='10年国债2003', volume=196, open_interest=2247.0, last_price=98.16, last_volume=0, limit_up=100.045, limit_down=96.125, open_price=98.15, high_price=98.18, low_price=98.03, pre_close=98.085, bid_price_1=98.145, bid_price_2=0, bid_price_3=0, bid_price_4=0, bid_price_5=0, ask_price_1=98.165, ask_price_2=0, ask_price_3=0, ask_price_4=0, ask_price_5=0, bid_volume_1=8, bid_volume_2=0, bid_volume_3=0, bid_volume_4=0, bid_volume_5=0, ask_volume_1=2, ask_volume_2=0, ask_volume_3=0, ask_volume_4=0, ask_volume_5=0),
TickData(gateway_name='CTP', symbol='T2003', exchange=Exchange('CFFEX'), datetime=datetime.datetime(2019, 9, 25, 14, 40, 41, 500000), name='10年国债2003', volume=196, open_interest=2247.0, last_price=98.16, last_volume=0, limit_up=100.045, limit_down=96.125, open_price=98.15, high_price=98.18, low_price=98.03, pre_close=98.085, bid_price_1=98.145, bid_price_2=0, bid_price_3=0, bid_price_4=0, bid_price_5=0, ask_price_1=98.165, ask_price_2=0, ask_price_3=0, ask_price_4=0, ask_price_5=0, bid_volume_1=3, bid_volume_2=0, bid_volume_3=0, bid_volume_4=0, bid_volume_5=0, ask_volume_1=2, ask_volume_2=0, ask_volume_3=0, ask_volume_4=0, ask_volume_5=0),
TickData(gateway_name='CTP', symbol='T2003', exchange=Exchange('CFFEX'), datetime=datetime.datetime(2019, 9, 25, 14, 40, 46), name='10年国债2003', volume=198, open_interest=2245.0, last_price=98.145, last_volume=0, limit_up=100.045, limit_down=96.125, open_price=98.15, high_price=98.18, low_price=98.03, pre_close=98.085, bid_price_1=98.145, bid_price_2=0, bid_price_3=0, bid_price_4=0, bid_price_5=0, ask_price_1=98.165, ask_price_2=0, ask_price_3=0, ask_price_4=0, ask_price_5=0, bid_volume_1=1, bid_volume_2=0, bid_volume_3=0, bid_volume_4=0, bid_volume_5=0, ask_volume_1=4, ask_volume_2=0, ask_volume_3=0, ask_volume_4=0, ask_volume_5=0),
TickData(gateway_name='CTP', symbol='T2003', exchange=Exchange('CFFEX'), datetime=datetime.datetime(2019, 9, 25, 14, 40, 46, 500000), name='10年国债2003', volume=198, open_interest=2245.0, last_price=98.145, last_volume=0, limit_up=100.045, limit_down=96.125, open_price=98.15, high_price=98.18, low_price=98.03, pre_close=98.085, bid_price_1=98.145, bid_price_2=0, bid_price_3=0, bid_price_4=0, bid_price_5=0, ask_price_1=98.165, ask_price_2=0, ask_price_3=0, ask_price_4=0, ask_price_5=0, bid_volume_1=4, bid_volume_2=0, bid_volume_3=0, bid_volume_4=0, bid_volume_5=0, ask_volume_1=4, ask_volume_2=0, ask_volume_3=0, ask_volume_4=0, ask_volume_5=0),
TickData(gateway_name='CTP', symbol='T2003', exchange=Exchange('CFFEX'), datetime=datetime.datetime(2019, 9, 25, 14, 40, 50), name='10年国债2003', volume=198, open_interest=2245.0, last_price=98.145, last_volume=0, limit_up=100.045, limit_down=96.125, open_price=98.15, high_price=98.18, low_price=98.03, pre_close=98.085, bid_price_1=98.145, bid_price_2=0, bid_price_3=0, bid_price_4=0, bid_price_5=0, ask_price_1=98.165, ask_price_2=0, ask_price_3=0, ask_price_4=0, ask_price_5=0, bid_volume_1=6, bid_volume_2=0, bid_volume_3=0, bid_volume_4=0, bid_volume_5=0, ask_volume_1=3, ask_volume_2=0, ask_volume_3=0, ask_volume_4=0, ask_volume_5=0),
TickData(gateway_name='CTP', symbol='T2003', exchange=Exchange('CFFEX'), datetime=datetime.datetime(2019, 9, 25, 14, 40, 51), name='10年国债2003', volume=198, open_interest=2245.0, last_price=98.145, last_volume=0, limit_up=100.045, limit_down=96.125, open_price=98.15, high_price=98.18, low_price=98.03, pre_close=98.085, bid_price_1=98.145, bid_price_2=0, bid_price_3=0, bid_price_4=0, bid_price_5=0, ask_price_1=98.165, ask_price_2=0, ask_price_3=0, ask_price_4=0, ask_price_5=0, bid_volume_1=6, bid_volume_2=0, bid_volume_3=0, bid_volume_4=0, bid_volume_5=0, ask_volume_1=2, ask_volume_2=0, ask_volume_3=0, ask_volume_4=0, ask_volume_5=0)]

bar_list = []

for ix, tick in enumerate(tick_list):
    bar_dict = {}
    bar_dict["gateway_name"] = tick.gateway_name
    bar_dict["symbol"] = tick.symbol
    bar_dict["exchange"] = tick.exchange
    bar_dict["datetime"] = tick.datetime
    bar_dict["interval"] = Interval("1m")
    bar_dict["volume"] = tick.volume
    bar_dict["open_interest"] = tick.open_interest
    bar_dict["open_price"] = tick.open_price
    bar_dict["high_price"] = tick.high_price
    bar_dict["low_price"] = tick.low_price
    bar_dict["close_price"] = tick.last_price
    bar_list.append(bar_dict)

bar_df = DataFrame.from_dict(bar_list).set_index("datetime")

print(bar_df)