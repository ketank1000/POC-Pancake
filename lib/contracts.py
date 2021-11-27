
import json
from time       import sleep
from datetime   import datetime
from web3       import Web3
from lib        import constants
from lib.enums  import Prediction


class Pancake():
    def __init__(self):
        self.contract_instance = None
        self.config = None
        self.read_config()
        self.web3_init()

    def read_config(self):
        configObj = open(constants.PANCAKE_CONFIG, "r")
        self.config = json.loads(configObj.read())

    def web3_init(self):
        w3 = Web3(Web3.HTTPProvider(constants.BSC_CHAIN))
        with open(constants.PANCAKE_ABI, "r") as abiptr:
            abi = json.loads(abiptr.read())
        self.contract_instance = w3.eth.contract(address=self.config['contract_address'], abi=abi)

    def get_current_epoch(self):
        return self.contract_instance.functions.currentEpoch().call()

    def get_round_details(self, epoch=None):
        if not epoch:
            epoch = self.get_current_epoch()
        round = self.contract_instance.functions.rounds(epoch).call()
        round = {
            "epoch": round[0],
            "startTimestamp": round[1],
            "lockTimestamp": round[2],
            "closeTimestamp": round[3],
            "lockPrice": round[4],
            "closePrice": round[5],
            "lockOracleId": round[6],
            "closeOracleId": round[7],
            "totalAmount": round[8],
            "bullAmount": round[9],
            "bearAmount": round[10],
            "rewardBaseCalAmount": round[11],
            "rewardAmount": round[12],
            "oracleCalled": round[13]
        }
        return round

    def get_prediction(self, epoch):
        round = self.get_round_details(epoch)
        diff = round["closePrice"] - round["lockPrice"]
        if diff > 0:
            return Prediction.BULL
        elif diff < 0:
            return Prediction.BEAR
        return Prediction.SKIP

    def get_next_round_waiting_time(self):
        round = self.get_round_details()
        locktime = datetime.utcfromtimestamp(round["lockTimestamp"])
        remaining_time = locktime - datetime.utcnow()
        return remaining_time.seconds, round['epoch']

    def wait_for_next_round(self):
        wait = float('inf')
        while wait > 1000 or wait < 40:
            wait, epoch = self.get_next_round_waiting_time()
            wait = wait - 20
        print(f"Waiting for next round {epoch} to start : {wait}s")
        sleep(wait)

    def wait_for_current_round_to_complete(self, round):
        locktime = datetime.utcfromtimestamp(round["closeTimestamp"])
        remaining_time = locktime - datetime.utcnow()
        wait = remaining_time.seconds + 10
        print(f"Waiting for current round {round['epoch']} to complete : {wait}s")
        sleep(wait)
