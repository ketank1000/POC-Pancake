import json
import requests
from datetime import datetime
from time     import sleep
from web3 import Web3
import json
from tradingview_ta import TA_Handler, Interval, Exchange
import pytz

class PredictBNB:
    def __init__(self):
        self.keyid = 1
        self.url = 'https://www.alphavantage.co/query?function=CRYPTO_INTRADAY&symbol=BNB&market=USD&interval={}&apikey={}'
        self.body_key = "Time Series Crypto ({})"
        self.buy = 0
        self.sell = 0
        self.next_predict = ''
        self.prev_predict = ''
        self.timezone = pytz.UTC
        self.wins = 0
        self.lose = 0
        self.skip = 0
        self.config = self.read_config()

    def read_config(self):
        configObj = open("data/config.json", "r")
        jsonContent = json.loads(configObj.read())
        return jsonContent

    def web3_init(self):
        w3 = Web3(Web3.HTTPProvider('https://bsc-dataseed.binance.org/'))
        print(w3.isConnected())
        with open('data/abi.json') as abiptr:
            abi = json.loads(abiptr.read())
        contract_instance = w3.eth.contract(address=self.config['contract_address'], abi=abi)

    def get_apikey(self, keyid):
        apikeyObject = open("data/apikey.json", "r")
        jsonContent = json.loads(apikeyObject.read())
        return jsonContent[str(keyid)]

    def generate_query(self, interval):
        # pass keyid
        # todo make keyid in roundrobbin way in future
        url = self.url.format(interval, self.get_apikey(self.keyid))
        #print(f"Taking data from : {url}")
        return url
    
    def get_data(self, interval, live=True):
        if live:
            data = requests.get(self.generate_query(interval))
            response = data.json()
            #print(response['Meta Data'])
            return response[self.body_key.format(interval)]
        else:
            apikeyObject = open("data/sample.json", "r")
            return json.loads(apikeyObject.read())[self.body_key.format(interval)]
    
    def get_technical_analysis(self, interval):
        ta = TA_Handler(
            symbol="BNBPERP",
            screener="crypto",
            exchange="BINANCE",
            interval=interval
        )
        return ta.get_analysis().summary

    def log(self, msg):
        print(f"{datetime.now(self.timezone)} : {msg}")

    def get_difference(self, data, ticks=4):
        diff = 0
        count = 0
        for time_series in data:
            diff += float(data[time_series]['4. close']) - float(data[time_series]['1. open'])
            if count < 4:
                count += 1
                continue
            break
        return diff

    def print_summary(self):
        print('\n    Summary:')
        print(f'      Wins: {self.wins}')
        print(f'      Lose: {self.lose}')
        print(f'      Skip: {self.skip}\n')

    def run(self):
        while True:
            try:
                min = datetime.now(self.timezone).minute
                #print(min)
                if min % 5 == 4:
                    print("\n\n")
                    sleeptime = 40 - datetime.now(self.timezone).second
                    self.log(f"Making Prediction ... ({sleeptime})")
                    if sleeptime > 0:
                        sleep(sleeptime)
                    data_1min = self.get_data('5min')
                    
                    diff = self.get_difference(data_1min)
                    self.prev_predict = self.next_predict
                    self.log(f"diff = {diff}")
                    min = datetime.now(self.timezone)
                    if diff > 0.0:
                        self.next_predict = 'UP'
                        self.log('Predicting UP')
                    elif diff < 0.0:
                        self.next_predict = 'DOWN'
                        self.log('Predicting Down')
                    else:
                        self.next_predict = ''
                        self.log("Skip predict")
                    
                    self.log(f"Validating prev prediction ... (60)")
                    sleep(60)
                    data_5min = self.get_data('5min')
                    time_series = list(data_5min.keys())
                    first_candle = data_5min[time_series[1]]
                    diff = float(first_candle['4. close']) - float(first_candle['1. open'])
                    min = datetime.now(self.timezone)
                    self.log(f"diff={diff} prev={self.prev_predict} next={self.next_predict}")
                    if diff > 0.0 and self.prev_predict == 'UP' or diff < 0.0 and self.prev_predict == 'DOWN':
                        self.log("previous prediction win")
                        self.wins += 1
                    elif self.prev_predict == '':
                        self.log("previous prediction skiped!")
                        self.skip += 1
                    else:
                        self.log("previous prediction lost")
                        self.lose += 1
                    self.print_summary()
                else:
                    min = datetime.now(self.timezone).minute
                    min_completed = 5 - (min % 5) - 1
                    sleeptime = 60 * min_completed
                    self.log(f"Waiting for next round ... ({sleeptime})")
                    sleep(sleeptime)
                
            except Exception as e:
                self.log(f"Error found {e}")


if __name__ == '__main__':
    st = PredictBNB()
    st.run()

    