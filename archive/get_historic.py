"""script to get historical data"""
from datetime import date, timedelta
import yfinance as yf
import pandas as pd


def get_historical_data(symbol, interval, create_csv):
    """
    Gets the historical data from yahoo finance
    prama symbol: str : name of instrument
    param interval: str: time interval to extract (1m,5m,15m,1d)
    param create_csv: bool: flag to create csv file
    Sample data from dataframe
                               Open       High       Low        Close      Adj Close  Volume
    Datetime
    2021-02-08 09:15:00+05:30  96.500000  96.599998  96.300003  96.599998  96.599998       0
    2021-02-08 09:16:00+05:30  96.650002  97.500000  96.650002  97.500000  97.500000  928583
    2021-02-08 09:17:00+05:30  97.400002  97.650002  97.349998  97.500000  97.500000  916726
    2021-02-08 09:18:00+05:30  97.599998  97.900002  97.599998  97.800003  97.800003  535410
    2021-02-08 09:19:00+05:30  97.800003  98.000000  97.800003  98.000000  98.000000  396855
    ...                              ...        ...        ...        ...        ...     ...
    2021-02-12 15:25:00+05:30  96.050003  96.099998  96.000000  96.099998  96.099998   36766
    2021-02-12 15:26:00+05:30  96.099998  96.099998  96.050003  96.050003  96.050003   23478
    2021-02-12 15:27:00+05:30  96.099998  96.099998  96.000000  96.050003  96.050003   30915
    2021-02-12 15:28:00+05:30  96.099998  96.150002  96.050003  96.050003  96.050003   58852
    2021-02-12 15:29:00+05:30  96.099998  96.150002  96.000000  96.050003  96.050003   46264
    """
    delta = timedelta(days=7)
    start_date = date.today() - timedelta(days=60)
    end_date = date.today()
    frame_start = start_date
    frame_end = start_date + delta
    data_list = []
    ticker = f'{symbol}'
    while frame_end <= end_date:
        print(f'downloading data from {frame_start} to {frame_end}')
        symbol_data_7_days = yf.download(ticker, interval=interval, start=frame_start, end=frame_end)
        frame_start = frame_end
        frame_end += delta
        symbol_data_7_days = symbol_data_7_days[::-1]
        data_list.append(symbol_data_7_days)

    if frame_end != end_date:
        print(f'downloading data from {frame_start} to {end_date}')
        symbol_data_remaining = yf.download(ticker, interval=interval, start=frame_start, end=end_date)
        symbol_data_remaining = symbol_data_remaining[::-1]
        data_list.append(symbol_data_remaining)

    data_list.reverse()
    symbol_data = pd.concat(data_list)
    index_list = symbol_data.index.tolist()
    index_list = [(str(_)).replace(':00+01:00', '') for _ in index_list]
    symbol_data.index = index_list
    symbol_data.iloc[::-1]
    if create_csv:
        symbol_data.to_csv(f'{symbol}_{interval}.csv')
    else:
        return symbol_data


get_historical_data('BNB-USD', '5m', True)
# get_historical_data('BNB-USD', '1m', True)