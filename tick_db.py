import pyupbit as up
import rsi_sample as rsi
import numpy as np

def make_tick_db(start, end, ticker, time):
	minute = 'minute'
	range = minute+str(time)
	data = up.get_ohlcv_from(ticker,range,start,end)

	# data.index.name = "date"
	# 단순 이동평균을 사용하여 추세 파악
	window = 14
	data['sma'] = data['open'].rolling(window=window).mean()
	# 단순 이동평균을 사용하여 추세 파악
	data['signal'] = np.where(data['open'] > data['sma'], 1, -1)

	k, d = rsi.get_stoch_rsi(data)
	data.loc[:,'rsi_k'] = k
	data.loc[:,'rsi_d'] = d
	# data.to_csv("./tick_db.csv")
	return data

if __name__ == '__main__':
	make_tick_db('2022-08-01 14:00:00', '2022-08-02 16:00:00','KRW-BTC',15)
