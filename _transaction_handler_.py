import requests
from datetime import datetime
import time
import json
import hmac
import hashlib
import math
import logging
from datetime import datetime

from coin import Coin
from account import Account
from _variables_ import _TIME_TO_DELAY_,_RANGEPRICE_,_GENERAL_API_LIST,_CONFIG_FILE_PATH_,_BASE_API_,logger, _TOP_CHANGE_COIN_DB_, _MARKET_

from utils import *

def dutheodinh(targeted_coin, _account, _saferange):
	topprice = 0
	# 1. Check price
	if(_saferange < 0): _saferange *=-1
	
	current_price = round(float(targeted_coin.get_current_price()), targeted_coin.lotsize)
	topprice = current_price
	print("Current price: {}".format(current_price))
	# Stop > limit
	_stopprice = str(round((float(current_price)-_saferange*_RANGEPRICE_), targeted_coin.lotsize))
	_limitprice = _stopprice

	logger.debug("[+] Limit price: {}".format((_limitprice)))
	logger.debug("[+] _LOT_SIZE_: {}".format((targeted_coin.lotsize)))
	logger.debug("[+] STEP: {}".format((targeted_coin.stepsize)))
	
	_quantity = str(round(targeted_coin.budget/float(_limitprice), targeted_coin.stepsize))

	result = _account.buy(_limitprice, _quantity)
	_RETURN_DATA = result

	logger.debug(result)
	if(result.get("code") == 1):
		result=result.get("content")
		logger.info("[{}][dutheodinh] - Buy successful! {}".format(_limitprice, result.get("content")))
	else:
		logger.info("[{}][dutheodinh] - Error occurs!".format(_limitprice))

	orderId = result.get("orderId")
	clientOrderId = result.get("clientOrderId")

	logger.debug("[dutheodinh] - orderId: {}\nclientOrderID: {}".format(orderId, clientOrderId))
	
	while(1):
		time.sleep(_TIME_TO_DELAY_)
		current_price = round(float(targeted_coin.get_current_price()), targeted_coin.lotsize)
		# Stop > limit
		_stopprice = str(round((current_price-_saferange*_RANGEPRICE_), targeted_coin.lotsize))
		_limitprice = _stopprice

		if(current_price > topprice):
			topprice = current_price
			cancel_order(_symbol=_symbol, _orderid=orderId, _origClientOrderId=clientOrderId)
			result = create_new_order(_symbol=_symbol, _limit_price="{:.8f}".format(_limitprice), _stop_price="{:.8f}".format(_stopprice), _quantity=_quantity)
			# result = result.decode("utf-8")
			result = json.loads(result)
			orderId = result.get("orderId")
			clientOrderId = result.get("clientOrderId")
		else:
			logger.debug("Cho cat lo!")

		if(orderId == None): break
		result = query_order(_symbol=_symbol, _orderid=orderId, _origClientOrderId=clientOrderId)
		result = result.decode("utf-8")
		result = json.loads(result)
		_RETURN_DATA = result
		status = result.get("status")
		if(status == "FILLED"): break


	return _RETURN_DATA

def bamday(_symbol, _saferange, _budget):
	# topprice
	topprice = 0
	iswait = True
	global _NUMBER_OF_ZERO_DIGIT, _TIME_TO_DELAY_, _LOT_SIZE_
	# 1. Check price
	if(_saferange < 0): _saferange *=-1
	current_price = query_symbol_price(_symbol)
	topprice = current_price

	# Stop < Limit
	_stopprice = round((current_price+_saferange*_RANGEPRICE_), _NUMBER_OF_ZERO_DIGIT)
	_limitprice = _stopprice

	logger.debug("_NUMBER_OF_ZERO_DIGIT {}".format(_NUMBER_OF_ZERO_DIGIT))
	logger.debug("[Follow lowest price] Current price: {:.8f}".format(current_price))
	logger.debug("[Follow lowest price] Top/Old price: {:.8f}".format(topprice))
	logger.debug("[Follow lowest price] SafeRange: {:.8f}".format(_saferange))
	logger.debug("[+] _LOT_SIZE_: {}".format((_LOT_SIZE_)))
	result = create_new_order(_symbol=_symbol, _limit_price="{:.8f}".format(_limitprice), _stop_price="{:.8f}".format(_stopprice), _quantity=round(_budget/current_price, _LOT_SIZE_), _side="BUY")
	# logger.debug("[*] Result: {}".format(result))
	result = result.decode("utf-8")
	result = json.loads(result)
	orderId = result["orderId"]
	clientOrderId = result["clientOrderId"]

	logger.debug("[Follow lowest price] - orderId: {}\nclientOrderID: {}".format(orderId, clientOrderId))
	
	while(iswait):
		if(orderId == None or clientOrderId==None):
			iswait = False
			break
		result = query_order(_symbol=_symbol, _orderid=orderId, _origClientOrderId=clientOrderId)
		temp_result = result.decode("utf-8")
		temp_result = json.loads(temp_result)
		# logger.debug("[bamday] - {}".format(result))
		status = temp_result.get("status")
		origQty = float(temp_result["origQty"])
		price = float(temp_result["price"])
		# logger.debug("[bamday] - Order status: {}\nPrice: {}\nQuantity: {}".format(status, price, origQty))
		
		if(status == "FILLED"):
			logger.debug("[bamday] - FILLED")
			iswait = False
			break

		logger.debug("[bamday] - Delay: {}s".format(_TIME_TO_DELAY_))
		time.sleep(_TIME_TO_DELAY_)

		current_price = query_symbol_price(_symbol)

		if(current_price < topprice or status == "CANCELED"):
			# Stop < Limit
			_stopprice = round((current_price+_saferange*_RANGEPRICE_), _NUMBER_OF_ZERO_DIGIT)
			_limitprice = _stopprice
			logger.debug("[Follow lowest price] Current price: {:.8f}".format(_stopprice))
			logger.debug("[bamday] - Cancel order id: {}\nCreate new order with price: {} and quantity: {}".format(orderId, current_price+_saferange, round((_budget/current_price), _LOT_SIZE_)))
			
			cancel_order(_symbol=_symbol, _orderid=orderId, _origClientOrderId=clientOrderId)
			
			topprice = current_price
			result = create_new_order(_symbol=_symbol, _limit_price="{:.8f}".format(_limitprice), _stop_price="{:.8f}".format(_stopprice), _quantity=round((_budget/current_price), _LOT_SIZE_), _side="BUY")
			result = result.decode("utf-8")
			result = json.loads(result)
			orderId = result.get("orderId")
			clientOrderId = result.get("clientOrderId")
		else:
			logger.debug("Cho vao gia!")

	return result

def automated(_symbol, _fund, _changed=None):
	#calculator
	current_price = query_symbol_price(_symbol)
	str_current_price = "{:.8f}".format(current_price)
	logger.debug(str_current_price.split("."))
	global _NUMBER_OF_ZERO_DIGIT, _TIME_TO_DELAY_, _PROFIT_

	_NUMBER_OF_ZERO_DIGIT = len(str_current_price.split(".")[1])

	logger.debug("_NUMBER_OF_ZERO_DIGIT: {}/{:.8f}".format(_NUMBER_OF_ZERO_DIGIT, current_price))
	logger.debug("_TIME_TO_DELAY_: {}".format(_TIME_TO_DELAY_))
	isnextstep = False

	while(isnextstep is False):
		time.sleep(5)
		next_price = query_symbol_price(_symbol)
		time.sleep(5)
		third_price = query_symbol_price(_symbol)

		# logger.debug("[automated] - last_price: {:.8f}".format(current_price))
		# logger.debug("[automated] - current_price: {:.8f}".format(next_price))

		if(_changed != None): 
			change_price = _changed
		else:
			change_price = current_price - next_price
			change_one_price = next_price - third_price

		logger.debug("[automated] - change_price: {:.8f}".format(change_price))

		current_price = query_symbol_price(_symbol)
		if(change_price != 0):
			if(change_price <= 0.00000003): change_price == 0.00000004
			if(change_price > 0 or change_one_price > 0):
				# Giam
				result = bamday(_symbol=_symbol, _saferange=change_price, _budget=_fund)
				bought_price = float(result.get("price"))
				orderId = result.get("orderId")
				clientOrderId = result.get("clientOrderId")
				logger.debug("[automated] - orderId: {}\nclientOrderID: {}".format(orderId, clientOrderId))
				status = result.get("status")
				origQty = float(result.get("origQty"))
				isnextstep = True
			else:
				# Tang			
				logger.debug("[+] - Buying coin {}".format(_symbol))
				change_price = change_price*(-1)
				if(change_price <= 0.00000003): change_price == 0.00000004

				# Stop limit < Limit
				# Mới mua vào nên giá mua chỉ cần cao hơn 1 chút so với hiện tại
				_stopprice = round(current_price+change_price*0.5, _NUMBER_OF_ZERO_DIGIT)
				_limitprice = _stopprice
				result = create_new_order(_symbol=_symbol, _type="STOP_LOSS_LIMIT", _limit_price="{:.8f}".format(round(_limitprice, _NUMBER_OF_ZERO_DIGIT)), _stop_price="{:.8f}".format(_stopprice), _quantity=round(_fund/next_price, _LOT_SIZE_), _side="BUY")
				logger.debug("[*] Result: {}".format(result))
				result = result.decode("utf-8")
				result = json.loads(result)
				orderId = result.get("orderId")
				clientOrderId = result.get("clientOrderId")

				logger.debug("[automated] - orderId: {}\nclientOrderID: {}".format(orderId, clientOrderId))

				isbuy = False
				while (isbuy == False and orderId != None):
					time.sleep(_TIME_TO_DELAY_)
					try:
						result = query_order(_symbol=_symbol, _orderid=orderId, _origClientOrderId=clientOrderId)
						result = result.decode("utf-8")
						logger.debug("[automated] - Result: {}".format(result))
						result = json.loads(result)
						status = result.get("status")
						origQty = float(result.get("origQty"))
						price = float(result.get("price"))
						symbol = result.get("symbol")
						logger.debug(status)
						bought_price = price

						current_price = query_symbol_price(_symbol)
						if(status == "FILLED"):
							isbuy = True
					except Exception as ex:
						logger.debug("[automated] - {}".format(ex))

			isnextstep = True
		else:
			logger.debug("[automated] - Average change to low! Find other coins!")
			send_notification("[automated] - Average change to low! Find other coins!")

		# time.sleep(_TIME_TO_DELAY_)


	logger.info("[automated] - Bought {} {} successful with {:.8f}".format(origQty, _symbol, bought_price))
	send_notification("[automated] - Bought {} {} successful with {:.8f}".format(origQty, _symbol, bought_price))

	# Follow top price
	iswait = True
	while(iswait):
		time.sleep(_TIME_TO_DELAY_/2)
		current_price = query_symbol_price(_symbol)
		logger.info("[automated] - Current price: {:.8f} (Waiting for > {:.8f})".format(current_price, (bought_price+change_price*1.1)))
		if(current_price > bought_price+change_price*1.1):
			logger.debug("[automated] - Buy {}\nSell: >{}".format(current_price, (bought_price+change_price*1.1)))
			iswait = False

	_dutheodinh = dutheodinh(_symbol=_symbol, _saferange=change_price, _quantity=origQty)
	filled_price = float(_dutheodinh.get("price"))
	filled_quantity = float(_dutheodinh.get("origQty"))

	logger.info("[automated] - Sold {} {} successfull with {:.8f}".format(filled_quantity, _symbol, filled_price))
	logger.info(":)")

	global _PROFIT_
	_PROFIT_ = (filled_price-bought_price)*filled_quantity
	with open("profit.data", "a+") as f:
		_now = datetime.now()
		data = "{} - [{}] - {:.8f}\n".format(_now.strftime("%d%m%y %H:%M:%S"), _symbol, _PROFIT_)
		f.write(str(data))
	logger.info("[automated] - _PROFIT_: {:.8f} {}".format(_PROFIT_, _symbol))
	send_notification("[automated] - _PROFIT_: {:.8f} {}".format(_PROFIT_, _symbol))
	return 0
