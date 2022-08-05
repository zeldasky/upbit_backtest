from datetime import datetime, timedelta
import backTest as bt

date_str = '2018-01-01 00:00:00'
start = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')

# Long term test
time_gap = timedelta(days=90)
tic = ['60','240']
ticker = ['KRW-ETH']

up = bt.backTest()

for i in range(1): #Ticker
	for j in range(1): #Tic
		for k in range(2): #Range
			up.run_backTest(ticker[i], tic[j], start+time_gap*k, start+time_gap*(k+1), False)
			
# Short term test
time_gap = timedelta(days=7)
tic = ['3','15']
ticker = ['KRW-ETH']

up = bt.backTest()

for i in range(1): #Ticker
	for j in range(1): #Tic
		for k in range(2): #Range
			up.run_backTest(ticker[i], tic[j], start+time_gap*k, start+time_gap*(k+1), False)
