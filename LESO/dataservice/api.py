import requests
import os
import warnings
import json
import pickle

from functools import lru_cache
from pathlib import Path
from datetime import datetime
import pandas as pd

from .api_static import renewable_ninja_turbines
from LESO.leso_logging import get_module_logger

logger = get_module_logger(__name__)

CACHE_FOLDER = Path(__file__).parent / "cache"


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
    filestring = f"pvgis_lat_{str(lat)}_lon_{str(lon)}.pkl"
    req_args = {"lat": lat, "lon": lon}
    filepath = CACHE_FOLDER / filestring

    if os.path.isfile(filepath):

        # read last API call
        tmy = pd.read_pickle(filepath)

        if not (tmy["lat"][1] == lat and tmy["lon"][1] == lon):

            # get new data true API
            logger.debug(
                f"get_pvgis: fetching data through API...", extra={"dct": req_args}
            )
            tmy = _getPVGIS(lat, lon)
            logger.debug(f"get_pvgis: code 200: success...", extra={"dct": req_args})
            tmy.to_pickle(filepath)

        else:

            logger.debug(f"get_pvgis: using stored data...", extra={"dct": req_args})
    else:

        # data does not exist locally

        logger.debug(
            f"get_pvgis: fetching data through API...", extra={"dct": req_args}
        )
        tmy = _getPVGIS(lat, lon)
        logger.debug(f"get_pvgis: code 200: success...", extra={"dct": req_args})
        tmy.to_pickle(filepath)

    # set relevant parameters needed for further processing based on PVgis
    tmy.wind_height = 10  # height of wind speed data[m]
    tmy.temperature_height = 2  # height of temp data[m]
    tmy.pressure_height = 10  # height of pressure data[m]
    tmy.lat = lat  # lattitude of requested data [deg]
    tmy.lon = lon  # longitude of requested data [deg]
    # overly complicated way to extract 'UTC' from index header
    tmy.tz = tmy.index.name.split("(")[1].split(")")[0]
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
        error = response.json()["message"]
        raise ValueError(
            f"Request to PVGIS not successful, check your input: {error}. URL: {request_url}"
        )

    # store to private df
    df = pd.DataFrame(response.json()["outputs"]["tmy_hourly"])
    # send to private function to set the date column as index with parser
    tmy = _tmy_dateparser(df)

    # for dataframe off-line / in-session storage
    tmy["lat"] = lat
    tmy["lon"] = lon
    tmy.columns = ["T", *tmy.columns[1:6].values, "WS", "WD", "SP", "lat", "lon"]

    return tmy


def _tmy_dateparser(df):

    dateparse = lambda x: datetime.strptime(x, "%Y%m%d:%H%M%S")
    for i in df["time(UTC)"].index:
        df.loc[i, "time(UTC)"] = dateparse(df["time(UTC)"][i])

    return df.set_index("time(UTC)")


def get_dowa(lat, lon, height=100):

    filestring = f"LESO/dataservice/cache/DOWA_{lat}_{lon}_{height}.pkl"

    if os.path.isfile(filestring):

        # read last API call
        dowa = pd.read_pickle(filestring)

    else:

        # data does not exist locally

        logger.debug(
            f"get_dowa: fetching data through API... [lat:{lat}, lon:{lon}, height:{height}]"
        )
        dowa = _getDOWA(lat, lon, height)
        logger.debug(
            f"get_dowa: code 200: success... [lat:{lat}, lon:{lon}, height:{height}]"
        )
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
    import xarray as xr
    import pyproj
    from secrets.keys import DOWA_key as api_key

    # check bounds based on data set meta data
    east_bound, west_bound, north_bound, south_bound = 8.2222, 1.3114, 54.7358, 50.1823
    if lat > north_bound or lat < south_bound:
        raise ValueError("Supplied lattitude out of range!")
    if lon > east_bound or lat < west_bound:
        raise ValueError("Supplied longitude out of range!")

    # map to indices as given in DOWA using projection
    grid_scale = 2500
    project = pyproj.Proj(
        "+proj=lcc +lat_1=52.500000 +lat_2=52.500000 +lat_0=52.500000 +lon_0=.000000 +k_0=1.0 +x_0=-92963.487426 +y_0=230383.739533 +a=6371220.000000 +b=6371220.000000"
    )
    ix, iy = project(lon, lat)
    ix = int(round(ix / grid_scale))
    iy = int(round(iy / grid_scale))

    # create file request
    dataset_name = "dowa_netcdf_ts_singlepoint_upd"
    version = 1
    file = f"DOWA_40h12tg2_fERA5_NETHERLANDS.NL_ix{ix:03}_iy{iy:03}_2018010100-2019010100_v1.0.nc"

    # request download url
    request_url = f"https://api.dataplatform.knmi.nl/open-data//v1/datasets/{dataset_name}/versions/{version}/files/{file}/url"
    r = requests.get(
        request_url,
        headers={"Authorization": api_key},
    )

    # either raise error or continue with a correct download url
    if r.status_code != 200:
        raise KeyError(
            f'Download URL request did not succeed, {r.status_code}: {r.json().get("message")}'
        )
    else:
        download_url = r.json().get("temporaryDownloadUrl")

    # request download and if success then continue to writeout
    d = requests.get(download_url)

    if d.status_code != 200:
        raise KeyError(
            f'Download URL request did not succeed, {d.status_code}: {d.json().get("message")}'
        )

    # write out
    temp_writeout_file = f"LESO/dataservice/DOWA_{lat}_{lon}_{height}.nc"
    p = Path(temp_writeout_file)
    p.write_bytes(d.content)

    # open nc to xarray for processing
    db = xr.open_dataset(temp_writeout_file)
    dowa = db.sel(height=height)[["ta", "wspeed", "wdir", "p"]].to_dataframe()

    # drop x and y index
    dowa.index = dowa.index.droplevel(level=[1, 2])

    # convert to celsius for consistency with PVGIS
    dowa.ta = dowa.ta - 275.15
    # drop 8761th point for consistency
    dowa.drop(dowa.index[-1], inplace=True)
    dowa.drop("height", axis=1, inplace=True)
    dowa.columns = ["T", "WS", "WD", "SP", "lon", "lat"]

    # close connection and delete temp file
    db.close()
    os.remove(temp_writeout_file)
    return dowa


def get_renewable_ninja(instance, tmy, ignore_cache=False):

    lat = tmy.lat[0]
    lon = tmy.lon[0]

    if hasattr(instance, "tilt"):
        name = "pv"
        t = instance.tilt
        a = instance.azimuth
        filestring = f"cache\\ninja_{name}_lat_{str(lat)}_lon_{str(lon)}_a_{a}_t{t}.pkl"
        req_args = {
            "type": name,
            "lat": lat,
            "lon": lon,
            "azimuth": a,
            "tilt": t,
        }
        kwargs = {
            "tilt": instance.tilt,
            "azim": instance.azimuth,
            "system_loss": instance.efficiency,
        }
    elif hasattr(instance, "hub_height"):
        name = "wind"
        turbinetype = instance.turbine_type.lower().replace(" ", "_")
        hubheight = str(instance.hub_height)
        filestring = f"cache\\ninja_{name}_lat_{str(lat)}_lon_{str(lon)}_h_{hubheight}_{turbinetype}.pkl"
        req_args = {
            "type": name,
            "lat": lat,
            "lon": lon,
            "hubheight": hubheight,
            "turbinetype": turbinetype,
        }
        kwargs = {
            "height": instance.hub_height,
            "turbine": instance.turbine_type,
        }

    dataservice_folder = os.path.dirname(__file__)
    filepath = os.path.join(dataservice_folder, filestring)

    if os.path.isfile(filepath) and not ignore_cache:

        # read last API call
        data = pd.read_pickle(filepath)
        logger.debug(
            f"get_renewable_ninja: using stored data...", extra={"dct": req_args}
        )

    else:

        # data does not exist locally
        logger.debug(
            f"get_renewable_ninja: fetching data through API...",
            extra={"dct": req_args},
        )
        data = _get_renewable_ninja(
            name=name,
            date_from=instance.date_from,
            date_to=instance.date_to,
            dataset=instance.dataset,
            lat=lat,
            lon=lon,
            **kwargs,
        )
        logger.debug(
            f"get_renewable_ninja: code 200: success...", extra={"dct": req_args}
        )
        if not ignore_cache:
            data.to_pickle(filepath)

    return data


def _get_renewable_ninja(
    name: str,
    date_from: str,
    date_to: str,
    dataset: str,
    lat: float,
    lon: float,
    **kwargs,
) -> pd.DataFrame:
    """ " API handler for renewables.ninja"""

    from secrets.keys import renewable_ninja_token as token

    api_base = "https://www.renewables.ninja/api/"

    s = requests.session()
    # Send token header with each request
    s.headers = {"Authorization": "Token " + token}

    ## General
    args = {
        "lat": lat,
        "lon": lon,
        "date_from": date_from,
        "date_to": date_to,
        "dataset": dataset,
        "format": "json",
    }

    ## PV
    if name == "pv":

        api_end = "data/pv"

        args.update(
            {
                "capacity": 1,  # force to one to never exceed ninjas capacity limit
                "system_loss": kwargs.get("system_loss"),
                "tracking": 0,
                "tilt": kwargs.get("tilt"),
                "azim": kwargs.get("azim"),
            }
        )

    ## Wind
    if name == "wind":

        api_end = "data/wind"
        turbine_type = kwargs.get("turbine")

        if turbine_type not in renewable_ninja_turbines:
            turbine_type_d = "Vestas V90 2000"
            msg = f"{turbine_type} not found in renwable.ninja, resorting to default ({turbine_type_d})."
            warnings.warn(msg)
            turbine_type = turbine_type_d

        args.update(
            {
                "capacity": 1,  # force to one to never exceed ninjas capacity limit
                "height": kwargs.get("height"),
                "turbine": turbine_type,
            }
        )

    url = api_base + api_end
    r = s.get(url, params=args)
    if r.status_code != 200:
        raise ConnectionError(
            f"Renewables.ninja did not return succesfully: {r.reason}"
        )

    # Parse JSON to get a pandas.DataFrame of data and dict of metadata
    parsed_response = json.loads(r.text)

    data = pd.read_json(json.dumps(parsed_response["data"]), orient="index")

    return data


def get_etm_curve(
    session_id: int,
    generation_whitelist: list,
    allow_import=False,
    allow_export=False,
    raw=False,
) -> pd.DataFrame:

    if raw:
        df = _get_etm_curve(
            session_id=session_id,
            generation_whitelist=generation_whitelist,
            allow_import=allow_import,
            allow_export=allow_export,
            raw=True,
        )
        return df
    else:
        timetag = datetime.now().strftime("%y%m%d")
        filestring = f"ETM_curves_{session_id}_{timetag}_i{int(allow_import)}_e{int(allow_export)}.pkl"
        req_args = {
            "session_id": session_id,
            "timetag": timetag,
            "allow_import": allow_import,
            "allow_export": allow_export,
        }

        filepath = CACHE_FOLDER / filestring

        if os.path.isfile(filepath):

            # read last API call
            with open(filepath, "rb") as infile:
                array = pickle.load(infile)

            logger.debug(
                f"get_etm_curve: using stored data...", extra={"dct": req_args}
            )

        else:

            # data does not exist locally
            logger.debug(
                f"get_etm_curve: downloading ETM curve...", extra={"dct": req_args}
            )
            array = _get_etm_curve(
                session_id=session_id,
                generation_whitelist=generation_whitelist,
                allow_import=allow_import,
                allow_export=allow_export,
                raw=False,
            )
            logger.debug(f"get_etm_curve: success... probably", extra={"dct": req_args})

            with open(filepath, "wb") as outfile:
                pickle.dump(array, outfile)

        return array


def _get_etm_curve(
    session_id: int,
    generation_whitelist: list,
    allow_import: bool = False,
    allow_export: bool = False,
    raw: bool = False,
) -> pd.DataFrame:
    # read file and find inputs / outputs
    url = f"https://engine.energytransitionmodel.com/api/v3/scenarios/{session_id}/curves/merit_order.csv"
    df = pd.read_csv(url)

    inputs, outputs = [], []
    for col in df.columns:
        if ".input" in col:
            inputs.append(col)
        if ".output" in col:
            outputs.append(col)
    # note: len(df.columns) == 173, inputs + outputs == 171.

    export_grid, import_grid = [], []
    for col in df.columns:
        if "inter" in col and "export" in col:
            export_grid.append(col)
        if "inter" in col and "import" in col:
            import_grid.append(col)

    # ETM by default does not close the energy balance 100%, so we need to add it explicitly
    default_deficit = df["deficit"]
    demand = df[inputs].copy(deep=True)

    if allow_export is False:
        demand.drop(labels=export_grid, axis=1, inplace=True)

    # if no generation_whitelist is supplied, none of the ETM generation is allowed and thus
    # will the total residual curve be exactly the same as the sum of all demand.
    if generation_whitelist is None or generation_whitelist is False:
        deficit = -demand.sum(axis=1) - default_deficit

    # for input analysis ('sustainable') options only
    elif isinstance(generation_whitelist, list):
        if allow_import is True:
            production = df[[*generation_whitelist, *import_grid]].copy(deep=True)
        else:
            production = df[generation_whitelist].copy(deep=True)
        # in convention; demand is negative
        deficit = production.sum(axis=1) - demand.sum(axis=1) - default_deficit

    if raw:
        return df
    else:
        return deficit.values
