import pandas as pd
import pyupbit as up
import rsi_sample as rsi

def make_tick_db(start, end):
	data = up.get_ohlcv_from('KRW-ETH','minute60',start,end)
	data.to_csv("./tick_db.csv")
	k, d = rsi.get_stoch_rsi(data)
	data.loc[:,'rsi_k'] = k
	data.loc[:,'rsi_d'] = d
	#rsi.display_rsi(data)
	return data

if __name__ == '__main__':
	make_tick_db('2022-08-01 14:00:00', '2022-08-02 16:00:00')
