

import enum
import traceback
from matplotlib.pyplot import xticks
import numpy as np
from datetime            import datetime
from time                import sleep

from toolz.itertoolz import drop
from lib                 import constants, helpers
from lib.enums           import Interval, Prediction
from lib.contracts       import Pancake
from lib.alphavintage    import Alpha
from lib.MachineLearning import Model
from lib.utils           import MeasureTime
import talib
from sklearn import preprocessing



class PredictBNB:
    def __init__(self):
        self.wins = 0
        self.lose = 0
        self.skip = 0
        self.min_bid_amount = constants.MIN_BID
        self.next_round = None
        self.prev_round = None
        self.prev_prediction = Prediction.SKIP
        self.next_prediction = Prediction.SKIP

        self.pancake_contract = Pancake()
        self.alpha_vintage = Alpha()
        self.Model = Model()
        self.model = None

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

    def run1(self):
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

    def ml(self):
        data_5min = self.alpha_vintage.get_historical_data(Interval.MIN_5.value)
        data_5min.drop(['Volume'], axis=1, inplace=True)
        data_5min = data_5min.reset_index(drop=True)
        macd = talib.MACD(data_5min['Close'])
        rsi = talib.RSI(data_5min['Close'])
        data_5min['macd'] = macd[2]
        data_5min['rsi'] = rsi
        data_5min.dropna(subset = ["macd", "rsi"], inplace=True)
        data_5min = data_5min.reset_index(drop=True)
        print(data_5min)
        print("test")

        self.model = self.Model.get_model()

        cell_timer = MeasureTime(task="Generating reshape unputs")
        X_test,Y_test, X_raw = self.Model.my_generator_candle_X_Y(data_5min.values,5)
        cell_timer.kill()

        print('Shape of X ' + str(X_test.shape))
        print('Shape of Y ' + str(Y_test.shape))
        print('Shape of X raw ohlc ' + str(X_raw.shape))

        unique, counts = np.unique(Y_test, return_counts=True)
        predictions_type = dict(zip(unique, counts))
        print('Bull: ' + str((predictions_type[1])) + ' percent: ' + str(round((predictions_type[1]*100)/len(Y_test),2)) + '%')
        print('Bear: ' + str((predictions_type[0])) + ' percent: ' + str(round((predictions_type[0]*100)/len(Y_test),2)) + '%')
        print('Total: ' + str(len(Y_test)))

        test_acc = self.model.evaluate(X_test, Y_test)
        print('Test accuracy:', test_acc)

        predits = self.model.predict(X_test)
        # print(predits)
        self.Model.validate_prediction(predits, Y_test, X_raw, X_test)
    
    # def make_prediction(self):


    def train_model(self):
        self.Model.training()


    def get_data(self):
        data_5min = self.alpha_vintage.get_historical_data(Interval.MIN_5.value)
        data_5min.drop(['Volume'], axis=1, inplace=True)
        data_5min = data_5min.reset_index(drop=True)
        macd = talib.MACD(data_5min['Close'])
        rsi = talib.RSI(data_5min['Close'])
        data_5min['macd'] = macd[2]
        data_5min['rsi'] = rsi
        data_5min.dropna(subset = ["macd", "rsi"], inplace=True)
        data_5min = data_5min.reset_index(drop=True)
        print(data_5min.tail(3).values)
        return data_5min


    def analysis2(self, data_5min):
        data_1min = self.alpha_vintage.get_historical_data(Interval.MIN_1.value)
        diff = helpers.get_candle_difference(data_1min)
        self.log(f"1min diff : {diff}")
        
        # data_5min = self.alpha_vintage.get_historical_data(Interval.MIN_5.value)
        ha_data = self.alpha_vintage.heikin_ashi(data_5min)
        last_candle_ha = ha_data.iloc[-1]
        second_last_candle_ha = ha_data.iloc[-2]

        self.log(f"5 min HA diff : {last_candle_ha.Change}, {second_last_candle_ha.Change}")
        # self.log(f"1st ha: {last_candle_ha}, 2nd Ha: {second_last_candle_ha}")
        # macd_1min = helpers.macd(data_1min)

        # if diff > 0:
        #     return Prediction.BULL
        # return Prediction.BEAR

        if abs(last_candle_ha.Change) > 0.4 and abs(last_candle_ha.Change) < 3.0 and abs(diff) > 0.5:
            if diff > 0 and last_candle_ha.Change > 0 and last_candle_ha.Close > second_last_candle_ha.Close:
                return Prediction.BULL
            elif diff < 0 and last_candle_ha.Change < 0 and last_candle_ha.Close < second_last_candle_ha.Close:
                return Prediction.BEAR
            else:
                return Prediction.SKIP

            # if diff > 0 and last_candle_ha.Change > 0 and last_candle_ha.close > second_last_candle_ha.close and second_last_candle_ha.change > 0 and macd_5min == Prediction.BULL:
            #     self.log(f"Predicting UP for {self.next_round['epoch']}")
            #     return Prediction.BULL
            # elif diff < 0 and last_candle_ha.change < 0 and last_candle_ha.close < second_last_candle_ha.close and second_last_candle_ha.change < 0 and macd_5min == Prediction.BEAR:
            #     self.log(f"Predicting Down for {self.next_round['epoch']}")
            #     return Prediction.BEAR
            # else:
            #     self.log(f"Skipping for {self.next_round['epoch']}")
            #     return Prediction.SKIP
    
        return Prediction.SKIP
        
    def run2(self):
        self.model = self.Model.get_model()
        while True:
            try:
                present_time = datetime.utcnow()
                print(present_time.second, present_time.minute, 5 - present_time.minute%5)
                wait = 60 - present_time.second + (4 - present_time.minute % 5)*60 - 30
                if wait < 0:
                    break
                self.log(f"Waiting for next round {wait}")
                sleep(wait)
                data_5min = self.get_data()
                cell_timer = MeasureTime(task="Generating reshape unputs")
                X_test, X_raw = self.Model.last_candel_generator_X(data_5min.tail(3).values)
                print(X_test)
                predits = self.model.predict(X_test)
                predit = predits[0][0]
                print(predit)
                cell_timer.kill()

                alpha_distance = 0.1
                self.prev_prediction = self.next_prediction
                if (predit > (1-alpha_distance) or predit < alpha_distance):
                    analyis = self.analysis2(data_5min)
                    if predit > (1-alpha_distance) and analyis == Prediction.BULL:
                        self.next_prediction = Prediction.BULL
                    elif predit < alpha_distance and analyis == Prediction.BEAR:
                        self.next_prediction = Prediction.BEAR
                    else:
                        self.next_prediction = Prediction.SKIP
                else:
                    self.next_prediction = Prediction.SKIP
                self.log(f"Making prediction {self.next_prediction}")

                self.log(f"Waiting for round to complete {100}")
                sleep(100)
                data_5min = self.alpha_vintage.get_historical_data(Interval.MIN_5.value)

                if self.prev_prediction == Prediction.SKIP:
                    self.skip += 1
                    self.log("SKIPPED")
                else:
                    print(data_5min.iloc[-2].Close,data_5min.iloc[-3].Close)
                    if data_5min.iloc[-2].Close > data_5min.iloc[-3].Close and self.prev_prediction == Prediction.BULL:
                        self.wins += 1
                        self.log("WON")
                    elif data_5min.iloc[-2].Close < data_5min.iloc[-3].Close and self.prev_prediction == Prediction.BEAR:

                        self.wins += 1
                        self.log("WON")
                    else:
                        self.lose += 1
                        self.log("LOST")

                self.print_summary()

            except Exception as e:
                traceback.print_exc()
                self.log(f"Error found {e}")

    def testing(self):
        data_5min = self.alpha_vintage.get_historical_data(Interval.MIN_5.value)
        data_5min.drop(['Volume'], axis=1, inplace=True)
        data_5min = data_5min.reset_index(drop=True)
        macd = talib.MACD(data_5min['Close'])
        rsi = talib.RSI(data_5min['Close'])
        data_5min['macd'] = macd[2]
        data_5min['rsi'] = rsi
        data_5min.dropna(subset = ["macd", "rsi"], inplace=True)
        data_5min = data_5min.reset_index(drop=True)
        print(data_5min)
        print("test")

        X_test,Y_test, X_raw = self.Model.my_generator_candle_X_Y(data_5min.values,3)

        for i in range(len(X_test)):
            temp = ""
            for j in range(3):
                temp += f", {X_test[i][j][3]}"
            
            temp += f", {Y_test[i]}"
            print(temp)



if __name__ == '__main__':
    st = PredictBNB()
    st.ml()
    # st.train_model()
    # st.run2()

    # st.testing()

    