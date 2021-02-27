import websocket
import json
import pprint
import talib
import numpy as np
import config
from binance.client import Client
from binance.enums import *

SOCKET_SYMBOL = 'adausdt'
INTERVAL = '1m'
SOCKET = f'wss://stream.binance.com:9443/ws/{SOCKET_SYMBOL}@kline_{INTERVAL}'

EMA_PERIOD = 9
MA_PERIOD = 20

TRADE_SYMBOL = 'ADAUSD'
TRADE_QUANTITY = 5

client = Client(api_key=config.API_KEY, api_secret=config.SECRET_KEY)

closes = []
# Keeps track of the position
in_position = False


def order(side, quantity, symbol, order_type=Client.ORDER_TYPE_MARKET):
    """
    Function that place the buy order. This is where magic happens :P

    Params
    ------
    side : str. Either <SIDE_BUY> or <SIDE_SELL>
    quantity : num. Amount to trade with
    symbol : str. cryptocoin + currency
    """
    try:
        print('Sending order...')
        # To place an actual order just use the create_order function
        my_order = client.create_test_order(symbol=symbol,
                                            side=side,
                                            type=order_type,
                                            quantity=quantity)
        print(my_order)
    except Exception as e:
        return False

    return True


def on_open(ws):
    """Informs about an opened connection to the websocket server. GOOD :)"""
    print('opened connection')


def on_close(ws):
    """Informs about a closed connection to the websocket server. BAD :("""
    print('closed connection')


def on_message(ws, message):
    """Gives info about the response received"""
    global closes
    global in_position

    # print('message received')
    json_message = json.loads(message)
    # pprint.pprint(json_message)

    candle = json_message['k']
    close = float(candle['c'])
    is_candle_closed = candle['x']

    if is_candle_closed:
        # print(f'Closed price is {close}')
        closes.append(close)
        # print(f'Closes so far: {closes}')

        if len(closes) > MA_PERIOD:
            np_closes = np.array(closes)
            ema = talib.EMA(np_closes, timeperiod=EMA_PERIOD)
            ma = talib.MA(np_closes, timeperiod=MA_PERIOD)
            print('All EMAs calculated so far: ')
            print(ema)
            print('All simple MA calculated so far: ')
            print(ma)
            last_ema = ema[-1]
            last_ma = ma[-1]

            if last_ema > last_ma:
                if not in_position:
                    print(f'Buy at {close}')
                    # Place a buy order
                    order_succeeded = order(side=Client.SIDE_BUY,
                                            quantity=TRADE_QUANTITY,
                                            symbol=TRADE_SYMBOL)
                    if order_succeeded:
                        in_position = True
                else:
                    print(f'In position at {close}')
            if last_ema < last_ma:
                if in_position:
                    print(f'Sell at {close}')
                    # Place a sell order
                    order_succeeded = order(side=Client.SISE_SELL,
                                            quantity=TRADE_QUANTITY,
                                            symbol=TRADE_SYMBOL)
                    if order_succeeded:
                        in_position = False
                else:
                    print(f'Waiting for an uptrend...')
        print('*' * 50)


ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message)
ws.run_forever()
