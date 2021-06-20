import alpaca_trade_api as tradeapi
from alpaca_trade_api import Stream, StreamConn
import time
import logging

from alpaca_trade_api.common import URL

API_KEY = "PKI8I2YJ0HQSSNPW35VW"
API_SECRET_KEY = "PGMRSa25PoTI5FpVozsyr9dErCdV4COwdNaKO1QU"
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"
ALPACA_STREAM_URL = "wss://paper-api.alpaca.markets/stream"

log = logging.getLogger(__name__)

class pyTradingBot:
    def __init__(self):
        self.alpaca = tradeapi.REST(API_KEY, API_SECRET_KEY, ALPACA_BASE_URL, api_version="v2")
        print("ACCOUNT STATUS: [ %s ]" % self.alpaca.get_account().status)
    def run(self):
        print("RUN METHOD")
        logging.basicConfig(level=logging.INFO)
        async def on_minute(conn, channel, bar):
            symbol = bar.symbol
            print("Close: ", bar.close)
            print("Open: ", bar.open)
            print("Low: ", bar.low)
            print("Symbol: ", symbol)
            if bar.close >= bar.open and bar.open - bar.low > 0.1:
                print("buying on doji candle!")
                self.alpaca.submit_order(symbol, 1 , 'buy', 'market', 'day') 
        conn = Stream(API_KEY, API_SECRET_KEY, base_url=URL(ALPACA_BASE_URL), data_feed='iex')
        on_minute = conn.on(r'AM$')(on_minute)
        conn.run(['AM.MFST'])

        async def trade_callback(t):
            print('Trade: ', t)

        async def quote_callback(q):
            print('Quote: ', q)
        
        async def print_trade_updates(tu):
            print('Trade Update: ', tu)

        stream = Stream(API_KEY, API_SECRET_KEY, base_url=URL(ALPACA_BASE_URL), data_feed='iex')
        stream.subscribe_trade_updates(print_trade_updates)
        stream.subscribe_trades(trade_callback, "GME")
        stream.subscribe_quotes(quote_callback, "IBM")

        @stream.on_bar('MFST')
        async def _(bar):
            print('bar', bar)

        stream.run()
       


#Run class
bd = pyTradingBot()
bd.run()
