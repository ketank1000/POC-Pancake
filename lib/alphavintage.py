
import json
from typing import OrderedDict
import requests
from lib        import constants
from pandas     import DataFrame, to_datetime

class Alpha:
    def __init__(self):
        self.keyid=2
        
    def get_apikey(self, keyid):
        with open(constants.API_KEYS, "r") as filekey:
            jsonContent = json.loads(filekey.read())
        return jsonContent[str(keyid)]

    def get_query(self, interval, symbol='BNB'):
        return constants.ALPHA_URL.format(symbol, interval, self.get_apikey(self.keyid))

    def get_historical_data(self, interval, symbol='BNB'):
        url = self.get_query(interval, symbol)
        data = requests.get(url)
        response = data.json()
        data = response[constants.BODY_SERIES.format(interval)]
        return self.dict_to_pd(data)

    def dict_to_pd(self, data):
        formated_data = OrderedDict()
        for tick in data:
            new_dict = {
                "Open"  : float(data[tick]["1. open"]),
                "High"  : float(data[tick]["2. high"]),
                "Low"   : float(data[tick]["3. low"]),
                "Close" : float(data[tick]["4. close"]),
                "Volume": float(data[tick]["5. volume"])
            }
            formated_data[tick] = new_dict

        df = DataFrame.from_dict(formated_data, orient='index')
        df.index = to_datetime(df.index)
        return df.iloc[::-1]

    def heikin_ashi(self, df):
        df_ha = DataFrame(index=df.index.values, columns=['Open', 'High', 'Low', 'Close', 'Change'])
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


# a = Alpha()
# d = a.get_historical_data('1min')
# print(d)
# ha = a.heikin_ashi(d)
# print(ha)
