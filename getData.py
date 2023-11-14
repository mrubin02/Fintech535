import eikon as ek
import datetime
import pandas as pd

# Set your App Key
ek.set_app_key('7f3b79b0b2a44576a25f3d6a234cfefc81e7fbb5')

# Get the date 5 years ago from today
end_date = datetime.date.today()
start_date = end_date - datetime.timedelta(days=5*365)

# List of symbols for dividend aristocrats (example list, might be different based on your data source)
aristocrats = [
    'DOV.N', 'PG.N', 'GPC.N', 'EMR.N', 'MMM.N', 'CINF.O', 'KO.N', 'CL.N', 'NDSN.O', 'JNJ.N', 'HRL.N', 'FRT.N', 'SWK.N', 'SYY.N', 'TGT.N', 'PPG.N', 'ITW.N', 'GWW.N', 'ABBV.N', 'BDX.N', 'ABT.N', 'KMB.N', 'PEP.O', 'NUE.N', 'SPGI.N', 'ADM.N', 'WMT.N', 'ED.N', 'LOW.N', 'ADP.O', 'WBA.O', 'PNR.N', 'MCD.N', 'MDT.N', 'CLX.N', 'SHW.N', 'BEN.N', 'AFL.N', 'APD.N', 'XOM.N', 'CTAS.O', 'BFb.N', 'MKC.N', 'TROW.O', 'CAH.N', 'ATO.N', 'CVX.N', 'GD.N', 'ROP.O', 'ECL.N', 'WST.N', 'LIN.N', 'AOS.N', 'O.N', 'EXPD.O', 'CB.N', 'ALB.N', 'ESS.N', 'BRO.N', 'NEE.N', 'CAT.N', 'IBM.N', 'CHD.N', 'SJM.N', 'CHRW.O'  # COMPLETE LIST
]

# Create an empty dataframe to store the results
all_data = pd.DataFrame()

data, data_err = ek.get_data(instruments = aristocrats, 
                           fields = [
                            'TR.CLOSEPRICE(Adjusted=0)',
                            'TR.PriceCloseDate'
                            ],
                            parameters = {
                                'SDate': start_date.strftime("%Y-%m-%d"),
                                'EDate': end_date.strftime("%Y-%m-%d"),
                                'Frq': 'D'
                            })


##### prices
data.rename(
    columns = {
        'Open Price':'open',
        'High Price':'high',
        'Low Price':'low',
        'Close Price':'close'
    },
    inplace = True
)
data.dropna(inplace=True)
data['Date'] = pd.to_datetime(data['Date']).dt.date
# save as csv so you can open in Excel if you want
data.to_csv('dividend_data.csv', index=False)

