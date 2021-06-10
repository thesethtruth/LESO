import requests
from datetime import datetime
import pandas as pd
import os.path
import os
from pathlib import Path
import xarray as xr
import pyproj
from bs4 import BeautifulSoup
import json
from functools import lru_cache

@lru_cache(10)
def get_pvgis(lat, lon):
    """
    Returns:
        TMY as dataframe with information appended as class items. 
    Inputs:
        Lattitude
        Longtiude 
    ---
    Checks the cache for a match (stored offline) to save the time of getting 
    data from PV GIS
    """
    filestring = f"LESO/dataservice/cache/DOWA_lat_{str(lat)}_lon_{str(lon)}.pkl"
    if os.path.isfile(filestring):
        
        # read last API call
        tmy = pd.read_pickle(filestring)
        
        if not (tmy['lat'][1] == lat and tmy['lon'][1] == lon):
            
            # get new data true API
            print('Fetching data through API...')
            tmy = _getPVGIS(lat, lon)
            print('Code 200: Succes!')
            tmy.to_pickle(filestring)
            
        else: 
                
            print('API call matches last call, using stored data')
    else:
        
        # data does not exist locally
        
        print('Fetching data through API...')
        tmy = _getPVGIS(lat, lon)
        print('Code 200: Succes!')
        tmy.to_pickle(filestring)
    
    
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
    tmy.columns = ['T', *tmy.columns[1:6].values, 'WS', 'WD', 'SP', 'lat', 'lon']

    return tmy

def _tmy_dateparser(df):
    
    dateparse = lambda x: datetime.strptime(x, '%Y%m%d:%H%M%S')
    for i in df['time(UTC)'].index:
        df.loc[i, 'time(UTC)']= dateparse(df['time(UTC)'][i]) 
        
    return df.set_index('time(UTC)')

def get_dowa(lat, lon, height=100):


    filestring = f"LESO/dataservice/cache/DOWA_{lat}_{lon}_{height}.pkl"
    
    if os.path.isfile(filestring):
        
        # read last API call
        dowa = pd.read_pickle(filestring)
        
    else:
        
        # data does not exist locally
        
        print('Fetching data through API...')
        dowa = _getDOWA(lat, lon, height)
        print('Code 200: Succes!')
        dowa.to_pickle(filestring)

    # set height of data points in same way as PVGIS api
    dowa.temperature_height = height     
    dowa.pressure_height = height       
    dowa.wind_height = height
    
    
    return dowa

def _getDOWA(lat, lon, height=100):
    """
    This function does the actual hard work of api's: requesting and processing the response.
    """
    api_key = "eyJvcmciOiI1ZTU1NGUxOTI3NGE5NjAwMDEyYTNlYjEiLCJpZCI6IjVjOTBhZWYwODJjYjQ5NmI4NzNmMmRiYWE0NWI0YTRmIiwiaCI6Im11cm11cjEyOCJ9"

    # check bounds based on data set meta data
    east_bound, west_bound, north_bound, south_bound = 8.2222, 1.3114, 54.7358, 50.1823
    if lat > north_bound or lat < south_bound:
        raise ValueError('Supplied lattitude out of range!')
    if lon > east_bound or lat < west_bound:
        raise ValueError('Supplied longitude out of range!')

    # map to indices as given in DOWA using projection
    grid_scale = 2500
    project = pyproj.Proj("+proj=lcc +lat_1=52.500000 +lat_2=52.500000 +lat_0=52.500000 +lon_0=.000000 +k_0=1.0 +x_0=-92963.487426 +y_0=230383.739533 +a=6371220.000000 +b=6371220.000000")
    ix, iy = project(lon, lat)
    ix = int(round(ix/grid_scale))
    iy = int(round(iy/grid_scale))
    
    # create file request
    dataset_name = "dowa_netcdf_ts_singlepoint_upd"
    version = 1
    file = f'DOWA_40h12tg2_fERA5_NETHERLANDS.NL_ix{ix:03}_iy{iy:03}_2018010100-2019010100_v1.0.nc'
    api_key = "eyJvcmciOiI1ZTU1NGUxOTI3NGE5NjAwMDEyYTNlYjEiLCJpZCI6IjVjOTBhZWYwODJjYjQ5NmI4NzNmMmRiYWE0NWI0YTRmIiwiaCI6Im11cm11cjEyOCJ9"

    # request download url
    request_url = f"https://api.dataplatform.knmi.nl/open-data//v1/datasets/{dataset_name}/versions/{version}/files/{file}/url"
    r = requests.get(
        request_url, 
        headers={"Authorization": api_key},
    )

    # either raise error or continue with a correct download url
    if r.status_code != 200:
        raise KeyError(f'Download URL request did not succeed, {r.status_code}: {r.json().get("message")}')
    else:
        download_url = r.json().get('temporaryDownloadUrl')
    
    # request download and if success then continue to writeout
    d = requests.get(
        download_url
    )

    if d.status_code != 200:
        raise KeyError(f'Download URL request did not succeed, {d.status_code}: {d.json().get("message")}')

    # write out
    temp_writeout_file = f'LESO/dataservice/DOWA_{lat}_{lon}_{height}.nc'
    p = Path(
        temp_writeout_file
    )
    p.write_bytes(d.content)

    # open nc to xarray for processing
    db = xr.open_dataset(temp_writeout_file)
    dowa = db.sel(height=height)[['ta', 'wspeed', 'wdir', 'p']].to_dataframe()
    
    # drop x and y index
    dowa.index = dowa.index.droplevel(level=[1,2])
    
    # convert to celsius for consistency with PVGIS
    dowa.ta = dowa.ta - 275.15
    # drop 8761th point for consistency
    dowa.drop(dowa.index[-1], inplace=True)
    dowa.drop('height', axis=1, inplace=True)
    dowa.columns = ['T', 'WS', 'WD', 'SP', 'lon', 'lat']

    # close connection and delete temp file
    db.close()
    os.remove(temp_writeout_file)
    return dowa

def etm_id_extractor_external(etmDemand_instance, scenario_id):
        etmd = etmDemand_instance
        # if 4 digit and not None (also len = 4) then extract id
        if len(str(scenario_id)) == 4 and scenario_id is not None:

            url = f"https://pro.energytransitionmodel.com/saved_scenarios/{scenario_id}/load"
            r = requests.get(url)
            if r.status_code != 200:
                raise ValueError("Response not 200!")

            soup = BeautifulSoup(r.content, "html.parser")

            scripts = soup.find_all("script")
            for script in scripts:
                string = script.string
                if string is not None and string.find("preset_scenario_id") > 0:
                    start = (
                        string.find("preset_scenario_id")
                        + len("preset_scenario_id")
                        + 2
                    )
                    end = start + 6
                    preset_scenario_id = int(string[start:end])

            _scenario_id = preset_scenario_id
            etmd.locked = True  # due to using preset_scenario_id
            etmd.title = soup.find("span", attrs={"class": "name"}).text[1:-1]

        # if 6 digit or None then just keep that id
        elif len(str(scenario_id)) == 6 or scenario_id is None:
            _scenario_id = scenario_id
            etmd.locked = False
            etmd.title = etm_get_title_external(_scenario_id)

        else:
            raise ValueError(f"Scenario ID provided is not valid: {scenario_id}")

        return _scenario_id

def etm_get_title_external(scenario_id):
    
    url = f"https://engine.energytransitionmodel.com/api/v3/scenarios/{scenario_id}"
    r = requests.get(url)
    if r.status_code != 200:
        raise ValueError("Response not 200")
    di = json.loads(r.content)
    title = di["title"]

    return title