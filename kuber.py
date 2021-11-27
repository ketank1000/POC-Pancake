

import traceback
from datetime           import datetime
from time               import sleep
from pandas.core.window.rolling import Window
from lib                import constants, helpers
from lib.enums          import Interval, Prediction
from lib.contracts      import Pancake
from lib.alphavintage   import Alpha



class PredictBNB:
    def __init__(self):
        self.wins = 0
        self.lose = 0
        self.skip = 0
        self.min_bid_amount = constants.MIN_BID
        self.next_round = None
        self.prev_round = None
        self.prev_prediction = None
        self.next_prediction = None

        self.pancake_contract = Pancake()
        self.alpha_vintage = Alpha()

    def log(self, msg):
        print(f"{datetime.utcnow()} : {msg}")

    
    def print_summary(self):
        profit = 0
        rate = 0
        if (self.wins+self.lose) != 0:
            rate = (self.wins/(self.wins+self.lose))*100
            profit = self.min_bid_amount*self.wins*0.6 - self.min_bid_amount*self.lose
        print('\nSummary:')
        print(f' Wins/Lose/skip: {self.wins}/{self.lose}/{self.skip}')
        print(f' Win rate: {rate} %')
        print(f" Profit: {profit} $ (bid amt: {self.min_bid_amount})\n")
        with open('data/output.txt','w') as output:
            output.write("Summary :\n")
            output.write(f' Wins/Lose/skip: {self.wins}/{self.lose}/{self.skip}\n')
            output.write(f' Rate: {rate} %\n')
            output.write(f" Profit: {profit} $ (bid amt: {self.min_bid_amount}, M: 1.6x)\n")

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

    def run(self):
        while True:
            try:
                self.prev_round = self.next_round
                self.pancake_contract.wait_for_next_round()
                self.next_round = self.pancake_contract.get_round_details()

                self.prev_prediction = self.next_prediction
                self.next_prediction = self.analysis()
                
                # if prev rount is None
                current_epoch = self.next_round['epoch'] - 1
                print(f"Waiting for current round {current_epoch} to complete : {50}s")
                sleep(50)

                if self.prev_prediction == None:
                    continue
 
                if self.prev_prediction == Prediction.SKIP:
                    self.log(f"Skipped for {self.prev_round['epoch']}")
                    self.skip += 1
                else:
                    results = self.pancake_contract.get_prediction(self.prev_round['epoch'])
                    self.log(f"Result {results}")
                    if results == self.prev_prediction:
                        self.log(f"Win for {self.prev_round['epoch']}")
                        self.wins += 1
                    else:
                        self.log(f"Lost for {self.prev_round['epoch']}")
                        self.lose += 1

                self.print_summary()
                
            except Exception as e:
                traceback.print_exc()
                self.log(f"Error found {e}")


if __name__ == '__main__':
    st = PredictBNB()
    st.run()

    