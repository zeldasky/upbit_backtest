import tick_db as db
import math
import rsi_sample as dw
import sys
import logging
from datetime import datetime, timedelta

# logging.basicConfig(level=logging.DEBUG)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
my_format = logging.Formatter('%(message)s')
ch.setFormatter(my_format)

LOGGER = logging.getLogger()
LOGGER.addHandler(ch)
LOGGER.setLevel(logging.INFO)

buy_order = list()
sell_order = list()
first = 1000000000
seed = 1000000000
min_price = 0
max_price = 0
coin_num = 0

prev = 0
cur = 0
min_rate = 1.01
max_rate = 1.01
oversold_rsi = 20
overbought_rsi = 80

start_price = 0
end_price = 0
order_price = 0
total_profit = 0
display_chart = False

class backTest:
	def display_account(self, title, tics, start_time, end_time):

		logging.info("\n-----------------------------------------------------------------------------")
		logging.info(f"Ticker, Tic: {title}, {tics}")
		logging.info(f"Range : {start_time} ~ {end_time}")
		logging.info("Start Seed: ")
		logging.info("{0:>30,} KRW".format(round(first)))
		logging.info("Stop Seed: ")
		logging.info("{0:>30,} KRW".format(round(seed)))
		logging.info("Start Price: ")
		logging.info("{0:>30,} KRW".format(round(start_price)))
		logging.info("End Price: ")
		logging.info("{0:>30,} KRW".format(round(end_price)))
		logging.info("Coin Price Change Rate: ")
		logging.info("(Start - End price) ")
		logging.info("{0:>30,} %".format(round(((end_price-start_price)*100/start_price))))
		logging.info("Trading Profit Rate : ")
		logging.info("{0:>30,} %".format(round((seed-first)*100/first)))
		logging.info("-----------------------------------------------------------------------------\n")
		return round((seed-first)*100/first,2)

	def sell_condition(self,price):
		ret = False
		global max_price
		if max_price == 0:
			max_price = price
		elif max_price*max_rate > price:
			max_price = price
			ret = True
		else:
			max_price = price
		logging.debug(f"sell condition: { max_price} - {price}")
		return ret

	def buy_condition(self, price):
		ret = False
		global min_price
		if min_price == 0:
			min_price = price
		elif min_price*min_rate < price:
			min_price = price
			ret = True
		else:
			min_price = price
		logging.debug(f"buy condition: {min_price} - {price}")
		return ret

	def sell(self, price, force):
		global seed, coin_num
		if coin_num > 0:	
			if force == True:
				sell = price*coin_num 
				seed += sell
				logging.debug(f"[Sell] price: {price}  - number:  {coin_num} - coin Seed: {price*coin_num}")
				logging.debug(f"[Sell] Seed: {seed}")
				coin_num = 0
				order_price = price
				sell_order.append(order_price)
				buy_order.append(-1)
			else:
				if self.sell_condition(price):
					sell = price*coin_num 
					seed += sell
					logging.debug(f"[Sell] price: {price}  - number:  {coin_num} - coin Seed: {price*coin_num}")
					logging.debug(f"[Sell] Seed: {seed}")
					coin_num = 0
					order_price = price
					sell_order.append(order_price)
					buy_order.append(-1)
				else:
					sell_order.append(-1)
					buy_order.append(-1)
		else:
			sell_order.append(-1)
			buy_order.append(-1)

	def buy(self, price, force):
		global seed, coin_num
		if seed > price:
			if force == True:
				buy_num = int(seed/price)
				coin_num += buy_num
				seed -= (buy_num*price) 
				order_price = price
				buy_order.append(order_price)
				sell_order.append(-1)
				logging.debug(f"[Buy] price: {price}  - number:  {coin_num} - coin Seed: {price*coin_num}")
				logging.debug(f"[Buy] Seed: {seed}")
			else:
				if self.buy_condition(price):
					buy_num = int(seed/price)
					coin_num += buy_num
					seed -= (buy_num*price) 
					order_price = price
					buy_order.append(order_price)
					sell_order.append(-1)
					logging.debug(f"[Buy] price: {price}  - number:  {coin_num} - coin Seed: {price*coin_num}")
					logging.debug(f"[Buy] Seed: {seed}")
				else:
					buy_order.append(-1)
					sell_order.append(-1)
		else:
			buy_order.append(-1)
			sell_order.append(-1)

	def run_backTest(self, ticker, tic, start, end, display_chart):
		global seed, first, coin_num, start_price, end_price, min_price, max_price
		seed = first
		coin_num =0

		sell_order.clear()
		buy_order.clear()
		data = db.make_tick_db(start, end, ticker, tic)
		# logging.info(data)
		for i in range(len(data)):
			rsi_k = data.iloc[i]['rsi_k']
			rsi_d = data.iloc[i]['rsi_d']
			signal = data.iloc[i]['signal']
			price = data.iloc[i]['close']
			time = data.index[i]

			if i == 0:
				start_price = price
			elif i == (len(data)-1):
				end_price = price

			if math.isnan(rsi_k) or math.isnan(rsi_d):
				sell_order.append(-1)
				buy_order.append(-1)
				continue

			if i > 0:
				pre = data.iloc[i-1]['rsi_k']
				cur = rsi_k

			if (rsi_k > rsi_d) and (rsi_k < oversold_rsi) and signal > 0:
				self.buy(price, False)
			elif (rsi_k < rsi_d) and (rsi_k > overbought_rsi) and signal < 0:
				self.sell(price, False)
			else:
				sell_order.append(-1)
				buy_order.append(-1)

		sell = price*coin_num
		seed += sell
		coin_num = 0
		total_profit = self.display_account(ticker, tic, start, end)
		data['buy_order'] = buy_order
		data['sell_order'] = sell_order
		# data.to_csv("./tick_db.csv")
		if display_chart:
			dw.display_rsi(data)

		return total_profit


if __name__ == '__main__':
	a = backTest()
	# a.run_backTest('KRW-ETH',240,'2023-01-01 00:00:00', '2024-01-01 00:00:00', False)
	date_str = '2022-01-01 00:00:00'
	start = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')

	time_gap = timedelta(days=31*12*2)
	tic = ['60']
	tic_num = len(tic)
	ticker = ['KRW-BTC', 'KRW-ETH']
	ticker_num = len(ticker)
	total_profit = [0 for _ in range(ticker_num)]
	for i in range(0, ticker_num): #Ticker
		for j in range(tic_num): #Tic
			for k in range(1): #Range
				total_profit[i] += a.run_backTest(ticker[i], tic[j], start+time_gap*k, start+time_gap*(k+1), display_chart)

	logging.info(f"\n========== Total Profit ==========")
	for i in range(ticker_num):
		logging.info(f"{ticker[i]} :")
		logging.info("{0:>30,} %".format(round(total_profit[i])))
	logging.info(f"==================================\n")
