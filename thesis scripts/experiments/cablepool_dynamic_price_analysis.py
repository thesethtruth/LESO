import pandas as pd
import plotly.graph_objects as go
import csv
import os
from scipy.signal import savgol_filter
from LESO.plotly_extension import thesis_default_styling

# read csv from ETM and convert into correct unit
with open(os.path.join(os.getcwd(), 'models', 'cablepool_price_kea_31ch4_85co2.csv'), newline='') as f:
    reader = csv.reader(f)
    data = list(reader)
    energy_market_price = [float(row[1])/1e6 for row in data[1:]]
#%% plot the energy price
edf = pd.DataFrame(
    index = pd.date_range(start="01/01/2021", periods=8760, freq='h'),
    data = [price*1e6 for price in energy_market_price],
    columns= ['energy_price']
)
edf['smoother_energy_price'] = savgol_filter(edf.energy_price, 25, 4)
edf.describe()
edf.plot(kind='hist', bins=100)
edf.energy_price.plot(kind='hist', bins=100)

## default
if False:
    fig = go.Figure(
        data=   go.Scatter(
            x=edf.index,
            y=edf.energy_price.values,
            line_color='#c75252',         
            line_width=1  
        )
    )

    fig = thesis_default_styling(fig)
    fig.update_yaxes(title='Market energy price', tickangle=90, nticks=4, ticksuffix = "€/MWh")
    fig.update_xaxes(title="Day of the year", tickformat='%B', nticks=5, tickcolor="rgba(0,0,0,0)")
    fig.show()
    # fig.write_image("ETM_price_kea2030.pdf")

    ## Smoother
    fig = go.Figure(
        data=   go.Scatter(
            x=edf.index,
            y=edf.smoother_energy_price.values,        
            line_color='#52aec7',       
            line_width=1
        )
    )
    fig = thesis_default_styling(fig)
    fig.update_yaxes(title='Market energy price', nticks=4, ticksuffix = "€/MWh")
    fig.update_xaxes(title="Day of the year", tickformat='%B', nticks=5, tickcolor="rgba(0,0,0,0)")
    fig.show()
    # fig.write_image("ETM_price_kea2030_smooth.pdf")


    #%% compare

    # make a snip
    start = 300
    duration = 168
    snip = edf.iloc[start:start+duration,:].copy()

    fig = go.Figure()
    # ETM curve
    fig.add_trace(
        go.Scatter(
            x=snip.index,
            y=snip.energy_price.values,        
            line_color='grey',       
            line_width=2,
            name='ETM modelled price'
        )
    )
    # smooth curve
    fig.add_trace(
        go.Scatter(
            x=snip.index,
            y=snip.smoother_energy_price.values,        
            line_color='#52aec7',       
            line_width=1.5,
            name='Savitzky-Golay filter'
        )
    )

    fig = thesis_default_styling(fig)
    fig.update_yaxes(title='Market energy price', nticks=4, ticksuffix = "€/MWh")
    fig.update_xaxes(title="Day of the year", tickformat='%B', nticks=5, tickcolor="rgba(0,0,0,0)")
    fig.show()

from models.experiments_overview import MODEL_FOLDER

filename="cablepool_dynamic_savgol_filtered_etmprice_31ch4_85co2.pkl"
filepath = os.path.join(MODEL_FOLDER, filename)

edf.smoother_energy_price.to_pickle(filepath)

