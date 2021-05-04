import requests
from datetime import datetime
import time
import json
import hmac
import hashlib
import math
import logging
from datetime import datetime
from _variables_ import _TIME_TO_DELAY_,_RANGEPRICE_,_GENERAL_API_LIST,_CONFIG_FILE_PATH_,_BASE_API_,logger,_ACCOUNT_API_,_MARKET_



class Account(object):
	_CONFIG_FILE_PATH_ = r"configuration.conf"
	def __init__(self, _coin):
		self.read_config()
		self.symbol = _coin
		self.coin = _coin
		return

	def read_config(self):
		try:
			configurations = dict()
			with open(self._CONFIG_FILE_PATH_, "r+") as f:
				for line in f:
					temp = line.strip().split("=")
					configurations[temp[0]] = temp[1]
					# logger.debug((temp[1]))
			# logger.debug(configurations)
			self._TIME_TO_DELAY_ = int(configurations.get("_TIME_TO_DELAY_"))
			self._API_KEY_ = configurations.get("_API_KEY_")
			self._SECRET_KEY_ = configurations.get("_SECRET_KEY_").encode()
			self._TELEGRAM_BOT_TOKEN_ = configurations.get("_TELEGRAM_BOT_TOKEN_")
			self._CHATID_ = configurations.get("_CHATID_")

		except Exception as ex:
			logger.debug("[{}][read_config] - Error: {}".format(self.symbol, ex))

	def generate_hmac_signature(self, data):
		# sample_data = b"symbol=LTCBTC&side=BUY&type=LIMIT&timeInForce=GTC&quantity=1&price=0.1&recvWindow=5000&timestamp=1499827319559"
		# hmac_signature = "c8db56825ae71d6d79447849e617115f4a920fa2acdcab2b053c4b2838bd6b71"
		self.signature = hmac.new(self._SECRET_KEY_, data, hashlib.sha256).hexdigest()
		return self.signature

	def get_general_api(self, _api, _params=None):
		_RETURN_DATA = dict()
		_RETURN_DATA["code"] = 0
		api_index = 0

		while (api_index < len(_BASE_API_)):
			logger.debug("[{}] - Trying {}".format(self.symbol, api_index))
			try:
				if(_params == None):
					_endpoint_url_ = "{}/{}".format(_BASE_API_[api_index], _api)
				else:
					_endpoint_url_ = "{}/{}?{}".format(_BASE_API_[api_index], _api, _params)

				logger.debug("[{}][+] EP URL: {}".format(self.symbol, _endpoint_url_))
				req = requests.get(_endpoint_url_)
				if(req.status_code == 200):
					_RETURN_DATA["content"] = json.loads(req.content.decode("utf-8"))
					_RETURN_DATA["code"] = 1
					break
				else:
					logger.debug("[{}][+] Connection info: {} - {}".format(self.symbol, req.status_code, req.content))
					_RETURN_DATA["content"] = json.loads(req.content.decode("utf-8"))
					_RETURN_DATA["code"] = -1
					break
			except Exception as ex:
				logger.debug("[{}][-] Error: {}".format(self.symbol, ex))
				_RETURN_DATA["content"] = "Connection error!"
				_RETURN_DATA["code"] = -2
				_RETURN_DATA["exception"] = ex
				api_index += 1
				time.sleep(0.5)

		return _RETURN_DATA

	# Account endpoint function
	def account_api(self, _api, _method="GET", _req_body=None, _req_header=None):
		_RETURN_DATA = dict()
		# _RETURN_DATA = {"code": 0, "content": "", "exception": ""}
		_RETURN_DATA["code"] = 0 # Do not do anything
		api_index = 0
		while (api_index < len(_BASE_API_)):
			logger.debug("[{}]Trying {}".format(self.symbol, api_index))
			try:
				_endpoint_url_ = "{}/{}".format(_BASE_API_[api_index], _api)
				if(_method == "GET"):
					if(_req_body != None):
						_endpoint_url_ = "{}?{}".format(_endpoint_url_, _req_body)
						logger.debug("[{}][+] EP URL: [GET] / {}".format(self.symbol, _endpoint_url_))
						req = requests.get(_endpoint_url_, headers=_req_header)
				elif(_method == "POST"):
					#Post request, make header/body
					logger.debug("[{}][+] EP URL: [POST] / {}".format(self.symbol, _endpoint_url_))
					if(_req_body == None):
						logger.debug("[{}][account_api] - _req_body needed!".format(self.symbol))
					else:
						logger.debug("[{}][account_api] - _req_body: {}\n_req_header: {}\n".format(self.symbol, _req_body, _req_header))
						req = requests.post(_endpoint_url_, data=_req_body, headers=_req_header)
				elif(_method == "DELETE"):
					logger.debug("[{}][account_api] - _req_body: {}\n_req_header: {}\n".format(self.symbol, _req_body, _req_header))
					req = requests.delete(_endpoint_url_, data=_req_body, headers=_req_header)
				

				if(req.status_code == 200):
					# logger.debug("[200][account_api][{}] - {}".format(_api, req.content))
					_RETURN_DATA["content"] = json.loads(req.content.decode("utf-8"))
					_RETURN_DATA["code"] = 1 #Success
					break
				else:
					logger.debug("[{}][+] Connection info: {}/{}".format(self.symbol, req.status_code, req.content))
					_RETURN_DATA["content"] = json.loads(req.content.decode("utf-8"))
					_RETURN_DATA["code"]
					break
			except Exception as ex:
				logger.debug("[{}][-] Error: {}".format(self.symbol, ex))
				_RETURN_DATA["content"] = "Connection error!"
				_RETURN_DATA["exception"] = ex
				_RETURN_DATA["code"] = -2 #Exception
				time.sleep(0.1)
				api_index += 1

		return _RETURN_DATA

	def get_balance(self):
		_RETURN_DATA = None
		# make header
		headers = {"X-MBX-APIKEY": self._API_KEY_}
		# Test get server time
		svrtime = self.get_general_api(_GENERAL_API_LIST["GETSVRTIME"])
		if(svrtime.get("code") == 1):
			svrtime = svrtime.get("content")
		timestamp = svrtime.get("serverTime") + 3

		bodies = "timestamp={}&recvWindow=50000".format(timestamp)
		signature = self.generate_hmac_signature(bodies.encode("utf-8"))
		bodies = "{}&signature={}".format(bodies, signature)
		rs = self.account_api(_ACCOUNT_API_["BALANCE"], _method="GET", _req_body=bodies, _req_header=headers)
		if(rs.get("code") == 1):
			rs = rs.get("content")
			rs = rs.get("balances")
			for _rs in rs:
				if(_rs.get("asset") == _MARKET_):
					_RETURN_DATA = _rs.get("free")
		else:
			logger.debug("[check_balance] - Error code: {} | {}".format(rs.get("code"), rs.get("content")))

		return _RETURN_DATA

	def create_new_order(self, _limit_price=None, _stop_price=None, _quantity=0, _type="STOP_LOSS_LIMIT", _side="SELL"):
		_RETURN_DATA = dict()
		_RETURN_DATA["code"] = 0
		if(_limit_price != None and _stop_price != None):
			# Handler
			headers = {"X-MBX-APIKEY": self._API_KEY_}
			# Test get server time
			svrtime = self.get_general_api(_GENERAL_API_LIST["GETSVRTIME"])
			if(svrtime.get("code") == 1):
				svrtime = svrtime.get("content")
				svrtime = svrtime.get("serverTime")
			else:
				logger.debug("[{}][create_new_order] - Error code: {} | {} | {}".format(self.symbol, server.get("code"), server.get("content"), server.get("exception")))
				return svrtime

			logger.debug("[+] Server time: {}".format(svrtime))
			balances = self.get_balance()

			timestamp = svrtime + 3
			bodies = "symbol={}&side={}&type={}&timeInForce={}&quantity={}&price={}&timestamp={}&recvWindow=50000".format(self.symbol, _side, _type, "GTC", _quantity, _limit_price, timestamp)
			if(float(_stop_price) != 0.0):
				bodies = "{}&stopPrice={}".format(bodies, _stop_price)
			signature = self.generate_hmac_signature(bodies.encode("utf-8"))
			bodies = "{}&signature={}".format(bodies, signature)
			logger.debug("[{}][create_new_order] - Body: {}".format(self.symbol, bodies))

			# def account_api(_api, _method="GET", _req_body=None, _req_header=None):
			rs = self.account_api(_ACCOUNT_API_["ORDER"], _method="POST", _req_body=bodies, _req_header=headers)
			# logger.debug("[create_new_order] - DEBUG - {}".format(rs))
			if(rs.get("code") == 1):
				ct = rs.get("content")
				ct["price"] = _stop_price
				ct["origQty"] = _quantity
				rs["content"] = ct
				return rs
			else:
				logger.debug("[{}][create_new_order] - Error code: {} | {} | {}".format(self.symbol, rs.get("code"), rs.get("content"), rs.get("exception")))
				return rs
		else:
			_RETURN_DATA["code"] = -1
			_RETURN_DATA["content"] = "Assession failed"

		return _RETURN_DATA

	def cancel_order(self, _orderid, _origClientOrderId):
		_RETURN_DATA = dict()
		_RETURN_DATA["code"] = 0
		# b'{"symbol":"IQBNB","orderId":12856460,"orderListId":-1,"clientOrderId":"IWiBFgXE3WOWVPskKazLcS","transactTime":1615721252141}'
		headers = {"X-MBX-APIKEY": self._API_KEY_}
		# Test get server time
		svrtime = self.get_general_api(_GENERAL_API_LIST["GETSVRTIME"])
		if(svrtime.get("code") == 1):
			svrtime = svrtime.get("content")
			svrtime = svrtime.get("serverTime")
		else:
			logger.debug("[{}][create_new_order] - Error code: {} | {} | {}".format(self.symbol, server.get("code"), server.get("content"), server.get("exception")))
			return svrtime
		logger.debug("[+] Server time: {}".format(svrtime))
		timestamp = svrtime

		bodies = "symbol={}&orderId={}&origClientOrderId={}&timestamp={}&recvWindow=50000".format(self.symbol, _orderid, _origClientOrderId, timestamp)
		signature = self.generate_hmac_signature(bodies.encode("utf-8"))
		bodies = "{}&signature={}".format(bodies, signature)

		logger.debug("[{}][cancel_order] - Body: {}".format(self.symbol, bodies))

		# def account_api(_api, _method="GET", _req_body=None, _req_header=None):
		rs = self.account_api(_ACCOUNT_API_["ORDER"], _method="DELETE", _req_body=bodies, _req_header=headers)
		logger.debug("[{}][cancel_order] - Body: {}".format(self.symbol, rs))
		if(rs.get("code") == 1):
			return rs
		else:
			logger.debug("[{}][cancel_order] - Error code: {} | {} | {}".format(self.symbol, rs.get("code"), rs.get("content"), rs.get("exception")))
			return rs

		return rs

	def query_order(self, _orderid, _origClientOrderId):
		_RETURN_DATA = None
		# make header
		headers = {"X-MBX-APIKEY": self._API_KEY_}
		# Test get server time
		svrtime = self.get_general_api(_GENERAL_API_LIST["GETSVRTIME"])
		if(svrtime.get("code") == 1):
			svrtime = svrtime.get("content")
			svrtime = svrtime.get("serverTime")
		else:
			logger.debug("[{}][create_new_order] - Error code: {} | {} | {}".format(self.symbol, server.get("code"), server.get("content"), server.get("exception")))
			return svrtime
		timestamp = svrtime + 3

		bodies = "symbol={}&orderId={}&origClientOrderId={}&timestamp={}&recvWindow=50000".format(self.symbol, _orderid, _origClientOrderId, timestamp)
		signature = self.generate_hmac_signature(bodies.encode("utf-8"))
		bodies = "{}&signature={}".format(bodies, signature)
		rs = self.account_api(_ACCOUNT_API_["ORDER"], _method="GET", _req_body=bodies, _req_header=headers)
		_RETURN_DATA = rs
		return _RETURN_DATA

	def sell(self, _price, _quantity):
		logger.info("[{}][{}] - price: {} | quantity: {} ".format(self.symbol, "SELL" , _price, _quantity))
		rs = self.create_new_order(_limit_price=_price, _stop_price=_price, _quantity=_quantity)
		if(rs.get("code") != 1):
			logger.info("[{}][sell] - Error code: {} | {} | {}".format(self.symbol, rs.get("code"), rs.get("content"), rs.get("exception")))

		return rs

	def buy(self, _price, _quantity):
		logger.info("[{}][{}] - price: {} | quantity: {} ".format(self.symbol, "BUY", _price, _quantity))
		rs = self.create_new_order(_limit_price=_price, _stop_price=_price, _quantity=_quantity, _side="BUY")
		if(rs.get("code") != 1):
			logger.info("[{}][{}] - Error code: {} | {} | {}".format(self.symbol, "BUY", rs.get("code"), rs.get("content"), rs.get("exception")))
		else:
			logger.info("[{}][{}] - BUY: _price: {} | _quantity: {} |".format(self.symbol, "BUY", _price, _quantity))

		return rs

	def followtop(self, targeted_coin, _saferange, orderinfo=None):
		_RETURN_DATA = dict()
		_RETURN_DATA["code"] = -1

		if(orderinfo == None): 
			logger.debug("[{}][followtop][+] There is not orderinfo!".format(self.symbol))
		else:
			logger.debug("[{}][followtop][+] orderinfo: {}".format(self.symbol, orderinfo))

		orderId = orderinfo.get("orderId")
		clientOrderId = orderinfo.get("clientOrderId")
		_limitprice = orderinfo.get("price")
		buy_price = float(_limitprice)
		_quantity = orderinfo.get("origQty")
		logger.debug("[followtop] - orderId: {} | clientOrderID: {}".format(orderId, clientOrderId))


		# Waiting for filled buy order
		isWait = True
		while(isWait):
			isWait = False
			time.sleep(1.337)
			result = self.query_order(_orderid=orderId, _origClientOrderId=clientOrderId)

			# Error handler
			if(result.get("code") != 1):
				error = result.get("content")
				logger.info("[{}][followtop] - Code: {} | msg: {}".format(self.symbol, error.get("code"), error.get("msg")))
				isWait=True
			# End error handler

			_RETURN_DATA = result.get("content")
			tranaction = result.get("content")
			logger.debug("[{}][followtop] - Line 300: {}".format(self.symbol, tranaction))
			status = _RETURN_DATA.get("status")
					
			if(tranaction.get("status") == "FILLED"):
				filled_quantity = tranaction.get("origQty")
				logger.info("[{}][followtop] - Line 304 buy successfull!  {} | {}".format(self.symbol, _limitprice, filled_quantity))
				profit = float(_limitprice) - buy_price
				isWait = False
				_RETURN_DATA["profit"] = round(profit, 8)*float(filled_quantity)
				_RETURN_DATA["code"] = 1
				_RETURN_DATA["content"] = tranaction
				return _RETURN_DATA
		# End waiting
	

		# Wait for always take profit
		nottakeprofit = True
		while(nottakeprofit):
			current_price = round(float(targeted_coin.get_current_price()), targeted_coin.lotsize)
			targeted_price = str(round(float(buy_price)+_saferange*_RANGEPRICE_, targeted_coin.lotsize))
			# ID: 112233
			logger.info("[{}][followtop] - 112233 - wait for always taking profit currnet price {} | {}".format(self.symbol, current_price, targeted_price))
			if(current_price >= float(targeted_price)):
				nottakeprofit = False

			time.sleep(1.337)
		# End wait to take profit

		# Sell when filled buy order
		isloop = True
		while(isloop):
			isloop = False
			current_price = round(float(targeted_coin.get_current_price()), targeted_coin.lotsize)
			topprice = float(current_price)
			targeted_price = str(round(float(current_price)-_saferange*_RANGEPRICE_, targeted_coin.lotsize))
			if(targeted_coin.lotsize == 8):
				targeted_price = "{:.8f}".format(round(float(current_price)-_saferange*_RANGEPRICE_, targeted_coin.lotsize))
			
			result = self.sell(targeted_price, _quantity)
			# Error handler
			if(result.get("code") != 1):
				error = result.get("content")
				logger.info("[{}][followbottom] - Code: {} | msg: {}".format(self.symbol, error.get("code"), error.get("msg")))
				if(error.get("code") == -2010 and error.get("msg") == "Stop price would trigger immediately."): # Stop price would trigger immediately.
					isloop = True
					_saferange += _saferange*0.2
					time.sleep(1)
				elif(error.get("msg") == "Account has insufficient balance for requested action."):
					_RETURN_DATA = result
					_RETURN_DATA["code"] = -1
					_RETURN_DATA["content"] = error
					return _RETURN_DATA
				elif(error.get("code") == -1100):
					_RETURN_DATA = result
					_RETURN_DATA["code"] = -1
					_RETURN_DATA["content"] = error
					return _RETURN_DATA
				else:
					_RETURN_DATA = result
					_RETURN_DATA["code"] = -1
					_RETURN_DATA["content"] = error
					return _RETURN_DATA
			else:
				tranaction = result.get("content")
				logger.debug("[{}][followtop] - First sell: {}".format(self.symbol, tranaction))
				if(tranaction.get("status") == "FILLED"):
					filled_quantity = tranaction.get("origQty")
					logger.info("[{}][followtop] - Line 338 Sell successfull!  {} | {}".format(self.symbol, _limitprice, filled_quantity))
					if(float(filled_quantity) == float(_quantity)):
						profit = float(_limitprice) - buy_price
						_RETURN_DATA["code"] = 1
						_RETURN_DATA["content"] = tranaction
						_RETURN_DATA["profit"] = round(profit, 8)*float(filled_quantity)
						isloop = False
						return _RETURN_DATA
					else:
						_quantity = str(round((float(_quantity) - float(filled_quantity)), targeted_coin.stepsize))
					
		orderId = tranaction.get("orderId")
		clientOrderId = tranaction.get("clientOrderId")
		#  End

		# if price is increasing --> follow price.
		isloop = True
		while(isloop):
			time.sleep(_TIME_TO_DELAY_)
			current_price = round(float(targeted_coin.get_current_price()), targeted_coin.lotsize)

			if(current_price > topprice):
				topprice = current_price
				# Stop > limit
				if(targeted_coin.lotsize == 8):
					_stopprice = "{:.8f}".format(round((current_price-round(_saferange*_RANGEPRICE_, 8)), targeted_coin.lotsize))
				else:
					_stopprice = str(round((current_price-_saferange*_RANGEPRICE_), targeted_coin.lotsize))

				_limitprice = _stopprice
				self.cancel_order(_orderid=orderId, _origClientOrderId=clientOrderId)
				result = self.sell(_limitprice, _quantity)
				# result = result.decode("utf-8")
				
				# Error handler
				if(result.get("code") != 1):
					error = result.get("content")
					logger.info("[{}][followbottom] - Code: {} | msg: {}".format(self.symbol, error.get("code"), error.get("msg")))
					if(error.get("code") == -2010 and error.get("msg") == "Stop price would trigger immediately."): # Stop price would trigger immediately.
						_saferange += _saferange*0.5
						time.sleep(1)
					elif(error.get("msg") == "Account has insufficient balance for requested action."):
						_RETURN_DATA = result
						_RETURN_DATA["code"] = -1
						_RETURN_DATA["content"] = error
						return _RETURN_DATA
					elif(error.get("code") == -1100):
						_RETURN_DATA = result
						_RETURN_DATA["code"] = -1
						_RETURN_DATA["content"] = error
						return _RETURN_DATA
					else:
						_RETURN_DATA = result
						_RETURN_DATA["code"] = -1
						_RETURN_DATA["content"] = error
						return _RETURN_DATA
				else:
					tranaction = result.get("content")
					logger.debug("[{}][followtop] - Create new order: {}".format(self.symbol, tranaction))
					if(tranaction.get("status") == "FILLED"):
						filled_quantity = tranaction.get("origQty")
						logger.info("[{}][followtop] - Line 399 Sell successfull!  {} | {}".format(self.symbol, _limitprice, filled_quantity))
						isloop = False
						profit = float(_limitprice) - buy_price
						_RETURN_DATA["code"] = 1
						_RETURN_DATA["content"] = tranaction
						_RETURN_DATA["profit"] = round(profit, 8)*float(filled_quantity)
						return _RETURN_DATA

				orderId = tranaction.get("orderId")
				clientOrderId = tranaction.get("clientOrderId")
	
				if(orderId == None): break

				# Double check order status
				isloopp = True
				while(isloopp):
					isloopp = False
					result = self.query_order(_orderid=orderId, _origClientOrderId=clientOrderId)

					# Error handler
					if(result.get("code") != 1):
						error = result.get("content")
						logger.info("[{}][followtop] - Code: {} | msg: {}".format(self.symbol, error.get("code"), error.get("msg")))
						isloopp=True
					# End error handler

					_RETURN_DATA = result.get("content")
					tranaction = result.get("content")
					logger.debug("[{}][followtop] - Query order: {}".format(self.symbol, tranaction))
					status = _RETURN_DATA.get("status")
					
					if(tranaction.get("status") == "FILLED"):
						filled_quantity = tranaction.get("origQty")
						logger.info("[{}][followtop] - Line 431 Sell successfull!  {} | {}".format(self.symbol, _limitprice, filled_quantity))
						profit = float(_limitprice) - buy_price
						isloopp = False
						_RETURN_DATA["profit"] = round(profit, 8)*float(filled_quantity)
						_RETURN_DATA["code"] = 1
						_RETURN_DATA["content"] = tranaction
						return _RETURN_DATA
				# End

			else:
				# Check order status again
				result = self.query_order(_orderid=orderId, _origClientOrderId=clientOrderId)

				# Error handler
				if(result.get("code") != 1):
					error = result.get("content")
					logger.info("[{}][followtop] - Code: {} | msg: {}".format(self.symbol, error.get("code"), error.get("msg")))
					isloopp=True
				else:
					tranaction = result.get("content")
				# End error handler

				_RETURN_DATA = result.get("content")
				tranaction = result.get("content")
				logger.debug("[{}][followtop] - Content: {}".format(self.symbol, _RETURN_DATA))
				status = _RETURN_DATA.get("status")
					
				if(tranaction.get("status") == "FILLED"):
					filled_quantity = tranaction.get("origQty")
					logger.info("[{}][followtop] - Sell successfull!  {} | {}".format(self.symbol, _limitprice, filled_quantity))
					profit = float(_limitprice) - buy_price
					_RETURN_DATA["profit"] = round(profit, 8)*float(filled_quantity)
					_RETURN_DATA["code"] = 1
					_RETURN_DATA["content"] = tranaction
					return _RETURN_DATA
				# end order status
				logger.debug("[{}][followtop] - Waiting for price...".format(self.symbol))
			# End following price

		return _RETURN_DATA

	def followbottom(self, targeted_coin, _saferange):
		_RETURN_DATA = dict()
		_RETURN_DATA["code"] = -1
		isloop = True
		while isloop:
			isloop = False 
			topprice = 0
			# 1. Check price
			if(_saferange < 0): _saferange *=-1
			
			current_price = round(float(targeted_coin.get_current_price()), targeted_coin.lotsize)
			topprice = current_price
			# Stop > limit
			_stopprice = str(round((float(current_price)+_saferange*0.2), targeted_coin.lotsize))
			if(targeted_coin.lotsize == 8):
				_stopprice = "{:.8f}".format(round((float(current_price)+round(_saferange*0.2, 8)), targeted_coin.lotsize))

			_limitprice = _stopprice	
			_quantity = str(round(targeted_coin.budget/float(_limitprice), targeted_coin.stepsize))

			logger.info("[{}][followbottom][+]Current price: {}".format(self.symbol, current_price))
			logger.info("[{}][followbottom][+]_saferange: {:.8f}".format(self.symbol, _saferange))
			logger.info("[{}][followbottom][+]Limit price: {}".format(self.symbol, _limitprice))
			logger.info("[{}][followbottom][+]_LOT_SIZE_: {}".format(self.symbol, targeted_coin.lotsize))
			logger.info("[{}][followbottom][+]STEP: {}".format(self.symbol, targeted_coin.stepsize))

			result = self.buy(_limitprice, _quantity)

			# Error handler
			if(result.get("code") != 1):
				error = result.get("content")
				logger.info("[{}][followbottom] - Code: {} | msg: {}".format(self.symbol, error.get("code"), error.get("msg")))
				if(error.get("code") == -2010 and error.get("msg") == "Stop price would trigger immediately."): # Stop price would trigger immediately.
					isloop = True
					_saferange += _saferange*0.5
					time.sleep(1)
				elif(error.get("msg") == "Account has insufficient balance for requested action."):
					_RETURN_DATA = result
					_RETURN_DATA["code"] = -1
					_RETURN_DATA["content"] = error
					return _RETURN_DATA
				elif(error.get("code") == -1100):
					_RETURN_DATA = result
					_RETURN_DATA["code"] = -1
					_RETURN_DATA["content"] = error
					return _RETURN_DATA
				else:
					_RETURN_DATA = result
					_RETURN_DATA["code"] = -1
					_RETURN_DATA["content"] = error
					return _RETURN_DATA
			else:
				tranaction = result.get("content")
				logger.debug("[{}][followbottom] - Content: {}".format(self.symbol, tranaction))
				# if(tranaction.get("status") != "FILLED"): isloop = True
			# End error handler

			_RETURN_DATA = result.get("content")

		logger.debug(result)
		
		if(result.get("code") == 1):
			logger.info("[{}][followbottom] - Order accepted! {}".format(_limitprice, result.get("content")))
			result = result.get("content")
		else:
			logger.info("[{}][followbottom] - Buy unsuccessful!".format(_limitprice))
			_RETURN_DATA["profit"] = 0
			return _RETURN_DATA

		orderId = result.get("orderId")
		clientOrderId = result.get("clientOrderId")

		logger.debug("[followbottom] - orderId: {} | clientOrderID: {}".format(orderId, clientOrderId))

		while(1):
			time.sleep(_TIME_TO_DELAY_)
			current_price = round(float(targeted_coin.get_current_price()), targeted_coin.lotsize)
				# Stop > limit
			_stopprice = str(round((current_price+_saferange*_RANGEPRICE_), targeted_coin.lotsize))
			_limitprice = _stopprice
			if(current_price < topprice):
				topprice = current_price
				self.cancel_order(_orderid=orderId, _origClientOrderId=clientOrderId)
				isloop = True
				while(isloop):
					if(targeted_coin.lotsize == 8):
						_limitprice = "{:.8f}".format(round(float(_limitprice) + round(float(_saferange)*0.1, 8), targeted_coin.lotsize))
					else:
						_limitprice = str(round(float(_limitprice) + float(_saferange)*0.1, targeted_coin.lotsize))
					isloop = False
					result = self.buy(_limitprice, _quantity)
					# result = result.decode("utf-8")
					
					# Error handler
					if(result.get("code") != 1):
						error = result.get("content")
						logger.info("[{}][followbottom] - Code: {} | msg: {}".format(self.symbol, error.get("code"), error.get("msg")))
						if(error.get("code") == -2010 and error.get("msg") == "Stop price would trigger immediately."): # Stop price would trigger immediately.
							isloop = True
							_saferange += _saferange*0.5
							time.sleep(1)
						elif(error.get("msg") == "Account has insufficient balance for requested action."):
							_RETURN_DATA["code"] = -1
							_RETURN_DATA["content"] = error
						elif(error.get("code") == -1100):
							_RETURN_DATA["code"] = -1
							_RETURN_DATA["content"] = error
						else:
							_RETURN_DATA = result
							_RETURN_DATA["code"] = -1
							_RETURN_DATA["content"] = error
							return _RETURN_DATA
					else:
						tranaction = result.get("content")
						logger.debug("[{}][followbottom] - Content: {}".format(self.symbol, tranaction))
						# if(tranaction.get("status") != "FILLED"): isloop = True
					# End error handler

					orderId = tranaction.get("orderId")
					clientOrderId = tranaction.get("clientOrderId")
			else:
				logger.debug("Waiting for filled!")

			result = self.query_order(_orderid=orderId, _origClientOrderId=clientOrderId)

			# Error handler
			if(result.get("code") != 1):
				error = result.get("content")
				logger.info("[{}][followbottom] - Code: {} | msg: {}".format(self.symbol, error.get("code"), error.get("msg")))
				# _RETURN_DATA["profit"] = 0
				# return _RETURN_DATA
			# End error handler

			_RETURN_DATA = result.get("content")
			logger.debug("[{}][followbottom] - Content: {}".format(self.symbol, _RETURN_DATA))
			status = _RETURN_DATA.get("status")
			if(status == "FILLED"):
				_RETURN_DATA["code"] = 1
				_RETURN_DATA["content"] = result.get("content")
				# profit = float(_limitprice) - buy_price
				# _RETURN_DATA["profit"] = round(profit, 8)*float(_quantity)
				break


		return _RETURN_DATA