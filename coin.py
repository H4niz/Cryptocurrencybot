import requests
import json
import os
from _variables_ import _GENERAL_API_LIST,_ACCOUNT_API_,_BASE_API_,logger, _RANGEPRICE_
import time

class Coin(object):
	"""
	Coin class:
		* Providing method for get coin information, exchange coin.
	"""
	coin_info_file_path = ""
	def __init__(self, _symbol, _budget):
		self.symbol = _symbol
		self.budget = _budget
		self.logger = logger
		self.download_coin_info()
		self.lotsize = self.get_ticksize()
		self.stepsize = self.get_stepsize()

	# def __del__(self):
	# 	os.unlink(self.coin_info_file_path)

	def get_general_api(self, _api, _params=None):
		_RETURN_DATA = dict()
		_RETURN_DATA["code"] = 0
		api_index = 0

		while (api_index < len(_BASE_API_)):
			self.logger.debug("[{}] - Trying {}".format(self.symbol, api_index))
			try:
				if(_params == None):
					_endpoint_url_ = "{}/{}".format(_BASE_API_[api_index], _api)
				else:
					_endpoint_url_ = "{}/{}?{}".format(_BASE_API_[api_index], _api, _params)

				self.logger.debug("[{}][+] EP URL: {}".format(self.symbol, _endpoint_url_))
				req = requests.get(_endpoint_url_)
				if(req.status_code == 200):
					_RETURN_DATA["content"] = json.loads(req.content.decode("utf-8"))
					_RETURN_DATA["code"] = 1
					break
				else:
					self.logger.debug("[{}][+] Connection info: {} - {}".format(self.symbol, req.status_code, req.content))
					_RETURN_DATA["content"] = json.loads(req.content.decode("utf-8"))
					_RETURN_DATA["code"] = -1
					break
			except Exception as ex:
				self.logger.debug("[{}][-] Error: {}".format(self.symbol, ex))
				_RETURN_DATA["content"] = "Connection error!"
				_RETURN_DATA["code"] = -2
				_RETURN_DATA["exception"] = ex
				api_index += 1
				time.sleep(0.5)

		return _RETURN_DATA


	def get_exchange_info(self):
		_RETURN_DATA = dict()
		_RETURN_DATA["code"] = 0
		_RETURN_DATA = self.get_general_api(_GENERAL_API_LIST["EXCINFO"])
		return _RETURN_DATA

	def download_coin_info(self):
		self.coin_info_file_path = os.path.join("databases", "{}_info.coin".format(self.symbol))
		self.coin_filter_info_file_path = os.path.join("databases", "{}_filter_info.coin".format(self.symbol))
		data = self.get_exchange_info()

		if(data.get("code") == 1):
			data = data.get("content")
			_symbols = data.get("symbols")
			for _s in _symbols:
				if(_s.get("symbol") == self.symbol):
					new_dict = _s
					for filter_type in _s.get("filters"):
						if(filter_type.get("filterType") == "PRICE_FILTER"):
							new_dict["tickSize"] = filter_type.get("tickSize")
						elif(filter_type.get("filterType") == "LOT_SIZE"):
							new_dict["stepSize"] = filter_type.get("stepSize")

					with open(self.coin_info_file_path, "w+") as f:
						f.write(json.dumps(new_dict))
					break
			self.logger.debug("[get_coin_info] - Get info successful! Store data in {}".format(self.coin_info_file_path))

		else:
			self.logger.debug("[get_coin_info] - Error code: {} | {}".format(data.get("code"), data.get("content")))


	def get_current_price(self):
		self.data = "symbol={}".format(self.symbol)
		rs = self.get_general_api(_GENERAL_API_LIST["TIKER_PRICE"], self.data)
		self.logger.debug("[{}][get_current_price] - {}".format(self.symbol, rs))

		if(rs.get("code") == 1):
			_RETURN_DATA = rs.get("content")
			_RETURN_DATA = _RETURN_DATA.get("price")
		return _RETURN_DATA

	def get_ticksize(self):
		with open(self.coin_info_file_path, "r") as f:
			data = f.read().strip()

		data = json.loads(data)
		ticksize = data.get("tickSize")
		if(ticksize == None):
			self.logger.debug("[get_ticksize] - Get ticksize error!")
		else:
			ticksize = ticksize.find("1") - 1
		return ticksize

	def get_stepsize(self):
		with open(self.coin_info_file_path, "r") as f:
			data = f.read().strip()

		data = json.loads(data)
		stepsize = data.get("stepSize")
		if(stepsize == None):
			self.logger.debug("[get_ticksize] - Get ticksize error!")
		else:
			stepsize = stepsize.find("1") - 1

		if(stepsize < 0):
			stepsize = 0

		return stepsize

	def get_rank_statistics(self):
		_api_ = _GENERAL_API_LIST["TIKER_STATISTICS"]
		tiker_statistics = dict()

		rs = self.get_general_api(_api_, _params="symbol={}".format(self.symbol))
		if(rs.get("code") == 1):
			rs = rs.get("content")
			tiker_statistics[rs.get("symbol")] = rs.get("priceChangePercent")
		else:
			self.logger.debug("[get_rank_statistics] - Error code {} | {}".format(rs.get("code"), rs.get("content")))

		return tiker_statistics