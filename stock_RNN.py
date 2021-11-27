import pandas as pd
from keras.layers.core import Dense, Dropout
from keras.layers.recurrent import GRU
from keras.models import Sequential, load_model
import matplotlib.pyplot as plt
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from lib.alphavintage   import Alpha
from lib.enums          import Interval


bnb = pd.read_csv('data/BNB-USD_5m.csv',index_col=0)
alpha_vintage = Alpha()
test = alpha_vintage.get_historical_data(Interval.MIN_1.value)
# old -> new
bnb = bnb.iloc[::-1]

# preparing input features
bnb = bnb.drop(['Adj Close'], axis=1)
bnb = bnb.drop(['Volume'], axis=1)
test = test.drop(['volume'], axis=1)

# # preparing label data
bnb_shift = bnb.shift(-1)
label = bnb['Close']

# test = test[-5:]
test.loc['*'] = [test.iloc[-1].open, test.iloc[-1].high, test.iloc[-1].low, test.iloc[-1].close]
# test.index = test.index + 1  # shifting index
# test.sort_index(inplace=True)
# test = test[::-1]
print(test)

test_label = test['close']


# # adjusting the shape of both
bnb.drop(bnb.index[len(bnb)-1], axis=0, inplace=True)
label.drop(label.index[len(label)-1], axis=0, inplace=True)


# # conversion to numpy array
x, y = bnb.values, label.values
x_t, y_t = test.values, test_label.values

# # scaling values for model
x_scale = MinMaxScaler()
y_scale = MinMaxScaler()

X_train = x_scale.fit_transform(x)
y_train = y_scale.fit_transform(y.reshape(-1,1))

X_test = x_scale.fit_transform(x_t)
y_test = y_scale.fit_transform(y_t.reshape(-1,1))

# # splitting train and test
#X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size=0.33)
X_train = X_train.reshape((-1,1,4))
X_test = X_test.reshape((-1,1,4))

# creating model using Keras
# tf.reset_default_graph()

model_name = 'BNB-GRU-model'

# model = Sequential()
# model.add(GRU(units=512,
#               return_sequences=True,
#               input_shape=(1, 4)))
# model.add(Dropout(0.2))
# model.add(GRU(units=256))
# model.add(Dropout(0.2))
# model.add(Dense(1, activation='sigmoid'))
# model.compile(loss='mse', optimizer='adam')

model = load_model("{}.h5".format(model_name))
print("MODEL-LOADED")

# model.fit(X_train,y_train,batch_size=250, epochs=500, validation_split=0.1, verbose=1)
# model.save("{}.h5".format(model_name))
# print('MODEL-SAVED')

# score = model.evaluate(X_test, y_test)
# print('Score: {}'.format(score))
# yhat = model.predict(X_test)
# yhat = y_scale.inverse_transform(yhat)
# y_test = y_scale.inverse_transform(y_test)
# print(yhat[-5:])
# print(y_test[-5:])
# plt.plot(yhat[-100:], label='Predicted')
# plt.plot(y_test[-100:], label='Ground Truth')
# plt.legend()
# plt.show()


# predict = model.predict(start=len(X_train), end=len(X_train)+1, typ='levels')