import requests
from datetime import datetime
import time
import os
import json
import hmac
import hashlib
import math
import logging
from datetime import datetime

from coin import Coin
from account import Account
from _variables_ import _TIME_TO_DELAY_, _FUND_
from _transaction_handler_ import *
from utils import *
#du theo dinh script

if __name__ == '__main__':
	# symbol = "YFIBNB"
	topcoin = get_top_symbols()
	symbol = topcoin[0].get("symbol")
	user = Account(topcoin[0].get("symbol"))
	read_config()

	while(True):
		if(len(topcoin) > 0):
			# Check top coin
			bl = user.get_balance()

			# send_notification("[{}] - My balance: {}".format(time.asctime(), bl))
			logger.info("My balance: {}".format(bl))

			idx = 0
			ischeck = True
			coinmatrix = []
			while(ischeck):
				symbol = topcoin[idx].get("symbol")
				logger.info("Analyzing coin {}".format(symbol))
				coinmatrix = make_matrix(symbol)
				# print("Matrix: {}".format(coinmatrix))			
				if(anhnlq_check(coinmatrix)):
				# if(1):
					ischeck = False
					break
				else:
					idx += 1
	# 
				if(idx == len(topcoin)-1):
					idx = 0
					bl = user.get_balance()
					send_notification("[{}][+] Can not find potential symbol to trade. Last balance: {}".format(symbol, bl))
					time.sleep(60)
					topcoin = get_top_symbols()


			logger.info("Starting trade {}".format(symbol))
			# send_notification("[{}] - Starting trade {}".format(time.asctime(), symbol))
			targeted_coin = Coin(symbol, _FUND_)
			user = Account(symbol)
			price_one = targeted_coin.get_current_price()
			time.sleep(30)
			price_two = targeted_coin.get_current_price()
			changed = float(price_two) - float(price_one)

			_saferange = changed

			logger.info("Changing popular {:.8f}".format(_saferange))
			if(_saferange > 0):
				isloop = True
				while isloop:
					isloop = False 
					topprice = 0
					# 1. Check price
					if(_saferange < 0): _saferange *=-1
					
					current_price = round(float(targeted_coin.get_current_price()), targeted_coin.lotsize)
					topprice = current_price
					# Stop > limit
					_stopprice = str(round((float(current_price)+_saferange*0.1), targeted_coin.lotsize))
					_limitprice = _stopprice	
					_quantity = str(round(targeted_coin.budget/float(_limitprice), targeted_coin.stepsize))

					logger.info("[{}][main][+]Current price: {}".format(symbol, current_price))
					logger.info("[{}][main][+]_saferange: {:.8f}".format(symbol, _saferange))
					logger.info("[{}][main][+]Limit price: {}".format(symbol, _limitprice))
					logger.info("[{}][main][+]_LOT_SIZE_: {}".format(symbol, targeted_coin.lotsize))
					logger.info("[{}][main][+]STEP: {}".format(symbol, targeted_coin.stepsize))

					result = user.buy(_limitprice, _quantity)

					# Error handler
					if(result.get("code") != 1):
						error = result.get("content")
						logger.info("[{}][main] - Code: {} | msg: {}".format(symbol, error.get("code"), error.get("msg")))
						if(error.get("code") == -2010 and error.get("msg") == "Stop price would trigger immediately."): # Stop price would trigger immediately.
							isloop = True
							_saferange += _saferange*0.5
							time.sleep(1)
						elif("Account has insufficient balance for requested action" in error.get("msg")):# Account has insufficient balance for requested action.
							logger.info("[{}][main] - Code: {} | msg: {}".format(symbol, error.get("code"), error.get("msg")))
							isloop = False
							topcoin.pop(idx)
							break
						else:
							topcoin.pop(idx)

					else:
						transaction_info = result.get("content")
						logger.info("[{}][main] - transaction_info: {} |".format(symbol, transaction_info))
						logger.debug("[{}][main] - Content: {}".format(symbol, transaction_info))
						# if(tranaction.get("status") != "FILLED"): isloop = True
					# End error handler
						result = user.followtop(targeted_coin, changed, transaction_info)
						if(result.get("code") == 1):
							# send_notification("================================")
							send_notification("[{}][{}]\n 🪙💰🪙 Take profit: {:.8f}".format(time.asctime(), symbol, float(result.get("profit"))))
							profit_file = os.path.join("profit", "{}_PROFIT.txt".format(time.strftime("%d_%m")))
							with open(profit_file, "a+") as f:
								f.write(str(result.get("profit")))
								f.write("\n")
							# send_notification("================================")
							topcoin = get_top_symbols()
						else:
							send_notification("🆘 --[{}][{}] \nFollowtop Error!--".format(time.asctime(), symbol))
			elif(changed < 0.0):
				changed *=-1
				# send_notification("[{}][main] - Next round!".format(targeted_coin.symbol))
				logger.info("[{}][main] - Follow bottom".format(targeted_coin.symbol))
				_RETURN_DATA = user.followbottom(targeted_coin, changed)
				if(_RETURN_DATA.get("code") != 1):
					error = _RETURN_DATA.get("content")
					logger.debug("[{}][main] - Error: {}".format(symbol, error))
				else:
					# Result: {'symbol': 'CAKEBNB', 'orderId': 38750556, 'orderListId': -1, 'clientOrderId': 'urh9gJ6gSnIP1fgAROCXlT', 'price': '0.06441000', 'origQty': '1.60000000', 'executedQty': '0.00000000', 'cummulativeQuoteQty': '0.00000000', 'status': 'NEW', 'timeInForce': 'GTC', 'type': 'STOP_LOSS_LIMIT', 'side': 'BUY', 'stopPrice': '0.06441000', 'icebergQty': '0.00000000', 'time': 1617003386324, 'updateTime': 1617003386324, 'isWorking': False, 'origQuoteOrderQty': '0.00000000'}
					transaction_info = _RETURN_DATA.get("content")
					logger.info("[{}][main] - Result: {}".format(targeted_coin.symbol, transaction_info))

					logger.info("[{}][main] - transaction_info: {} |".format(symbol, transaction_info))
					result = user.followtop(targeted_coin, changed, transaction_info)
					if(result.get("code") == 1):
						# send_notification("================================")
						send_notification("[{}][{}]\n 🪙💰🪙 Take profit: {:.8f}".format(time.asctime(), symbol, float(result.get("profit"))))
						profit_file = os.path.join("profit", "{}_PROFIT.txt".format(time.strftime("%d_%m")))
						with open(profit_file, "a+") as f:
							f.write(str(result.get("profit")))
							f.write("\n")
						# send_notification("================================")
						topcoin = get_top_symbols()
					else:
						send_notification("🆘 --[{}][{}] \nFollowtop Error!--".format(time.asctime(), symbol))
		else:
			topcoin = get_top_symbols()