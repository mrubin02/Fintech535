import eikon as ek
import datetime
import pandas as pd

# Set your App Key
#ek.set_app_key('7f3b79b0b2a44576a25f3d6a234cfefc81e7fbb5') #maddie app key
ek.set_app_key('9190767d89924e47b6125365150557616654eb0d') #sam app key

# Get the date 5 years ago from today
end_date = datetime.date.today()
start_date = end_date - datetime.timedelta(days=5*365)

# List of symbols for dividend aristocrats (example list, might be different based on your data source)
features = ['XLV.PH', '.TRGSPI', '.TRGSPS', 'VNQ', 'SDY', 'XLU','SPLV.K', 'XLI', 'XLP']

# Create an empty dataframe to store the results
all_data = pd.DataFrame()

data  = ek.get_timeseries(['XLV.PH', '.TRGSPI', '.TRGSPS', 'VNQ', 'SDY', 'XLU','SPLV.K'],
                            fields = ['CLOSE'],
                            start_date = start_date.strftime("%Y-%m-%d"),
                            end_date = end_date.strftime("%Y-%m-%d"))

data.dropna(inplace=True)
data.to_csv('feature_data.csv', index=True)
