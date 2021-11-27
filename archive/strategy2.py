import json
import requests
from datetime import datetime
from time     import sleep
from tradingview_ta import TA_Handler, Interval, Exchange

class PredictBNB:
    def __init__(self):
        self.keyid = 1
        self.url = 'https://www.alphavantage.co/query?function=CRYPTO_INTRADAY&symbol=BNB&market=USD&interval=1min&apikey='
        self.body_key = "Time Series Crypto (1min)"
        self.buy = 0
        self.sell = 0
        self.predict = 'NA'

    def get_apikey(self, keyid):
        apikeyObject = open("data/apikey.json", "r")
        jsonContent = json.loads(apikeyObject.read())
        return jsonContent[str(keyid)]

    def generate_query(self):
        # pass keyid
        # todo make keyid in roundrobbin way in future
        return self.url + self.get_apikey(self.keyid)
    
    def get_data(self, live=True):
        if live:
            data = requests.get(self.generate_query())
            return data.json()[self.body_key]
        else:
            apikeyObject = open("data/sample.json", "r")
            return json.loads(apikeyObject.read())[self.body_key]
    
    def get_technical_analysis(self, interval):
        ta = TA_Handler(
            symbol="BNBPERP",
            screener="crypto",
            exchange="BINANCE",
            interval=interval
        )
        return ta.get_analysis().summary

    def run(self):
        # print(self.get_data(live=False))
        candel_5 = True
        while True:
            try:
                min = datetime.now().minute
                if min % 5 == 4:
                    candel_5 = True
                else:
                    candel_5 = False
                
                if candel_5:
                    ta_5min = self.get_technical_analysis(Interval.INTERVAL_5_MINUTES)
                    ta_1min = self.get_technical_analysis(Interval.INTERVAL_1_MINUTE)
                    #print(ta_5min)
                    #print(ta_1min)
                    if ta_1min['BUY'] > ta_1min['SELL']:
                        self.buy += 1
                    else:
                        self.sell += 1

                    if self.buy > self.sell:
                        self.predict = 'up'
                    else:
                        self.predict = 'down'
                    self.buy = 0
                    self.sell = 0
                    print(f"predicting {datetime.now()} : {self.predict}")
                        
                else:
                    # if min % 5 == 0:
                    #     print(f"prediction found {datetime.now()} : {self.predict}")
                    ta_1min = self.get_technical_analysis(Interval.INTERVAL_1_MINUTE)
                    #print(ta_1min)
                    if ta_1min['BUY'] > ta_1min['SELL']:
                        self.buy += 1
                    else:
                        self.sell += 1
                
            except Exception as e:
                print(f"Error found {e}")

            sleeptime = 60 - datetime.now().second
            #print(f"sec {datetime.now().second}, sleeptime {sleeptime}")
            sleep(sleeptime)

if __name__ == '__main__':
    st = PredictBNB()
    st.run()

    