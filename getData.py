import eikon as ek
import datetime
import pandas as pd

# Set your App Key
ek.set_app_key('YOUR_APP_KEY')

# Get the date 5 years ago from today
end_date = datetime.date.today()
start_date = end_date - datetime.timedelta(days=5*365)

# List of symbols for dividend aristocrats (example list, might be different based on your data source)
aristocrats = [
    'DOV.N', 'PG.N', 'GPC.N', 'EMR.N', 'MMM.N', 'CINF.O', 'KO.N', 'CL.N', 'NDSN.O', 'JNJ.N', 'KVUE.N', 'HRL.N', 'FRT.N', 'SWK.N', 'SYY.N', 'TGT.N', 'PPG.N', 'ITW.N', 'GWW.N', 'ABBV.N', 'BDX.N', 'ABT.N', 'KMB.N', 'PEP.O', 'NUE.N', 'SPGI.N', 'ADM.N', 'WMT.N', 'ED.N', 'LOW.N', 'ADP.O', 'WBA.O', 'PNR.N', 'MCD.N', 'MDT.N', 'CLX.N', 'SHW.N', 'BEN.N', 'AFL.N', 'APD.N', 'XOM.N', 'AMCR.N', 'CTAS.O', 'BFb.N', 'MKC.N', 'TROW.O', 'CAH.N', 'ATO.N', 'CVX.N', 'GD.N', 'ROP.O', 'ECL.N', 'WST.N', 'LIN.N', 'AOS.N', 'O.N', 'EXPD.O', 'CB.N', 'ALB.N', 'ESS.N', 'BRO.N', 'NEE.N', 'CAT.N', 'IBM.N', 'CHD.N', 'SJM.N', 'CHRW.O'  # COMPLETE LIST
]

# Create an empty dataframe to store the results
all_data = pd.DataFrame()

# Fetch historical data for each code
for ric in aristocrats:
    data, err = ek.get_data(ric, 
                            ["DATE", "CLOSE"],
                            {'start_date': start_date, 'end_date': end_date, 'frequency': 'daily'})
    
    data['RIC'] = ric  # Add a column to differentiate the data by stock
    all_data = all_data.append(data, ignore_index=True)

# Save the data to a CSV
all_data.to_csv('dividend_aristocrats_history.csv', index=False)
