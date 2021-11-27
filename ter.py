import curses
import time
import sys
import requests

# Constants
CURRENCY='USD'
REQUESTS_PER_MINUTE=10
REQUEST_URI='https://api.coinmarketcap.com/v1/ticker/'

## Display related methods/classes
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

TITLE_ROW = 'Rank\tSymbol\tName\t\tPrice\t\t24h Volume\tMarket Cap\t% Change (1h)\t% Change (24h)\t% Change (7d)\tAvailable Supply\tLast Updated'

def report_progress(data):
    stdscr.scrollok(1)
    stdscr.idlok(1)
    stdscr.scroll(100)
    stdscr.addstr(0, 0, TITLE_ROW, curses.A_BOLD)
    
    # for idx, bit_coin in enumerate(data):
    #     if idx > 51:
    #         break
    #     stdscr.addstr(idx+2, 0, "{}\t".format(bit_coin['rank']))
    #     stdscr.addstr("{}\t".format(bit_coin['symbol']), curses.color_pair(4))
    #     stdscr.addstr("{}\t\t".format(bit_coin['name'][:7]))
    #     stdscr.addstr("{}\t\t".format(bit_coin['price_usd'][:7]), curses.color_pair(3))
    #     stdscr.addstr("{:10}\t".format(bit_coin['24h_volume_usd']))
    #     stdscr.addstr("{:13}\t".format(bit_coin['market_cap_usd']))
    #     if float(bit_coin.get('percent_change_1h',0.0)) > 0:
    #         stdscr.addstr("{}\t\t".format(bit_coin['percent_change_1h'][:7]), curses.color_pair(1))
    #     elif float(bit_coin.get('percent_change_1h',0.0)) < 0:
    #         stdscr.addstr("{}\t\t".format(bit_coin['percent_change_1h'][:7]), curses.color_pair(2))
    #     else:
    #         stdscr.addstr("None\t\t")

    #     if float(bit_coin.get('percent_change_24h',0.0)) > 0:
    #         stdscr.addstr("{}\t\t".format(bit_coin['percent_change_24h'][:7]), curses.color_pair(1))
    #     elif float(bit_coin.get('percent_change_24h',0.0)) < 0:
    #         stdscr.addstr("{}\t\t".format(bit_coin['percent_change_24h'][:7]), curses.color_pair(2))
    #     else:
    #         stdscr.addstr("None\t\t")

    #     if bit_coin.get('percent_change_7d'):
    #         if float(bit_coin.get('percent_change_7d',0.0)) > 0:
    #             stdscr.addstr("{}\t\t".format(bit_coin['percent_change_7d'][:7]), curses.color_pair(1))
    #         elif float(bit_coin.get('percent_change_7d',0.0)) < 0:
    #             stdscr.addstr("{}\t\t".format(bit_coin['percent_change_7d'][:7]), curses.color_pair(2))
    #     else:
    #         stdscr.addstr("None\t\t")
    #     stdscr.addstr("{}\t\t".format(bit_coin['available_supply'][:7]))
    #     local_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(bit_coin['last_updated'])))
    #     stdscr.addstr("{}".format(str(local_time)))
        
    stdscr.refresh()

# Service request
def get_data():
    r = requests.get(REQUEST_URI)
    if r.status_code != 200:
        print ("Cannot get data from {}".format(REQUEST_URI))
        print ("Return code: {}, Message: {}".format(r.status_code, r.data))
        return None
    else:
        return r.json()

if __name__ == "__main__":
    stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)

    try:
        while True:
            #resp = get_data()
            report_progress("asdf")
            time.sleep(60/REQUESTS_PER_MINUTE)
    finally:
        curses.echo()
        curses.nocbreak()
        curses.endwin()