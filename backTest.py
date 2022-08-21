import pandas as pd
import tick_db as db
import math
import rsi_sample as dw
import datetime

order = list()
first = 10000000
seed = 10000000
min_price = 0
max_price = 0
coin_num = 0

prev = 0
cur = 0
min_rate = 1.02
max_rate = 1.005
force_sell_rate = 1.01
force_buy_rate = 1.01
min_rsi = 20
max_rsi = 80

start_price = 0
end_price = 0
order_price = 0
total_profit = 0

class backTest:
	def display_account(self, title, tics, start_time, end_time):
		print("----------------------")
		print("Ticker, Tic: ", title, tics)
		print("Range : ", start_time,"-",end_time)
		print("Start Seed: ", "{:,}".format(round(first)), "won")
		print("End Seed: ", "{:,}".format(round(seed)), "won")
		print("Start Price: ", "{:,}".format(round(start_price)), "won")
		print("End Price: ", "{:,}".format(round(end_price)), "won")
		print("Change Rate : ", round(((end_price-start_price)*100/start_price),2), "(%)")
		print("Profit : ", round((seed-first)*100/first,2), "(%)")
		print("----------------------")
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
		#print("sell condition: ", max_price, "-", price)
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
		#print("buy condition: ", min_price, "-", price)
		return ret

	def sell(self, price, force):
		global seed, coin_num
		if coin_num > 0:	
			if force == True:
				sell = price*coin_num 
				seed += sell
				'''
				print("[Sell] price: ", price, " - number: ", coin_num, " - coin Seed: ", price*coin_num)
				print("[Sell] Seed: ", seed)
				print("\n")
				'''
				coin_num = 0
				order_price = 0
				order.append("Sell")
			else:
				if self.sell_condition(price):
					sell = price*coin_num 
					seed += sell
					'''
					print("[Sell] price: ", price, " - number: ", coin_num, " - coin Seed: ", price*coin_num)
					print("[Sell] Seed: ", seed)
					print("\n")
					'''
					coin_num = 0
					order_price = 0
					order.append("Sell")
				else:
					order.append("Nothing")
		else:
			order.append("Nothing")

	def buy(self, price, force):
		global seed, coin_num
		if seed > price:
			if force == True:
				buy_num = int(seed/price)
				coin_num += buy_num
				seed -= (buy_num*price) 
				order_price = price
				order.append("Buy")
				'''
				print("[Buy] price: ", price, " - number: ", coin_num, " - coin Seed: ", price*coin_num)
				print("[Buy] Seed: ", seed)
				'''
			else:
				if self.buy_condition(price):
					buy_num = int(seed/price)
					coin_num += buy_num
					seed -= (buy_num*price) 
					order_price = price
					order.append("Buy")
					'''
					print("[Buy] price: ", price, " - number: ", coin_num, " - coin Seed: ", price*coin_num)
					print("[Buy] Seed: ", seed)
					'''
				else:
					order.append("Nothing")
		else:
			order.append("Nothing")

	def run_backTest(self, ticker, tic, start, end, display_chart):
		global seed, first, coin_num, start_price, end_price, min_price, max_price
		seed = first
		coin_num =0

		order.clear()
		data = db.make_tick_db(start, end, ticker, tic)
		for i in range(len(data)):
			rsi_k = data.iloc[i]['rsi_k']
			rsi_d = data.iloc[i]['rsi_d']
			price = data.iloc[i]['close']
			time = data.index[i]

			if i == 0:
				start_price = price
			elif i == (len(data)-1):
				end_price = price

			if math.isnan(rsi_k) or math.isnan(rsi_d):
				order.append("Nothing")
				continue

			if i > 0:
				pre = data.iloc[i-1]['rsi_k']
				cur = rsi_k

			if (rsi_k > rsi_d) and (rsi_k < min_rsi):
				#print("[normal] time: ", time)
				self.buy(price, False)
			elif (rsi_k < rsi_d) and (rsi_k > max_rsi):
				#print("[normal] time: ", time)
				self.sell(price, False)
			else:
				order.append("Nothing")

		sell = price*coin_num 
		seed += sell
		coin_num = 0
		total_profit = self.display_account(ticker, tic, start, end)
		data['order'] = order

		if display_chart:
			dw.display_rsi(data)

		return total_profit
			
if __name__ == '__main__':
	a = backTest()
	a.run_backTest('KRW-ETH',15,'2022-08-01 00:00:00', '2022-08-21 00:00:00', False)
