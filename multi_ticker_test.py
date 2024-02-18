import logging
from datetime import datetime, timedelta
import main as bt

date_str = '2019-01-01 00:00:00'
start = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')

time_gap = timedelta(days=30)
tic = ['15']
ticker = ['KRW-ETH','KRW-ETC']

up = bt.backTest()

for i in range(1,2): #Ticker
	total_profit = 0
	for j in range(1): #Tic
		for k in range(16): #Range
			total_profit =  total_profit + up.run_backTest(ticker[i], tic[j], start+time_gap*k, start+time_gap*(k+1), False)

	logging.info(f"\n======== Total Profit =========")
	logging.info(f"{round(total_profit, 2)} %")
	logging.info(f"============================\n")
