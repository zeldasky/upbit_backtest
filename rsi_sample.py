import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import talib as ta

def get_stoch_rsi(data):
	close = data['close']
	rsi = ta.RSI(close, timeperiod=14)
	sto_k, sto_d = ta.STOCH(rsi,rsi,rsi,14)

	k = ta.SMA(sto_k, 3)
	d = ta.SMA(k, 3)
	return k,d

def display_rsi(data):
	time = data.index
	fig = make_subplots(
		rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.02,
		row_heights=[0.7, 0.3] ,
	)
	fig.add_candlestick(x=time,
	                open=data['open'], high=data['high'],
	                low=data['low'], close=data['close'], row=1,col=1)
	k, d = get_stoch_rsi(data)

	buy = data['buy_order']
	df = pd.DataFrame({'buy':buy})
	df.drop(df[df['buy'] < 0].index, inplace=True)
	fig.add_trace(go.Scatter(x=df.index ,
							 y = df['buy'],
							 mode = "markers",
							 marker_symbol = "diamond-dot",
							 marker_size = 13,
							 marker_line_width = 2,
							 marker_line_color = "rgba(0,0,0,0.7)",
							 marker_color = "rgba(0,255,0,0.7)",
							 name = "Entries"),
				  row=1, col=1)

	sell = data['sell_order']
	df = pd.DataFrame({'sell':sell})
	df.drop(df[df['sell'] < 0].index, inplace=True)
	fig.add_trace(go.Scatter(x=df.index ,
							 y = df['sell'],
							 mode = "markers",
							 marker_symbol = "diamond-dot",
							 marker_size = 13,
							 marker_line_width = 2,
							 marker_line_color = "rgba(0,0,0,0.7)",
							 marker_color = "rgba(255,0,0,0.7)",
							 name = "Exits"),
				  row=1, col=1)
	fig.add_trace(go.Scatter(x=time, y=k, name = "Stoch_K"), row=2, col=1)
	fig.add_trace(go.Scatter(x=time, y=d, name = "Stoch_D"), row=2, col=1)
	fig.add_hline(y=80, row=2, col=1)
	fig.add_hline(y=20, row=2, col=1)
	fig.update_layout(xaxis_rangeslider_visible=False)
	fig.show()
