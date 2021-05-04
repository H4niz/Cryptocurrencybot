import requests
from datetime import datetime
import time
import json
import os
import hmac
import hashlib
import math
import logging
from datetime import datetime

_CONFIG_FILE_PATH_ = r"configuration.conf"
_BASE_API_= ["https://api.binance.com", "https://api1.binance.com", "https://api2.binance.com", "https://api3.binance.com"]
_GENERAL_API_LIST = {"PING": "api/v3/ping", "GETSVRTIME": "api/v3/time", "EXCINFO": "api/v3/exchangeInfo", "TIKER_PRICE":"api/v3/ticker/price", "TIKER_STATISTICS": "api/v3/ticker/24hr", "CANDLESTICK": "api/v3/klines"}
_ACCOUNT_API_ = {"ORDER": "api/v3/order", "QUERY_ORDER": "api/v3/order", "BALANCE": "api/v3/account", "MYTRADE": "api/v3/myTrades"}

_TOP_CHANGE_COIN_DB_ = os.path.join("databases", "top_change_coin.dat")

# Telegram
_TELEGRAM_BOT_TOKEN_ = ""
_CHATID_ = 0

# Market
_MARKET_ = "BNB"
_RANGEPRICE_ = 1.3
_TIME_TO_DELAY_ = 10
_FUND_ = 0.07

_LOG_PATH_ = "logs"
logger = logging.getLogger("CCOIN")
_log_file_ = "pricehunter_{}.log".format(time.time())
fulllogpath = os.path.join(_LOG_PATH_, _log_file_)
logging.basicConfig(filename=fulllogpath)
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - [%(name)s][%(levelname)s]:%(message)s", datefmt='%m/%d/%Y %I:%M:%S %p')
		
# add formatter to ch
ch.setFormatter(formatter)
# add ch to logger
logger.addHandler(ch)