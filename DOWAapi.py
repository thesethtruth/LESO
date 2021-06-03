
#%%
from LESO.dataservice import get_pvgis

tmy = get_pvgis(52, 5)

#%%
import requests
from pathlib import Path
import xarray as xr
import pyproj

lat, lon = 52.6, 2.4


east_bound = 8.2222
west_bound = 1.3114
north_bound = 54.7358
south_bound = 50.1823

if lat > north_bound or lat < south_bound:
    raise ValueError('Supplied lattitude out of range!')
if lon > east_bound or lat < west_bound:
    raise ValueError('Supplied longitude out of range!')

grid_scale = 2500
project = pyproj.Proj("+proj=lcc +lat_1=52.500000 +lat_2=52.500000 +lat_0=52.500000 +lon_0=.000000 +k_0=1.0 +x_0=-92963.487426 +y_0=230383.739533 +a=6371220.000000 +b=6371220.000000")

ix, iy = project(lon, lat)
ix = int(round(ix/grid_scale))
iy = int(round(iy/grid_scale))
#%% create file request

dataset_name = "dowa_netcdf_ts_singlepoint_upd"
version = 1
file = f'DOWA_40h12tg2_fERA5_NETHERLANDS.NL_ix{ix:03}_iy{iy:03}_2018010100-2019010100_v1.0.nc'
api_key = "eyJvcmciOiI1ZTU1NGUxOTI3NGE5NjAwMDEyYTNlYjEiLCJpZCI6IjVjOTBhZWYwODJjYjQ5NmI4NzNmMmRiYWE0NWI0YTRmIiwiaCI6Im11cm11cjEyOCJ9"

# request_url = f"https://api.dataplatform.knmi.nl/open-data/v1/datasets/{dataset_name}/versions/{version}/files"
request_url = f"https://api.dataplatform.knmi.nl/open-data//v1/datasets/{dataset_name}/versions/{version}/files/{file}/url"
r = requests.get(
    request_url, 
    headers={"Authorization": api_key},
)

if r.status_code != 200:
    raise KeyError(f'Download URL request did not succeed, {r.status_code}: {r.json().get("message")}')

#%% download and writeout
download_url = r.json().get('temporaryDownloadUrl')
d = requests.get(
    download_url
)

if d.status_code != 200:
    raise KeyError(f'Download URL request did not succeed, {d.status_code}: {d.json().get("message")}')

file_writeout_name = f'DOWA_{lat}_{lon}.nc'
p = Path(
    f'cache/{file_writeout_name}'
)
p.write_bytes(d.content)

#%% open nc to db file
db = xr.open_dataset(f'cache/{file_writeout_name}')
dowa = db.sel(height=10)[['wspeed', 'p', 'ta']][:-1].to_dataframe()
