import os
import alpaca_trade_api as tradeapi
import pandas as pd
import smtplib
import pytz
import backtrader as bt
from datetime import datetime
from local_settings import alpaca_paper
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from alpaca_trade_api import Stream
from alpaca_trade_api.rest import REST
from alpaca_trade_api.rest import TimeFrame
import time
import logging

from alpaca_trade_api.common import URL


log = logging.getLogger(__name__)

API_KEY = "PKIHG91TD1R31CCNSIOK"
API_SECRET_KEY = "fss3ViRWiFjn8LAYHHCSLbG5CM3hqbt1ebRUw5db"
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"
ALPACA_STREAM_URL = "wss://paper-api.alpaca.markets/stream"
api = tradeapi.REST()
account = api.get_account()

#The mail addresses and password
sender_address = "jajohnson.dev@gmail.com"
sender_pass = "@xFxO=VEl!zk8%1v{0cW"
receiver_address = "jajohnson303@gmail.com"

#Setup the MIME
message = MIMEMultipart()
message['From'] = 'Trading Bot'
message['To'] = receiver_address
message['Subject'] = 'Pairs Trading Algo'

#Selection of stocks
days = 1000
stock1 = 'ADBE'
stock2 = 'AAPL'

#Put Historical data in variables
stock1_barset = api.get_barset(stock1, 'day', limit = days)
stock2_barset = api.get_barset(stock2, 'day', limit = days)
stock1_bars = stock1_barset[stock1]
stock2_bars = stock2_barset[stock2]

#grab stock1 & stock2 data and put into an array
data_1 = []
times_1 = []
data_2 = []
times_2 = []
for i in range(days):
    stock1_close = stock1_bars[i].c
    stock2_close = stock2_bars[i].c
    stock1_time = stock1_bars[i].t
    stock2_time = stock2_bars[i].t
    data_1.append(stock1_close)
    data_2.append(stock2_close)
    times_1.append(stock1_time)
    times_2.append(stock2_time)

#Putting them together
hist_close = pd.DataFrame(data_1, columns=[stock1])
hist_close[stock2] = data_2

#Current Spread between the two stocks
stock1_curr = data_1[days - 1]
stock2_curr = data_2[days - 1]
spread_curr = (stock1_curr - stock2_curr)

#Moving average of the two stocks
move_avg_days = 5
stock1_last = []
stock2_last = []
for i in range(move_avg_days):
    stock1_last.append(data_1[(days - 1) - i])
    stock2_last.append(data_2[(days - 1) - i])
    print(data_1[(days - 1) - i])
    print(data_2[(days - 1) - i])
stock1_hist = pd.DataFrame(stock1_last)
stock2_hist = pd.DataFrame(stock2_last)
stock1_mavg = stock1_hist.mean()
stock2_mavg = stock2_hist.mean()

#Spread_average
spread_avg = min(stock1_mavg - stock2_mavg)
spreadFactor = .01
wideSpread = spread_avg * (1 + spreadFactor)
thinSpread = spread_avg * (1 - spreadFactor)

#Calc_of_shares_to_trade
cash = float(account.buying_power)
limit_stock1 = cash // stock1_curr
limit_stock2 = cash // stock2_curr
number_of_shares = int(min(limit_stock1, limit_stock2) / 2)

#Trading_algo
portfolio = api.list_positions()
clock = api.get_clock()

if clock.is_open == True:
    if bool(portfolio) == False:
        #detect a wide spread
        if spread_curr > wideSpread:
            #short stock1
            api.submit_order(symbol = stock1, qty = number_of_shares, side = 'sell', type = 'market', time_in_force = 'day')
            #long stock2
            api.submit_order(symbol = stock2, qty = number_of_shares, side = 'buy', type = 'market', time_in_force = 'day')
            mail_content = "Trades have been made, short stock: [ " + stock1 + " ] and long stock: [ " + stock2 + " ]"
        #detect a tight spread
        elif spread_curr < thinSpread:
            #long stock1
            api.submit_order(symbol = stock1, qty = number_of_shares, side = 'buy', type = 'market', time_in_force = 'day')
            #short stock2
            api.submit_order(symbol = stock2, qty = number_of_shares, side = 'sell', type = 'market', time_in_force = 'day')
            mail_content = "Trades have been made, long stock: [ " + stock1 + " ] and short stock: [ " + stock2 + " ]"
    else:
        wideTradeSpread = spread_avg *(1+spreadFactor + .03)
        thinTradeSpread = spread_avg *(1+spreadFactor - .03)
        if spread_curr <= wideTradeSpread and spread_curr >=thinTradeSpread:
            api.close_position(stock1)
            api.close_position(stock2)
            mail_content = "Position has been closed for [ " + stock1 + " & " + stock2 + " ]"
        else:
            mail_content = "No trades were made, position remains open"
            pass
else:
    mail_content = "The Market is Closed"

#The body and the attachments for the mail
message.attach(MIMEText(mail_content, 'plain'))
#Create SMTP session for sending the mail
session = smtplib.SMTP('smtp.gmail.com', 587) #use gmail with port
session.starttls() #enable security
session.login(sender_address, sender_pass) #login with mail_id and password
text = message.as_string()
session.sendmail(sender_address, receiver_address, text)
session.quit()

done = 'Main Sent'

print(done)
