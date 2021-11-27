
from keras.callbacks import ModelCheckpoint
import numpy as np
import pandas as pd
from keras.models import Sequential, load_model
from keras.layers.core import Dense, Dropout
from keras.layers.recurrent import GRU, LSTM
from matplotlib import pyplot as plt
from sklearn import preprocessing
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from mplfinance.original_flavor import candlestick_ohlc
from lib.utils import MeasureTime
import talib



class Model:

    def __init__(self):
        self.model_name = "BNB-LSTM-Ratio"
        self.historic_data = 'data/BNBALL.csv'

    def graph_data_ohlc(self, dataset):
        fig = plt.figure()
        ax1 = plt.subplot2grid((1,1), (0,0))
        closep=dataset[:,[3]]
        highp=dataset[:,[1]]
        lowp=dataset[:,[2]]
        openp=dataset[:,[0]]
        date=range(len(closep))

        x = 0
        y = len(date)
        ohlc = []
        while x < y:
            append_me = date[x], openp[x], highp[x], lowp[x], closep[x]
            ohlc.append(append_me)
            x+=1
        candlestick_ohlc(ax1, ohlc, width=0.4, colorup='#77d879', colordown='#db3f3f')
        for label in ax1.xaxis.get_ticklabels():
            label.set_rotation(45)
        ax1.xaxis.set_major_locator(mticker.MaxNLocator(10))
        ax1.grid(True)
        plt.xlabel('Candle')
        plt.ylabel('Price')
        plt.title('Candlestick sample representation')

        plt.subplots_adjust(left=0.09, bottom=0.20, right=0.94, top=0.90, wspace=0.2, hspace=0)
        plt.show()

    def my_generator(self, data, lookback):
        final_output = []
        counter = 0
        first_row = 0
        arr = np.empty((1,lookback,4), int)
        for a in range(len(data)-lookback):
            temp_list = []
            for candle in data[first_row:first_row+lookback]:
                temp_list.append(candle)
            temp_list2 = np.asarray(temp_list)
            templist3 = [temp_list2]
            templist4 = np.asarray(templist3)
            arr = np.append(arr, templist4, axis=0)
            first_row=first_row+1
        return arr

    def ohlc_to_candlestick(self, conversion_array):
        candlestick_data = [0,0,0,0,0,0]
        #print(conversion_array)

        if conversion_array[3]>conversion_array[0]:
            candle_type=1
            wicks_up=abs(conversion_array[1]-conversion_array[3])
            wicks_down=abs(conversion_array[2]-conversion_array[0])
            body_size=abs(conversion_array[3]-conversion_array[0])

        else:
            candle_type=0
            wicks_up=abs(conversion_array[1]-conversion_array[0])
            wicks_down=abs(conversion_array[2]-conversion_array[3])
            body_size=abs(conversion_array[0]-conversion_array[3])

        candlestick_data[0]=candle_type
        # convert in ratio
        total = wicks_down + wicks_up + body_size
        # wicks_up = (wicks_up/total)*100
        # wicks_down = (wicks_down/total)*100
        # body_size = (body_size/total)*100

        # candlestick_data[1]=round(wicks_up,2)
        # candlestick_data[2]=round(wicks_down,2)
        # candlestick_data[3]=round(body_size,2)

        candlestick_data[1]=round(round(wicks_up,5)*10000,2)
        candlestick_data[2]=round(round(wicks_down,5)*10000,2)
        candlestick_data[3]=round(round(body_size,5)*10000,2)
    
        # candlestick_data[4]=conversion_array[4]
        # candlestick_data[5]=round(conversion_array[5],2)
        # candlestick_data[6]=round(conversion_array[6],2)

        # macd and rsi
        candlestick_data[4]=round(conversion_array[4],2)
        candlestick_data[5]=round(conversion_array[5],2)

        print(candlestick_data)
        return candlestick_data

    def my_generator_candle(self, data,lookback):
        first_row = 0
        arr = np.empty((1,lookback,4), int)
        for a in range(len(data)-lookback):
            temp_list = []
            for candle in data[first_row:first_row+lookback]:
                converted_data = self.ohlc_to_candlestick(candle)
                temp_list.append(converted_data)
            temp_list2 = np.asarray(temp_list)
            templist3 = [temp_list2]
            templist4 = np.asarray(templist3)
            arr = np.append(arr, templist4, axis=0)
            first_row=first_row+1
        return arr

    def my_generator_candle_X_Y(self, data,lookback,MinMax = False):
        if MinMax==True:scaler = preprocessing.MinMaxScaler()
        first_row = 0
        arr = np.empty((0,lookback,6))
        arr3 = np.empty((0,lookback,6))
        Y_list = []
        for a in range(len(data)-lookback):
            temp_list = []
            temp_list_raw = []
            for candle in data[first_row:first_row+lookback]:
                converted_data = self.ohlc_to_candlestick(candle)
                temp_list.append(converted_data)
                temp_list_raw.append(candle)
            temp_list3 = [np.asarray(temp_list)]
            templist4 = np.asarray(temp_list3)
            # print(templist4)

            if MinMax==True:
                templist99 = scaler.fit_transform(templist4[0])
                arr = np.append(arr, [templist99], axis=0)
            else:
                arr = np.append(arr, templist4, axis=0)

            temp_list7 = [np.asarray(temp_list_raw)]
            templist8 = np.asarray(temp_list7)
            # print(templist8,arr3)
            arr3 = np.append(arr3, templist8, axis=0)

            converted_data_prediction = self.ohlc_to_candlestick(data[first_row+lookback])
            prev = data[first_row+lookback - 1]
            curr = data[first_row+lookback]
            Prediction = 0
            if prev[3] < curr[3]:
                Prediction = 1
            # Prediction = converted_data_prediction[0]
            Y_list.append(Prediction)

            first_row=first_row+1

        arr2 = np.asarray(Y_list)

        return arr,arr2,arr3

    def last_candel_generator_X(self, data,lookback=3,MinMax = False):
        if MinMax==True:scaler = preprocessing.MinMaxScaler()
        arr = np.empty((0,lookback,6))
        arr3 = np.empty((0,lookback,6))

        temp_list = []
        temp_list_raw = []
        for candle in data:
            converted_data = self.ohlc_to_candlestick(candle)
            temp_list.append(converted_data)
            temp_list_raw.append(candle)
        temp_list3 = [np.asarray(temp_list)]
        templist4 = np.asarray(temp_list3)

        if MinMax==True:
            templist99 = scaler.fit_transform(templist4[0])
            arr = np.append(arr, [templist99], axis=0)
        else:
            arr = np.append(arr, templist4, axis=0)

        temp_list7 = [np.asarray(temp_list_raw)]
        templist8 = np.asarray(temp_list7)
        arr3 = np.append(arr3, templist8, axis=0)

        return arr,arr3

    def testing(self):
        my_dataset = pd.read_csv(self.historic_data)

        my_dataset.drop(['Volume'], axis=1, inplace=True)

        macd = talib.MACD(my_dataset['Close'])
        rsi = talib.RSI(my_dataset['Close'])
        my_dataset['macd'] = macd[2]
        my_dataset['rsi'] = rsi
        my_dataset.dropna(subset = ["macd", "rsi"], inplace=True)
        my_dataset = my_dataset.reset_index(drop=True)
        print(my_dataset)
        

        cell_timer = MeasureTime(task="Generating reshape unputs")
        X,Y, X_raw = self.my_generator_candle_X_Y(my_dataset.values,3)
        print(X)

    def training(self):
        my_dataset = pd.read_csv(self.historic_data)

        my_dataset.drop(['Volume'], axis=1, inplace=True)

        macd = talib.MACD(my_dataset['Close'])
        rsi = talib.RSI(my_dataset['Close'])
        my_dataset['macd'] = macd[2]
        my_dataset['rsi'] = rsi
        my_dataset.dropna(subset = ["macd", "rsi"], inplace=True)
        my_dataset = my_dataset.reset_index(drop=True)
        print(my_dataset)
        

        cell_timer = MeasureTime(task="Generating reshape unputs")
        X,Y, X_raw = self.my_generator_candle_X_Y(my_dataset.values,5)
        cell_timer.kill()

        print('Shape of X ' + str(X.shape))
        print('Shape of Y ' + str(Y.shape))
        print('Shape of X raw ohlc ' + str(X_raw.shape))

        unique, counts = np.unique(Y, return_counts=True)
        predictions_type = dict(zip(unique, counts))
        print('Bull: ' + str((predictions_type[1])) + ' percent: ' + str(round((predictions_type[1]*100)/len(Y),2)) + '%')
        print('Bear: ' + str((predictions_type[0])) + ' percent: ' + str(round((predictions_type[0]*100)/len(Y),2)) + '%')
        print('Total: ' + str(len(Y)))

        # model = Sequential()
        # model.add(GRU(units=512,
        #             return_sequences=True,
        #             input_shape = (None, X.shape[-1])))
        # model.add(Dropout(0.2))
        # model.add(GRU(units=256))
        # model.add(Dropout(0.2))
        # model.add(Dense(1, activation='sigmoid'))
        # model.compile(loss='mse', optimizer='adam')

        model = Sequential()
        model.add(LSTM(units = 1024,return_sequences=True, input_shape = (None, X.shape[-1])))
        model.add(LSTM(units = 526))
        model.add(Dense(units = 1,activation='sigmoid'))
        model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['acc'])

        # model = Sequential()
        # model.add(LSTM(units = 50,return_sequences=True, input_shape = (None, X.shape[-1])))
        # model.add(Dropout(0.1))
        # model.add(LSTM(units = 50, return_sequences=True))
        # model.add(Dropout(0.1))
        # model.add(LSTM(units = 50))
        # model.add(Dropout(0.1))
        # model.add(Dense(units = 1))
        # model.compile(optimizer='adam', loss='mean_squared_error')

        cell_timer = MeasureTime(task="Training Model")
        #checkpoint = ModelCheckpoint(f"{self.model_name}.h5", save_freq='epoch')
        # model.fit(X ,Y ,batch_size=250, epochs=500, verbose=1, callbacks=[checkpoint])
        model.fit(X ,Y ,batch_size=500, epochs=100, verbose=1)
        model.save(f"{self.model_name}.h5")
        cell_timer.kill()
        print("Model Saved")

    def validate_prediction(self, predictions, Y_test, X_test_raw, X_test):
        cell_timer = MeasureTime(task="Validating predictions")
        counter = 0
        won = 0
        lost = 0
        alpha_distance = 0.1
        #print(predictions)

        for a in predictions:
            # print(a, Y_test[counter])
            skip = False
            # for candel in X_test[counter]:
            #     if candel[3] < 0.2:
            #         skip = True
            #         break
            if (a > (1-alpha_distance) or a < alpha_distance) and not skip:
            #if a == 1.0 or a == 0.0:
                print(a)
                #print(X_test_raw[counter])
                #print(X_test[counter])
                if Y_test[counter] == 1:print('Correct prediction is Bullish')
                if Y_test[counter] == 0:print('Correct prediction is Bearish')
                if a > (1-alpha_distance):print('Model prediction is Bullish')
                if a < alpha_distance:print('Model prediction is Bearish')

                if (a > (1-alpha_distance) and Y_test[counter] == 1) or (a < alpha_distance and Y_test[counter] == 0):
                #if (a == 1.0 and Y_test[counter] == 1.0) or (a == 0.0 and Y_test[counter] == 0.0):
                    print(X_test_raw[counter])
                    print(X_test[counter])
                    won=won+1
                    print('WON\n')
                else:
                    print(X_test_raw[counter])
                    print(X_test[counter])
                    print('LOST\n')
                    lost=lost+1

                #self.graph_data_ohlc(X_test_raw[counter])

            counter=counter+1
        print('Won: ' + str(won) + ' Lost: ' + str(lost))
        if won+lost != 0:
            print('Success rate: ' + str(round((won*100)/(won+lost),2)) + '%')
        cell_timer.kill()

        plt.plot(Y_test)
        plt.plot(predictions)
        plt.title('Model accuracy')
        plt.ylabel('Accuracy')
        plt.xlabel('total calls')
        plt.legend(['Correct Value', 'Predictions'], loc='lower right')
        plt.show()


    def get_model(self):
        model = load_model(f"{self.model_name}.h5")
        print("MODEL-LOADED")
        return model

