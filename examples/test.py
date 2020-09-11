from datetime import datetime

theTime = '2019-12-20 10:22:00'
theTime = datetime.strptime(theTime, '%Y-%m-%d %H:%M:%S')
print(theTime)