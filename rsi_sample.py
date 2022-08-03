import plotly
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import pandas as pd
import requests
import talib as ta
import plotly.offline as pyo
import plotly.graph_objs as go
from datetime import datetime

import numpy as np

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
		row_heights=[0.4, 0.3, 0.3] ,
	)
	fig.add_candlestick(x=time,
	                open=data['open'], high=data['high'],
	                low=data['low'], close=data['close'], row=1,col=1)
	k, d = get_stoch_rsi(data)
	order = data['order']
	fig.add_trace(go.Scatter(x=time, y=k), row=3, col=1)
	fig.add_trace(go.Scatter(x=time, y=order), row=3, col=1)
	fig.add_hline(y=80, row=3, col=1)
	fig.add_hline(y=20, row=3, col=1)
	fig.show()
