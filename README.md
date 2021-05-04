## Description
Using curves fitting to detect trending of cryptocurrency. 
![image](https://github.com/H4niz/Cryptocurrencybot/blob/main/Chart/passing_symbol_1620140601.8311422.jpg)

![image](https://github.com/H4niz/Cryptocurrencybot/blob/main/Chart/lossing_symbol_1620140487.8995934.jpg)

## Configuration
Cấu hình các giá trị sau trong tệp tin cấu hình: ./configuration.conf
- _TIME_TO_DELAY_=15
- _API_KEY_=
- _SECRET_KEY_=
- _LOG_PATH_=
- _TELEGRAM_BOT_TOKEN_=
- _CHATID_=

Cấu hình các giá trị sau trong tệp tin _variable.py để lựa chọn thị trường và các giá trị khoảng giá phù hợp trong lúc trade.
- _MARKET_ = "BNB"
- _RANGEPRICE_ = 1.3 # khoảng cách giữa top và giá đặt
- _TIME_TO_DELAY_ = 10 # thời gian kiểm tra thị trường
- _FUND_ = 0.07 #số tiền muốn bỏ ra trade
