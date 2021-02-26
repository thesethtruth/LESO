import requests
import json
from datetime import datetime
import pandas as pd
import os.path

def get(lat, lon):
    """
    Returns:
        TMY as dataframe with information appended as class items. 
    Inputs:
        Lattitude
        Longtiude 
    ---
    Checks the latest api call (stored offline) to save the time of getting 
    data from PV GIS
    """
    if os.path.isfile("data/lastapicall.pkl"):
        
        # read last API call
        tmy = pd.read_pickle("data/lastapicall.pkl")
        
        if not (tmy['lat'][1] == lat and tmy['lon'][1] == lon):
            
            # get new data true API
            print('Fetching data through API...')
            tmy = _getPVGIS(lat, lon)
            print('Code 200: Succes!')
            tmy.to_pickle("data/lastapicall.pkl")
            
        else: 
                
            print('API call matches last call, using stored data')
    else:
        
        # data does not exist locally
        
        print('Fetching data through API...')
        tmy = _getPVGIS(lat, lon)
        print('Code 200: Succes!')
        tmy.to_pickle("data/lastapicall.pkl")
    
    
    # set relevant parameters needed for further processing based on PVgis
    tmy.wind_height = 10            # height of wind speed data[m]
    tmy.temperature_height = 2      # height of temp data[m]
    tmy.pressure_height = 10        # height of pressure data[m] 
    tmy.lat = lat                   # lattitude of requested data [deg]
    tmy.lon = lon                   # longitude of requested data [deg]
    # overly complicated way to extract 'UTC' from index header
    tmy.tz = tmy.index.name.split('(')[1].split(')')[0]
    return tmy


def _getPVGIS(lat, lon):
    """
    This function uses the non-interactive version of PVGIS to extract a 
    tmy dataset to be used to predict VRE yields for future periods. 
    
    ------ inputs ------    
    Latitude, in decimal degrees, south is negative.
    Longitude, in decimal degrees, west is negative.
    ------- returns -------
    tmy as dataframe with datetime as index, containing 9 timeseries
    Temperature, humidity, global horizontal, beam normal, diffuse horizontal, 
    infrared horizontal, wind speed, wind direction and pressure.  
    
    From PVGIS [https://ec.europa.eu/jrc/en/PVGIS/tools/tmy]
    "A typical meteorological year (TMY) is a set of meteorological data with 
    data values for every hour in a year for a given geographical location. 
    The data are selected from hourly data in a longer time period (normally 
    10 years or more). The TMY is generated in PVGIS following the procedure
    described in ISO 15927-4.
    
    The solar radiation database (DB) used is the default DB for the given 
    location, either PVGIS-SARAH, PVGIS-NSRDB or PVGIS-ERA5. The other 
    meteorogical variables are obtained from the ERA-Inteirm reanalysis."
    """
    outputformat = "json"
    
    request_url = f"https://re.jrc.ec.europa.eu/api/tmy?lat={lat}&lon={lon}&outputformat={outputformat}"
    response = requests.get(request_url)

    if not response.status_code == 200:
        raise ValueError("API get request not succesfull, check your input")
        
    # store to private df
    df = pd.DataFrame(response.json()['outputs']['tmy_hourly'])
    # send to private function to set the date column as index with parser
    tmy = _tmy_dateparser(df)
    
    # for dataframe off-line / in-session storage 
    tmy['lat']  = lat 
    tmy['lon']  = lon 
    
    return tmy
  
def _tmy_dateparser(df):
    
    dateparse = lambda x: datetime.strptime(x, '%Y%m%d:%H%M%S')
    for i in df['time(UTC)'].index:
        df.loc[i, 'time(UTC)']= dateparse(df['time(UTC)'][i]) 
        
    return df.set_index('time(UTC)')