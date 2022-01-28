"""
Current results: (15000 epochs)
    Win/lose: 38/23 (62.295081967213115%)
    Profit: 3.599999999999998 $

Current results: (15000 epochs)
    Win/lose: 186/153 (54.86725663716814%)
    Profit: -22.80000000000001 $
"""

import json
from os import EX_SOFTWARE
from typing_extensions import Required
import talib
import pandas as pd
from utils.contracts      import Pancake
from utils import enums

class KuberPancake:
    def __init__(self) -> None:
        self.pancake = Pancake()
        self.start_epoch = 10000
        self.end_epoch = 25000
        self.bnb_1m = None
        self.bnb_5m = None
        self.bnb_15m = None
        self.rounds = None
        self.wins = 0
        self.lose = 0

    def get_pancake_data(self):
        
        epoch_data = {}
        # st -> 10000
        # end -> 25000
        for epoch in range(self.start_epoch,self.end_epoch):
            print(f"getting {epoch}")
            epoch_data[epoch] = self.pancake.get_round_details(epoch)
            
        print(len(epoch_data))
        print(epoch_data[24999])
        with open('data/rounds.json', 'w') as fp:
            json.dump(epoch_data, fp)

    def collect_data(self):

        # Read rounds
        with open('data/rounds.json') as f:
            self.rounds = json.load(f)
        
        # Read 1 min data
        self.bnb_1m = self.read_data('1m')
        self.bnb_1m['macd'] = talib.MACD(self.bnb_1m['Close'])[0]
        self.bnb_1m['macd_signal'] = talib.MACD(self.bnb_1m['Close'])[1]
        self.bnb_1m['macd_hist'] = talib.MACD(self.bnb_1m['Close'])[2]
        self.bnb_1m['rsi'] = talib.RSI(self.bnb_1m['Close'])

        # Read 5 min data
        self.bnb_5m = self.read_data('5m')
        self.bnb_5m['ema'] = talib.EMA(self.bnb_5m['Close'], timeperiod=50)
        self.bnb_5m['rsi'] = talib.RSI(self.bnb_5m['Close'])

        # Read 15 min data
        self.bnb_15m = self.read_data('15m')
        self.bnb_15m['ema'] = talib.EMA(self.bnb_15m['Close'], timeperiod=50)
        self.bnb_15m['rsi'] = talib.RSI(self.bnb_15m['Close'])

        print(self.bnb_1m)
        print(self.bnb_5m)
        print(self.bnb_15m)
        

    def read_data(self, interval):
        
        bnb = pd.read_json(f'data/BNB_USDT-{interval}.json')
        #self.bnb = self.bnb.set_index(0)
        mapping = {
            bnb.columns[0]: 'Date',
            bnb.columns[1]: 'Open',
            bnb.columns[2]: 'High',
            bnb.columns[3]: 'Low',
            bnb.columns[4]: 'Close',
            bnb.columns[5]: 'Volume'
        }
        bnb = bnb.rename(columns=mapping)
        return bnb

    def heikin_ashi(self, df):
        df_ha = pd.DataFrame(index=df.index.values, columns=['Open', 'High', 'Low', 'Close', 'Change'])
        df_ha['Close'] = (df['Open'] + df['High'] + df['Low'] + df['Close']) / 4
        
        #print(df.iloc[0])
        for i in range(len(df)):
            if i == 0:
                df_ha.iat[0, 0] = df['Open'].iloc[0]
            else:
                df_ha.iat[i, 0] = round((df_ha.iat[i-1, 0] + df_ha.iat[i-1, 3]) / 2,3)
            
        df_ha['High'] = df.loc[:, ['Open', 'Close']].join(df['High']).max(axis=1)
        df_ha['Low'] = df.loc[:, ['Open', 'Close']].join(df['Low']).min(axis=1)
        df_ha['Change'] = df_ha['Close'] - df_ha['Open']

        return df_ha

    def get_macd_crossed(self, index):
        # print(self.bnb[index-3:index])

        if self.bnb_1m.iloc[index].macd > 0 and self.bnb_1m.iloc[index].macd_signal > 0:
            if self.bnb_1m.iloc[index-2].macd_hist > 0 and self.bnb_1m.iloc[index].macd_hist < 0:
                start = index - 3
                no_of_hist_switched = 0
                direction = True
                while self.bnb_1m.iloc[start].macd > 0 and self.bnb_1m.iloc[start].macd_signal > 0:
                    if self.bnb_1m.iloc[start].macd_hist < 0 and direction == True:
                        no_of_hist_switched += 1
                        direction = False
                    elif self.bnb_1m.iloc[start].macd_hist > 0 and direction == False:
                        no_of_hist_switched += 1
                        direction = True
                    start -= 1
                if no_of_hist_switched >= 1:
                    #print(f"no changes : {no_of_hist_switched}")
                    return enums.Prediction.BEAR
        elif self.bnb_1m.iloc[index].macd < 0 and self.bnb_1m.iloc[index].macd_signal < 0:
            if self.bnb_1m.iloc[index-2].macd_hist < 0 and self.bnb_1m.iloc[index].macd_hist > 0:
                start = index - 3
                no_of_hist_switched = 0
                direction = True
                while self.bnb_1m.iloc[start].macd < 0 and self.bnb_1m.iloc[start].macd_signal < 0:
                    if self.bnb_1m.iloc[start].macd_hist > 0 and direction == True:
                        no_of_hist_switched += 1
                        direction = False
                    elif self.bnb_1m.iloc[start].macd_hist < 0 and direction == False:
                        no_of_hist_switched += 1
                        direction = True
                    start -= 1
                if no_of_hist_switched >= 1:
                    #print(f"no changes : {no_of_hist_switched}")
                    return enums.Prediction.BULL
        return enums.Prediction.SKIP

    def get_sma_crossed(self, index_5m, index_15m):
        if self.bnb_5m.iloc[index_5m].ema > self.bnb_15m.iloc[index_15m].ema:
            return enums.Prediction.BULL
        return enums.Prediction.BEAR

    def validate_prediction(self, round, prediction):
        actual_prediction = None
        if round['lockPrice'] < round['closePrice']:
            actual_prediction = enums.Prediction.BULL
        elif round['lockPrice'] > round['closePrice']:
            actual_prediction = enums.Prediction.BEAR
        else:
            actual_prediction = enums.Prediction.SKIP

        if prediction == actual_prediction:
            self.wins += 1
            print(f'won : {self.wins} {round} {prediction}')
        else:
            self.lose += 1
            print(f'lose : {self.lose} {round} {prediction}')




    def strategy(self):
        for epoch in range(self.start_epoch, self.end_epoch):
            round = self.rounds[f"{epoch}"]
            epoch_required = int(round["startTimestamp"])//60 * 60000
            index_1m = self.bnb_1m.index.get_loc(self.bnb_1m.index[self.bnb_1m['Date'] == epoch_required][0])
            prediction_macd = self.get_macd_crossed(index_1m)
            epoch_required = (int(round["startTimestamp"]) - int(round["startTimestamp"])%(5*60))*1000
            index_5m = self.bnb_5m.index.get_loc(self.bnb_5m.index[self.bnb_5m['Date'] == epoch_required][0])
            epoch_required = (int(round["startTimestamp"]) - int(round["startTimestamp"])%(15*60))*1000
            index_15m = self.bnb_15m.index.get_loc(self.bnb_15m.index[self.bnb_15m['Date'] == epoch_required][0])
            prediction_ema = self.get_sma_crossed(index_5m, index_15m)

            prediction = enums.Prediction.SKIP
            if prediction_macd == enums.Prediction.BULL and prediction_ema == enums.Prediction.BULL: # and self.bnb_1m.loc[index_1m].rsi < 50:
                prediction = enums.Prediction.BULL
            elif prediction_macd == enums.Prediction.BEAR and prediction_ema == enums.Prediction.BEAR: # and self.bnb_1m.loc[index_1m].rsi > 50:
                prediction = enums.Prediction.BEAR
            
            if prediction != enums.Prediction.SKIP:
                self.validate_prediction(round, prediction)
                print(f"{index_1m},{index_5m},{index_15m}")
                print(f"{self.bnb_5m.iloc[index_5m].ema} / {self.bnb_15m.iloc[index_15m].ema}")
                print(self.bnb_1m.loc[index_1m-3:index_1m])
                # print(self.bnb_5m.loc[index_5m-3:index_5m])
                # print(self.bnb_15m.loc[index_15m-3:index_15m])

        print(f"Win/lose: {self.wins}/{self.lose} ({(self.wins/(self.wins+self.lose))*100}%)")
        print(f"Profit: {self.wins*0.7 - self.lose} $")

    def init(self):
        # self.get_pancake_data()
        self.collect_data()
        self.strategy()


if __name__ == '__main__':
    st = KuberPancake()
    st.init()