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
force_cell_rate = 1.03
force_buy_rate = 1.005
min_rsi = 20
max_rsi = 80

start_price = 0
end_price = 0
order_price = 0

display_chart = False

class backTest:
	def display_account(self, title, tics, start_time, end_time):
		print("----------------------")
		print("종목, 틱: ", title, tics)
		print("기간 : ", start_time,"-",end_time)
		print("시작 자금: ", "{:,}".format(round(first)), "원")
		print("종료 자금: ", "{:,}".format(round(seed)), "원")
		print("시작 가격: ", "{:,}".format(round(start_price)), "원")
		print("종료 가격: ", "{:,}".format(round(end_price)), "원")
		print("변동폭 : ", round(((end_price-start_price)*100/start_price),2), "(%)")
		print("이익률 : ", round((seed-first)*100/first,2), "(%)")
		print("----------------------")

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
			min_price = 0
		#print("buy condition: ", min_price, "-", price)
		return ret

	def sell(self, price, force):
		global seed, coin_num
		if coin_num > 0:	
			if force == True:
				sell = price*coin_num 
				seed += sell
				coin_num = 0
				order_price = 0
				order.append("매도")
				#print("매도: ", force, "-")
			else:
				if self.sell_condition(price):
					sell = price*coin_num 
					seed += sell
					coin_num = 0
					order_price = 0
					order.append("매도")
					#print("매도: ", force, "-", max_price, "-", price)
				else:
					order.append("관망")
		else:
			order.append("관망")

	def buy(self, price, force):
		global seed, coin_num
		if seed > price:
			if force == True:
				buy_num = int(seed/price)
				coin_num += buy_num
				seed -= (buy_num*price) 
				order_price = price
				order.append("매수")
				#print("매수: ", force, "-")
			else:
				if self.buy_condition(price):
					buy_num = int(seed/price)
					coin_num += buy_num
					seed -= (buy_num*price) 
					order_price = price
					order.append("매수")
					#print("매수: ", force, "-", min_price, "-", price)
				else:
					order.append("관망")
		else:
			order.append("관망")

	def run_backTest(self, start, end, ticker, tic):
		global seed, coin_num, start_price, end_price
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
				order.append("관망")
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
			#강제 매수 - rsi 20 이상에서 stoch 상승 그리고 가격이 buy_rate이상 높아지는 경우.
			elif (rsi_k > rsi_d) and (rsi_k > min_rsi) and (data.iloc[i-1]['close'] < data.iloc[i]['close']*force_buy_rate):
				#print("[force] time: ", time)
				self.buy(price, True)
			#강제 매도 - stoch 하락으로 변하는데 매수가 이하로 내려오는 경우
			elif (rsi_k < rsi_d) and (rsi_k < max_rsi) and (order_price >= price*force_cell_rate):
				#print("[force] time: ", time)
				self.sell(price, True)
			else:
				order.append("관망")

		sell = price*coin_num 
		seed += sell
		coin_num = 0
		self.display_account(ticker, tic, start, end)
		data['order'] = order
		if display_chart:
			dw.display_rsi(data)

if __name__ == '__main__':
	a = backTest()
	a.run_backTest('2022-07-01 00:00:00', '2022-08-01 00:00:00', 'KRW-ETH', 60)
