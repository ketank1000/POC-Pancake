

from os import listdir
import pandas as pd

bnb_path = 'data/BNB'
files = listdir(bnb_path)
files.sort(reverse=True)
bnb_all = []
col_names = [f'#{i}' for i in range(12)]
col_names[1] = 'Open'
col_names[2] = 'High'
col_names[3] = 'Low'
col_names[4] = 'Close'
col_names[5] = 'Volume'
for csv_file in files:
    if 'csv' in csv_file:
        temp = pd.read_csv(f"{bnb_path}/{csv_file}", header=None, names=col_names)
        delete_columns = [temp.columns[0],temp.columns[6],temp.columns[7],temp.columns[8],temp.columns[9], temp.columns[10],temp.columns[11]]
        temp.drop(delete_columns, axis=1, inplace=True)
        if len(bnb_all) > 0:
            bnb_all = pd.concat([temp, bnb_all], ignore_index=True)
        else:
            print("asdf")
            bnb_all = temp
        # print(temp)

bnb_all.to_csv('data/BNBFULL.csv',index=False)
print(bnb_all)