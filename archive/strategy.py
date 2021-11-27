import json
from os import CLD_EXITED
import requests
from datetime import datetime
from time     import sleep
from web3 import Web3
import json
import traceback
from tradingview_ta import TA_Handler, Interval, Exchange


class PredictBNB:
    def __init__(self):
        self.keyid = 1
        self.url = 'https://www.alphavantage.co/query?function=CRYPTO_INTRADAY&symbol=BNB&market=USD&interval={}&apikey={}'
        self.body_key = "Time Series Crypto ({})"
        self.buy = 0
        self.sell = 0
        self.next_predict = ''
        self.prev_predict = ''
        self.wins = 0
        self.lose = 0
        self.skip = 0
        self.min_bid_amount = 10
        self.contract_instance = None
        self.next_round = None
        self.prev_round = None
        self.config = self.read_config()
        self.web3_init()

    def read_config(self):
        configObj = open("data/config.json", "r")
        jsonContent = json.loads(configObj.read())
        return jsonContent

    def web3_init(self):
        w3 = Web3(Web3.HTTPProvider('https://bsc-dataseed.binance.org/'))
        print(w3.isConnected())
        with open('data/abi.json') as abiptr:
            abi = json.loads(abiptr.read())
        self.contract_instance = w3.eth.contract(address=self.config['contract_address'], abi=abi)

    def get_apikey(self, keyid):
        apikeyObject = open("data/apikey.json", "r")
        jsonContent = json.loads(apikeyObject.read())
        return jsonContent[str(keyid)]

    def get_round_details(self, epoch=None):
        if not epoch:
            epoch = self.contract_instance.functions.currentEpoch().call()    
        return self.contract_instance.functions.rounds(epoch).call()
        
    def get_next_round_waiting_time(self, locktime):
        locktime = datetime.utcfromtimestamp(locktime)
        remaining_time = locktime - datetime.utcnow()
        return remaining_time.seconds

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
    
    def get_technical_analysis(self):
        ta = TA_Handler(
            symbol="BNBPERP",
            screener="crypto",
            exchange="BINANCE",
            interval=Interval.INTERVAL_5_MINUTES
        )
        return ta.get_analysis().summary

    def log(self, msg):
        print(f"{datetime.utcnow()} : {msg}")

    def get_difference(self, data, ticks=3):
        vol = 0
        count = 0
        total_diff = 0
        for time_series in data:
            diff = float(data[time_series]['4. close']) - float(data[time_series]['1. open'])
            if diff > 0.0:
                vol += float(data[time_series]['5. volume'])
            elif diff < 0.0:
                vol -= float(data[time_series]['5. volume'])
            total_diff += diff
            if count < 4:
                count += 1
                continue
            break
        return total_diff ,vol

    def match_predict(self):
        self.log(self.prev_round)
        open = self.prev_round[4]
        close = self.prev_round[5]
        diff = close - open
        self.log(diff)
        print(diff)
        if diff > 0:
            return "UP"
        elif diff < 0:
            return "DOWN"
        return ""

    def print_summary(self):
        if (self.wins+self.lose) == 0:
            return
        rate = (self.wins/(self.wins+self.lose))*100
        profit = self.min_bid_amount*self.wins*0.6 - self.min_bid_amount*self.lose
        print('\nSummary:')
        print(f' Wins/Lose/skip: {self.wins}/{self.lose}/{self.skip}')
        print(f' Win rate: {rate}')
        print(f" Profit: {profit} $ (bid amt: {self.min_bid_amount})\n")
        with open('data/output.txt','w') as output:
            output.write("Summary :\n")
            output.write(f' Wins/Lose/skip: {self.wins}/{self.lose}/{self.skip}\n')
            output.write(f' Rate: {rate} %\n')
            output.write(f" Profit: {profit} $ (bid amt: {self.min_bid_amount}, M: 1.6x)\n")

    def run(self):
        while True:
            try:
                self.prev_round = self.next_round
                wait = 80000
                while wait > 10000 or wait < 40:
                    self.next_round = self.get_round_details()
                    wait = self.get_next_round_waiting_time(self.next_round[2]) - 30
                    print(wait)
                self.log(f"Waiting For next round ... ({wait})")
                sleep(wait)
                data_1min = self.get_data('1min')
                
                diff, vol = self.get_difference(data_1min)
                self.prev_predict = self.next_predict
                ta = self.get_technical_analysis()
                self.log(f"diff = {diff}, vol={vol}, ta={ta['RECOMMENDATION']}")
                
                data_5min = self.get_data('5min')
                min_keys = list(data_5min.keys())
                last_candle = data_5min[min_keys[0]]
                HA_close = (float(last_candle['1. open']) + float(last_candle['2. high']) + float(last_candle['3. low']) + float(last_candle['4. close'])) * 0.25
                self.log(f"{last_candle}, {HA_close}")
                if diff > 0.0 and vol > 0 and HA_close < float(last_candle['4. close']):
                    self.next_predict = 'UP'
                    self.log('Predicting UP')
                elif diff < 0.0 and vol < 0 and HA_close > float(last_candle['4. close']):
                    self.next_predict = 'DOWN'
                    self.log('Predicting Down')
                else:
                    self.next_predict = ''
                    self.log("Skip predict")

                if self.prev_predict == '':
                    sleep(60)
                    self.skip += 1
                    self.print_summary()
                    continue
                if self.prev_round == None:
                    continue
                complete_time = datetime.utcfromtimestamp(self.prev_round[3])
                self.log(f"{complete_time}, {self.next_round[2]}")
                remaining_time = complete_time - datetime.utcnow()
                remaining_time = remaining_time.seconds
                # sometime contract gives 86119 
                if remaining_time > 100:
                    remaining_time = 50
                self.log(f"Waiting for previous round to complete ... ({remaining_time})")
                if remaining_time > 0:
                    sleep(remaining_time + 30)
                self.prev_round = self.get_round_details(self.prev_round[0])
                predict = self.match_predict()

                if predict == self.prev_predict:
                    self.log("previous prediction win")
                    self.wins += 1
                else:
                    self.log("previous prediction lost")
                    self.lose += 1

                self.print_summary()
                
                
            except Exception as e:
                traceback.print_exc()
                self.log(f"Error found {e}")


if __name__ == '__main__':
    st = PredictBNB()
    st.run()

    