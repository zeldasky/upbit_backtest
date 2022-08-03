import pandas as pd
import tick_db as db
import math
import rsi_sample as dw

order = list()
seed = 1000000
coin_num = 0

def display_account():
	print("----------------------")
	print("Coin num: ", coin_num, "개")
	print("Seed: ", seed, "원")
	print("----------------------")
	print("\n")

data = db.make_tick_db('2020-01-01 00:00:00', '2022-08-01 00:00:00')

for i in range(len(data)):
	rsi = data.iloc[i]['rsi_k']
	price = data.iloc[i]['close']
	time = data.index[i]
	if math.isnan(rsi):
		order.append("0")
		continue

	if rsi < 20:
		if seed > price:
			buy_num = int(seed/price)
			coin_num += buy_num
			seed -= (buy_num*price) 
			#print("< ", time," >")
			#print("< Buy coin: ", price, buy_num, " >")
			order.append("100")
			#display_account()
		else:
			order.append("0")
	elif rsi > 80:
		if coin_num > 0:
			#print("< ", time," >")
			#print("< Sell coin:", price, coin_num, " >")
			sell = price*coin_num 
			seed += sell
			coin_num = 0
			order.append("-50")
			#display_account()
		else:
			order.append("0")
	else:
		order.append("0")

print("[ Settlement Of Coin:", price, coin_num, " ]")
sell = price*coin_num 
seed += sell
coin_num = 0
display_account()
data['order'] = order
dw.display_rsi(data)

