from numpy import sin
from numpy import power
from numpy import sqrt
from numpy import arange
import numpy as np
from pandas import read_csv
from scipy.optimize import curve_fit
from matplotlib import pyplot

import json
import os
import time
import requests
from _variables_ import _TELEGRAM_BOT_TOKEN_, _CHATID_,_RANGEPRICE_,_GENERAL_API_LIST,_CONFIG_FILE_PATH_,_BASE_API_,logger, _TOP_CHANGE_COIN_DB_, _MARKET_

isminus = False

def get_general_api(_api, _params=None):
	_RETURN_DATA = dict()
	_RETURN_DATA["code"] = 0
	api_index = 0

	while (api_index < len(_BASE_API_)):
		logger.debug("[get_general_api] - Trying {}".format(api_index))
		try:
			if(_params == None):
				_endpoint_url_ = "{}/{}".format(_BASE_API_[api_index], _api)
			else:
				_endpoint_url_ = "{}/{}?{}".format(_BASE_API_[api_index], _api, _params)

			logger.debug("[get_general_api][+] EP URL: {}".format(_endpoint_url_))
			req = requests.get(_endpoint_url_)
			if(req.status_code == 200):
				_RETURN_DATA["content"] = json.loads(req.content.decode("utf-8"))
				_RETURN_DATA["code"] = 1
				break
			else:
				logger.debug("[get_general_api][+] Connection info: {} - {}".format(req.status_code, req.content))
				_RETURN_DATA["content"] = json.loads(req.content.decode("utf-8"))
				_RETURN_DATA["code"] = -1
				break
		except Exception as ex:
			logger.debug("[get_general_api][-] Error: {}".format(ex))
			_RETURN_DATA["content"] = "Connection error!"
			_RETURN_DATA["code"] = -2
			_RETURN_DATA["exception"] = ex
		api_index += 1

	return _RETURN_DATA

def send_notification(context):
	# URL = bot[TOKEN]/sendMessage?chat_id=[CHAT_ID]&text=[MY_MESSAGE_TEXT]
	_BASE_URL_ = "https://api.telegram.org"

	_endpoint_url_ = "{}/{}/sendMessage?chat_id={}&text={}".format(_BASE_URL_, _TELEGRAM_BOT_TOKEN_, _CHATID_, context)
	logger.debug("[send_notification] - _endpoint_url_: {}".format(_endpoint_url_))
	triedtime = 3
	while(triedtime):
		try:
			req = requests.get(_endpoint_url_)
			triedtime = 0
		except Exception as ex:
			triedtime -= 1
			logger.debug("[send_notification] - Error: {}".format(ex))
			pass
	return 0


def read_config():
	# read apikey, secretkey, timetodelay
	global _TIME_TO_DELAY_, _API_KEY_, _SECRET_KEY_, _CHATID_, _TELEGRAM_BOT_TOKEN_
	try:
		configurations = dict()
		with open(_CONFIG_FILE_PATH_, "r") as f:
			for line in f:
				temp = line.strip().split("=")
				configurations[temp[0]] = temp[1]
				# logger.debug((temp[1]))
		# logger.debug(configurations)
		_TIME_TO_DELAY_ = int(configurations.get("_TIME_TO_DELAY_"))
		_API_KEY_ = configurations.get("_API_KEY_")
		_SECRET_KEY_ = configurations.get("_SECRET_KEY_").encode()
		_TELEGRAM_BOT_TOKEN_ = configurations.get("_TELEGRAM_BOT_TOKEN_")
		_CHATID_ = configurations.get("_CHATID_")

	except Exception as ex:
		logger.debug("[read_config][read_config] - Error: {}".format(ex))

def check_tiker_statistics(_list_tikers):
	_api_ = _GENERAL_API_LIST["TIKER_STATISTICS"]
	tiker_statistics = dict()

	for tiker in _list_tikers:
		rs = get_general_api(_api_, _params="symbol={}".format(tiker))
		if(rs.get("code") == 1):
			rs = rs.get("content")
			tiker_statistics[rs.get("symbol")] = rs.get("priceChangePercent")
		else:
			logger.debug("[check_tiker_statistics] - Error code {} | {}".format(rs.get("code"), rs.get("content")))

	return tiker_statistics

def get_top_symbols():
	_RETURN_DATA = dict()
	_RETURN_DATA["code"] = 0
	_api_ = _GENERAL_API_LIST["TIKER_STATISTICS"]
	tiker_statistics = dict()

	rs = get_general_api(_api_)
	bnbmarket = list()
	market = list()
	if(rs.get("code") == 1):
		rs = rs.get("content")
		for _rs in rs:
			if(_rs.get("symbol").find(_MARKET_) >= 1):
				_UP_ = "UP{}".format(_MARKET_)
				_DOWN_ = "DOWN{}".format(_MARKET_)
				if(_UP_ not in _rs.get("symbol") and _DOWN_ not in _rs.get("symbol")):
					bnbmarket.append(_rs)

		bnbmarket = sorted(bnbmarket, key=lambda k: float(k.get("quoteVolume")), reverse=True)

		for m in bnbmarket:
			if(float(m.get("priceChangePercent")) > 5.0):
				logger.debug("[get_top_symbols] - [{}]-{}".format(m.get("symbol"), m.get("quoteVolume")))
				market.append(m)
		with open(_TOP_CHANGE_COIN_DB_, "w+") as f:
			f.write(str(market))
	else:
		logger.debug("[check_tiker_statistics] - Error code {} | {}".format(rs.get("code"), rs.get("content")))

	return market

def coinanalyze(_symbol):
	reborn = False
	_api_ = _GENERAL_API_LIST["CANDLESTICK"]
	
	svrtime = get_general_api(_GENERAL_API_LIST["GETSVRTIME"])
	if(svrtime.get("code") == 1):
		svrtime = svrtime.get("content")
		svrtime = svrtime.get("serverTime")
	else:
		logger.debug("[{}][create_new_order] - Error code: {} | {} | {}".format(self.symbol, server.get("code"), server.get("content"), server.get("exception")))
		return svrtime
	timestamp = svrtime + 3
	starttime = timestamp - 60*5*60

	params = "symbol={}&interval=3m".format(_symbol)
	rs = get_general_api(_api_, params)

	if(rs.get("code") == 1):
		# logger.debug("[{}][coinanalyze] - Content: {}".format(_symbol, rs))
		candles = rs.get("content")[::-1]

		candle_coins = dict()
		check = 0
		while(check < 100):
			temp = dict()
			candle = candles[check]
			# logger.debug("Candle: {}".format(candle))
			temp["open"] = candle[1]
			# logger.debug("High: {}".format(candle[2]))
			temp["high"] = candle[2]
			# logger.debug("Low: {}".format(candle[3]))
			temp["low"] = candle[3]
			temp["closed"] = candle[4]
			# logger.debug("Num of trades: {}".format(candle[8]))
			temp["numoftrades"] = candle[8]
			# logger.debug("================")

			candle_coins[check] = temp 
			check += 1

		count = 0
		for i in candle_coins.keys():
			if(i >= 100): break
			if(float(candle_coins[1].get("closed")) > float(candle_coins[0].get("open"))):
				count += 1

		if(count >= 55):
			reborn = True

		else:
			return False
	else:
		return False

	params = "symbol={}&interval=5m".format(_symbol)
	rs = get_general_api(_api_, params)

	if(rs.get("code") == 1):
		# logger.debug("[{}][coinanalyze] - Content: {}".format(_symbol, rs))
		candles = rs.get("content")[::-1]
		logger.debug("Dict: {}".format(candle_coins))
		if(candle_coins[0].get("numoftrades") > 100):
			if(float(candle_coins[1].get("closed")) < float(candle_coins[0].get("open"))):
				if(float(candle_coins[2].get("closed")) < float(candle_coins[1].get("open"))):
					if(float(candle_coins[3].get("closed")) > float(candle_coins[2].get("open")) and reborn):
						logger.debug("Passed: {}".format(_symbol))
						return True
		else:
			return False
	else:
		return False
	return False

def iscontinuetrade(_symbol):
	_api_ = _GENERAL_API_LIST["CANDLESTICK"]
	
	svrtime = get_general_api(_GENERAL_API_LIST["GETSVRTIME"])
	if(svrtime.get("code") == 1):
		svrtime = svrtime.get("content")
		svrtime = svrtime.get("serverTime")
	else:
		logger.debug("[{}][create_new_order] - Error code: {} | {} | {}".format(self.symbol, server.get("code"), server.get("content"), server.get("exception")))
		return svrtime
	timestamp = svrtime + 3
	starttime = timestamp - 60*5*60

	params = "symbol={}&interval=5m".format(_symbol)
	rs = get_general_api(_api_, params)

	if(rs.get("code") == 1):
		logger.debug("[{}][coinanalyze] - Content: {}".format(_symbol, rs))
		candles = rs.get("content")[::-1]

		candle_coins = dict()
		check = 0
		while(check < 3):
			temp = dict()
			candle = candles[check]
			logger.debug("Open: {}".format(candle[1]))
			temp["open"] = candle[1]
			logger.debug("High: {}".format(candle[2]))
			temp["high"] = candle[2]
			logger.debug("Low: {}".format(candle[3]))
			temp["low"] = candle[3]
			logger.debug("Num of trades: {}".format(candle[8]))
			temp["numoftrades"] = candle[8]
			logger.debug("================")

			candle_coins[check] = temp 
			check += 1

		if(candle_coins[0].get("numoftrades") > 10):
			if(float(candle_coins[0].get("high")) > float(candle_coins[0].get("open"))):
				if(float(candle_coins[0].get("open")) > float(candle_coins[1].get("open")) and float(candle_coins[1].get("open")) > float(candle_coins[2].get("open"))):
					return True
		else:
			return False
	else:
		return False

	return False

def make_matrix(_symbol):
	_api_ = _GENERAL_API_LIST["CANDLESTICK"]
	
	svrtime = get_general_api(_GENERAL_API_LIST["GETSVRTIME"])
	if(svrtime.get("code") == 1):
		svrtime = svrtime.get("content")
		svrtime = svrtime.get("serverTime")
	else:
		logger.debug("[{}][create_new_order] - Error code: {} | {} | {}".format(self.symbol, server.get("code"), server.get("content"), server.get("exception")))
		return svrtime
	timestamp = svrtime + 3
	starttime = timestamp - 60*5*60

	params = "symbol={}&interval=1m".format(_symbol)
	rs = get_general_api(_api_, params)

	if(rs.get("code") == 1):
		# logger.debug("[{}][coinanalyze] - Content: {}".format(_symbol, rs))
		candles = rs.get("content")[::-1]

	check = 0
	candle_coins = []
	while(check < 30):
		candle_coins.append( float(candles[check][4])*10000 )
		check += 1	

	return candle_coins[::-1]


def is_btc_goup(_symbol="BTCUSDT"):
	_api_ = _GENERAL_API_LIST["CANDLESTICK"]
	
	svrtime = get_general_api(_GENERAL_API_LIST["GETSVRTIME"])
	if(svrtime.get("code") == 1):
		svrtime = svrtime.get("content")
		svrtime = svrtime.get("serverTime")
	else:
		logger.debug("[{}][create_new_order] - Error code: {} | {} | {}".format(self.symbol, server.get("code"), server.get("content"), server.get("exception")))
		return svrtime
	timestamp = svrtime + 3
	starttime = timestamp - 60*5*60

	params = "symbol={}&interval=1h".format(_symbol)
	rs = get_general_api(_api_, params)

	if(rs.get("code") == 1):
		# logger.debug("[{}][coinanalyze] - Content: {}".format(_symbol, rs))
		candles = rs.get("content")[::-1]

	return candles[0] > candles[1]


# Cubic function
def function_2(t,a,b,c,d):
	return a*pow(t,3) + b*pow(t, 2) + c*t +d
# Cubic function
def lossing(t,a,b,c,d):
	global isminus
	if( (a > 0 and ( b + c + d)<0) or (a < 0 and ( b + c + d)>0)): 
		isminus = False
	else:
		isminus = True
	return a*t - ( b + c + d) 

def anhnlq_check_lossing(_symbol_matrix):
	cp = _symbol_matrix
	temperature = []
	for i in range(len(cp)):
		temperature.append(i)

	popt, pcov = curve_fit(lossing, temperature,cp)
	fit_cp_c = lossing(np.array (temperature), *popt)

	pyplot.figure(3)
	pyplot.plot(temperature,cp, 'k--')
	pyplot.plot(temperature, fit_cp_c, color='red',linewidth = 1)
	pyplot.legend( ['Actual data','Curve fit'])
	# pyplot.xlabel('Temperature (K)')
	# pyplot.ylabel('Cp (KJ/Kg*K)')
	# pyplot.title('Cubic Curve fitting')
	pyplot.grid()
	global isminus
	# logger.debug("[+] isminus: {}".format(isminus))
	if(isminus):
		filename = "lossing_{}_{}.jpg".format("symbol", time.time())
		savepath = os.path.join("Chart", filename)
		pyplot.savefig(savepath)
		return False

	filename = "passing_{}_{}.jpg".format("symbol", time.time())
	savepath = os.path.join("Chart", filename)
	pyplot.savefig(savepath)

	s = np.sum(cp)
	l = np.size(cp)
	m = s/l
	# For Cubic curve fit
	cubic_SSE = 0
	cubic_SSR = 0
	for j in range(1):
		cubic_error = abs(np.sum((cp[i] - fit_cp_c[i])))
		cubic_SSE = cubic_SSE + (pow(cubic_error , 2))
		cubic_SSR = cubic_SSR + np.sum(pow( (fit_cp_c[i] - m), 2))

	cubic_SST = cubic_SSE + cubic_SSR
	cubic_R2= cubic_SSR/cubic_SST

	pyplot.cla()
	return cubic_R2 < 0.9

def anhnlq_check(_symbol_matrix):
	cp = _symbol_matrix
	temperature = []
	for i in range(len(cp)):
		temperature.append(i)

	popt, pcov = curve_fit(function_2, temperature,cp)
	fit_cp_c = function_2(np.array (temperature), *popt)
	
	pyplot.figure(3)
	pyplot.plot(temperature,cp, 'k--')
	pyplot.plot(temperature, fit_cp_c, color='red',linewidth = 1)
	pyplot.legend( ['Actual data','Curve fit'])
	# pyplot.xlabel('Temperature (K)')
	# pyplot.ylabel('Cp (KJ/Kg*K)')
	# pyplot.title('Cubic Curve fitting')
	pyplot.grid()
	filename = "curve_{}_{}.jpg".format("symbol", time.time())
	savepath = os.path.join("Chart", filename)

	"""
	# Measuring parameters for the fitness characetristics of the curves
	SSE (sum of error squared)
	SSR (sum of squares of the regression)
	SST = SSE + SSR
	R^2 = SSR/SST
	RMSE = (SSE/1)^0.5

	Finding mean of Cp data
	Mean = ( sum of all elements)/(total number of elements)"""

	s = np.sum(cp)
	l = np.size(cp)
	m = s/l
	# For Cubic curve fit
	cubic_SSE = 0
	cubic_SSR = 0
	for j in range(1):
		cubic_error = abs(np.sum((cp[i] - fit_cp_c[i])))
		cubic_SSE = cubic_SSE + (pow(cubic_error , 2))
		cubic_SSR = cubic_SSR + np.sum(pow( (fit_cp_c[i] - m), 2))

	cubic_SST = cubic_SSE + cubic_SSR
	cubic_R2= cubic_SSR/cubic_SST

	_return = False
	if(cubic_R2 > 0.9 and is_btc_goup() and anhnlq_check_lossing(_symbol_matrix)):
		_return = True
	# if(cubic_R2 > 0.9 and is_btc_goup()):
	# 	print('Cubic_R2 :', cubic_R2)
	# 	print('Candle 0 :', _symbol_matrix[0])
	# 	print('Candle 1 :', _symbol_matrix[1])
	# 	pyplot.show()

	pyplot.cla()

	return _return