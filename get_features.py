import eikon as ek
import datetime
import pandas as pd

# Set your App Key
ek.set_app_key('7f3b79b0b2a44576a25f3d6a234cfefc81e7fbb5') #maddie app key
#ek.set_app_key('9190767d89924e47b6125365150557616654eb0d') #sam app key

# Get the date 5 years ago from today
end_date = datetime.date.today()
print(end_date)
start_date = end_date - datetime.timedelta(days=5*365)
print(start_date)

# List of symbols for dividend aristocrats (example list, might be different based on your data source)
features = ['XLV.PH', '.TRGSPI', '.TRGSPS', 'VNQ', 'SDY', 'XLU','SPLV.K','XLI', 'XLP', '.BCOMCLC', 'SLX', '.DRG', 'LLY', '.MIWO0CS00PUS', 'GE', 'BA', ".BCOMKWC", "MUSA.K", ".BCOMCNC", ".SOLLIT", ".BATTIDX1", "TSLA.O", "PEP.O", "MCD", "KARS.A", "AAPL.O", "BRKa", "BLK", "XME"]

# Create an empty dataframe to store the results
all_data = pd.DataFrame()

for i in features: 
    data  = ek.get_timeseries(i,
                            fields = ['CLOSE'],
                            start_date = start_date.strftime("%Y-%m-%d"),
                            end_date = end_date.strftime("%Y-%m-%d"))
    all_data[i] = data

print(all_data)
data.dropna(inplace=True)
all_data.to_csv('feature_data.csv', index=True)
