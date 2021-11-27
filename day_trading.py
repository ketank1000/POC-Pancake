

import enum
import traceback
import numpy as np
from datetime            import datetime, timedelta
from time                import sleep

from toolz.itertoolz import drop
from lib                 import constants, helpers
from lib.enums           import Interval, Prediction, Position
from lib.contracts       import Pancake
from lib.alphavintage    import Alpha
from lib.MachineLearning import Model
from lib.utils           import MeasureTime
import talib
from sklearn import preprocessing
import matplotlib.pyplot as plt
import pprint
import mplfinance as mpf



class PredictBNB:
    def __init__(self):
        self.min_bid_amount = constants.MIN_BID
        self.alpha_vintage = Alpha()
        

    def log(self, msg):
        print(f"{datetime.utcnow()} : {msg}")

    def analysis(self):
        data_1min = self.alpha_vintage.get_historical_data(Interval.MIN_1.value)
        diff, vol = helpers.get_candle_difference(data_1min)
        self.log(f"1min diff : {diff}, vol {vol}")
        
        data_5min = self.alpha_vintage.get_historical_data(Interval.MIN_5.value)
        ha_data = self.alpha_vintage.heikin_ashi(data_5min)
        last_candle_ha = ha_data.iloc[-1]
        second_last_candle_ha = ha_data.iloc[-2]

        self.log(f"5 min HA diff : {last_candle_ha.change}, {second_last_candle_ha.change}")
        # self.log(f"1st ha: {last_candle_ha}, 2nd Ha: {second_last_candle_ha}")
        # macd_1min = helpers.macd(data_1min)
        macd_5min = helpers.macd(data_5min)
        in_trend = helpers.adx(data_5min)
        if abs(last_candle_ha.change) > 0.5 and vol < 3000:
            if diff > 0 and last_candle_ha.change > 0 and last_candle_ha.close > second_last_candle_ha.close and second_last_candle_ha.change > 0 and macd_5min == Prediction.BULL:
                self.log(f"Predicting UP for {self.next_round['epoch']}")
                return Prediction.BULL
            elif diff < 0 and last_candle_ha.change < 0 and last_candle_ha.close < second_last_candle_ha.close and second_last_candle_ha.change < 0 and macd_5min == Prediction.BEAR:
                self.log(f"Predicting Down for {self.next_round['epoch']}")
                return Prediction.BEAR
            else:
                self.log(f"Skipping for {self.next_round['epoch']}")
                return Prediction.SKIP
        
        self.log(f"Skipping for {self.next_round['epoch']}")
        return Prediction.SKIP

    def get_data(self):
        data_5min = self.alpha_vintage.get_historical_data('60min', symbol='BNB')
        macd = talib.MACD(data_5min['Close'])
        rsi = talib.RSI(data_5min['Close'])
        data_5min['macd'] = macd[2]
        data_5min['rsi'] = rsi
        data_5min.dropna(subset = ["macd", "rsi"], inplace=True)
        ha_data = self.alpha_vintage.heikin_ashi(data_5min)
        data_5min['ha_open'] = ha_data['Open']
        data_5min['ha_high'] = ha_data['High']
        data_5min['ha_low'] = ha_data['Low']
        data_5min['ha_close'] = ha_data['Close']
        return data_5min

    def plot_graph(self,data, buy_signals, sell_signals):
        buy_plot = mpf.make_addplot(buy_signals, type='scatter', marker='^', markersize=100, panel=0)
        sell_plot = mpf.make_addplot(sell_signals, type='scatter', marker='v', markersize=100, panel=0)
        mpf.plot(data, type='candle', addplot=[buy_plot,sell_plot],warn_too_much_data=10000)

    def caluclate(self, trades):
        profit = 0
        for trade in trades:
            print(trade)
            p = 0
            if trade['position'] == Position.LONG:
                p = trade['exit'] - trade['entry']
                profit += p
            elif trade['position'] == Position.SHORT:
                p = trade['entry'] - trade['exit']
                profit += p
            print(f"profit: {p}\n")
        print(f"Total profit: {profit}")
        return profit

    def make_long_entry_call(self, data, tick):
        ha_candel = data['ha_close'][tick] - data['ha_open'][tick]
        ha_tail = data['ha_open'][tick] - data['ha_low'][tick]
        trade = {}
        if ha_candel > 0  and abs(ha_candel) > 0.5 and data['ha_close'][tick] > data['ha_close'][tick-timedelta(minutes=5)] and ha_tail < 0.2:
            position = Position.LONG
            trade['entry'] = data['Close'][tick]
            trade['position'] = position
            trade['entry_time'] = tick
        
        return trade

    def make_long_exit_call(self, data, tick, sl):
        trade = {}
        if data['ha_close'][tick] < data['ha_close'][tick-timedelta(minutes=5)] or sl > data['Close'][tick]:
            if sl > data['Close'][tick]:
                trade['exit'] = sl
            else:
                trade['exit'] = data['Close'][tick]
            trade['exit_time'] = tick
        
        return trade

    def run(self):
        pp = pprint.PrettyPrinter(indent=4)
        data = self.get_data()
        data.index.name = 'Date'
        print(data)
        position = Position.OUT
        skip_3 = 0
        trades = []
        trade_long = {}
        trade_exit = {}
        sl = 0

        buy_signals = []
        sell_signals = []
        ctr = 0
        for tick in data.index:
            if ctr == 0:
                ctr = 1
                continue
            if position == Position.OUT:
                trade_long = self.make_long_entry_call(data, tick)
                if len(trade_long) > 0:
                    position = trade_long['position']
                    sl = data['Close'][tick] - 3
                    print(trade_long)
            elif position == Position.LONG:
                trade = self.make_long_exit_call(data, tick, sl)
                if len(trade) > 0:
                    print(trade)
                    position = Position.OUT
                    trade_long['exit'] = trade['exit']
                    trade_long['exit_time'] = trade['exit_time']
                    trades.append(trade_long)
                    print()
            new_sl = data['Close'][tick] - 3
            if sl < new_sl:
                # print(new_sl)
                sl = new_sl
        
        #pp.pprint(trades)
        # print(len(trades))
        self.caluclate(trades)
        print((f"Total No of trades : {len(trades)}"))
        #self.plot_graph(data, buy_signals, sell_signals)

    



if __name__ == '__main__':
    st = PredictBNB()
    st.run()

    