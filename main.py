import pandas as pd
import yaml
from sqlalchemy import create_engine
import urllib
from math import ceil

# read in queries
SAMPLES = 20 # number of sample weeks to do
WEEKS = 6 # should be between 1 and 6 (number of weeks to check until stock out)

with open(r'config.yml') as file:
        config = yaml.load(file, Loader=yaml.FullLoader)

params = urllib.parse.quote_plus('DRIVER={ODBC Driver 17 for SQL Server};'
                 f'SERVER={config["server_info"]["server"]};'
                 f'DATABASE={config["server_info"]["database"]};'
                 'Trusted_Connection=yes;')
engine = create_engine("mssql+pyodbc:///?odbc_connect=%s" % params) 

# get current inventory and change it into a workable dictionary
inventory = pd.read_sql(con=engine, sql=config["sql"]["inventory"])
inventory = inventory.set_index('sku')
inventory = inventory.to_dict()
inventory = inventory["available"]

# sample last six weeks of inventory needs 20 different times
orders = pd.read_sql(con=engine, sql=config["sql"]["orders"])
samples = [orders.sample(frac = 1/WEEKS).groupby('sku')['qty'].sum() for i in range(SAMPLES)]

# remove samples from inventory
master = pd.Series()
for sample in samples:
    sub_inv = inventory
    if master.empty:
        master = sample
    else: 
        master = pd.concat([master, sample], axis=1)

# get results from sampling
master.fillna(0, inplace=True)
master["avg"] = master.mean(axis=1)
master_dict = master.to_dict()
sample_results = master_dict["avg"]

# subract results from current inventory
inventory_after = {}
for key in sample_results.keys():
    if key in inventory.keys():
        inventory_after[key] = inventory[key] - sample_results[key]
    else:
        inventory_after[key] = 0 - sample_results[key]

# identify at risk
at_risk = pd.DataFrame.from_dict(inventory_after, orient='index')
at_risk.index.rename("sku", inplace=True)
at_risk.rename(columns = {0:'qty'}, inplace=True)

# assign priority level to sku risk
# priority 1: negative
# priority 2: below sample output
# priority 3: above sample output

at_risk = pd.concat([at_risk, master["avg"]], axis=1).fillna(0)
at_risk["low"] = at_risk["qty"] <= at_risk["avg"]

def priority(row):
    if row.qty <= 0: return 1
    elif row.qty <= row.avg: return 2
    else: return 3

at_risk["priority"] = at_risk.apply(lambda row: priority(row), axis=1)

# ouptput at risk SKUs
writer = pd.ExcelWriter('At Risk SKUs.xlsx', engine='xlsxwriter')
at_risk.to_excel(writer, sheet_name='Sheet1', startrow=1, header=False, index=True)

workbook = writer.book
worksheet = writer.sheets['Sheet1']

column_settings = [{'header': column} for column in at_risk.columns]
column_settings.insert(0, {'header':'sku'})

(max_row, max_col) = at_risk.shape
worksheet.add_table(0, 0, max_row, max_col, {'columns': column_settings})

writer.save()
