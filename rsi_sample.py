import plotly.graph_objects as go
from plotly.subplots import make_subplots

import talib as ta
import plotly.graph_objs as go

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
		rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.02,
		row_heights=[0.3, 0.2, 0.2] ,
	)
	fig.update_layout(xaxis_rangeslider_visible=False)
	fig.add_candlestick(x=time,
	                open=data['open'], high=data['high'],
	                low=data['low'], close=data['close'], row=1,col=1)
	k, d = get_stoch_rsi(data)
	order = data['order']
	fig.add_trace(go.Scatter(x=time, y=k), row=2, col=1)
	fig.add_trace(go.Scatter(x=time, y=d), row=2, col=1)
	fig.add_trace(go.Scatter(x=time, y=order), row=3, col=1)
	#fig.add_vline(x=order, row=1, col=1)
	fig.add_hline(y=80, row=2, col=1)
	fig.add_hline(y=20, row=2, col=1)
	fig.show()
