import pyupbit as up
import rsi_sample as rsi

def make_tick_db(start, end, ticker, time):
	minute = 'minute'
	range = minute+str(time)
	data = up.get_ohlcv_from(ticker,range,start,end)
	#data.to_csv("./tick_db.csv")
	k, d = rsi.get_stoch_rsi(data)
	data.loc[:,'rsi_k'] = k
	data.loc[:,'rsi_d'] = d
	return data

if __name__ == '__main__':
	make_tick_db('2022-08-01 14:00:00', '2022-08-02 16:00:00','KRW-BTC',15)
