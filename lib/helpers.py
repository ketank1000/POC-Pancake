
import talib
from lib.enums import Prediction

def get_candle_difference(df):
    vol = 0
    count = 0
    total_diff = 0
    for i in range(len(df)-1,0,-1):
        total_diff += df['Close'].iloc[i] - df['Open'].iloc[i]
        # print(df['volume'])
        # if diff > 0.0:
        #     vol += df['volume'].iloc[i]
        # elif diff < 0.0:
        #     vol -= df['volume'].iloc[i]
        if count < 4:
            count += 1
            continue
        break
    return total_diff


def macd(df):
    # talib.MACD returns 3 values
    #   1. macd
    #   2. macdsignal
    #   3. macdhist <-- we need this value, which is index 2
    macd_df = talib.MACD(df['close'])[2]
    last_entry = macd_df.iloc[-1]
    second_last_entry = macd_df.iloc[-2]
    third_last_entry = macd_df.iloc[-3]
    if last_entry > second_last_entry and second_last_entry > third_last_entry:
        return Prediction.BULL
    elif last_entry < second_last_entry and second_last_entry < third_last_entry:
        return Prediction.BEAR
    return Prediction.SKIP

def adx(df):
    adx_df = talib.ADX(df['high'], df['low'], df['close'], timeperiod=14)
    last_entry = adx_df.iloc[-1]
    second_entry = adx_df.iloc[-2]
    print(last_entry, second_entry)
    if last_entry > 20 and second_entry > 20:
        return True
    return False