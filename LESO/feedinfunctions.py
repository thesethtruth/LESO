from functools import lru_cache
import pandas as pd
from pvlib import irradiance
from pvlib import location
import pvlib
import numpy as np
from pvlib.pvsystem import PVSystem
from pvlib.tracking import SingleAxisTracker
from pvlib.location import Location
from pvlib.modelchain import ModelChain
from pvlib.temperature import TEMPERATURE_MODEL_PARAMETERS
import LESO
from LESO.logging import get_module_logger
logger = get_module_logger(__name__)


def PVlibwrapper(PV_instance, tmy, return_model_object=False):
    PV = PV_instance

    tmy.site = Location(tmy.lat, tmy.lon)

    cec_inverters = pvlib.pvsystem.retrieve_sam("cecinverter")
    cec_modules = pvlib.pvsystem.retrieve_sam("CECMod")

    # default: Jinko Solar Co Ltd JKM350M 72 V
    module = cec_modules[PV.module]

    # default: Huawei Technologies Co Ltd SUN2000 100KTL USH0 800V
    cec_inverter = cec_inverters[PV.inverter]

    temperature_model_parameters = TEMPERATURE_MODEL_PARAMETERS["sapm"][
        "open_rack_glass_glass"
    ]

    if PV.tracking:
        system = SingleAxisTracker(
            axis_tilt=0,
            axis_azimuth=PV.azimuth,
            module_parameters=module,
            inverter_parameters=cec_inverter,
            temperature_model_parameters=temperature_model_parameters,
            strings_per_inverter=PV.strings_per_inverter,
            modules_per_string=PV.modules_per_string,
        )
        losses_model = "no_loss"
    else:
        system = PVSystem(
            surface_tilt=PV.tilt,
            surface_azimuth=PV.azimuth,
            module_parameters=module,
            inverter_parameters=cec_inverter,
            temperature_model_parameters=temperature_model_parameters,
            strings_per_inverter=PV.strings_per_inverter,
            modules_per_string=PV.modules_per_string,
        )
        losses_model = "pvwatts"

    total_module_power = PV.strings_per_inverter * PV.modules_per_string * module["STC"]

    mc = ModelChain(
        system,
        tmy.site,
        aoi_model="ashrae",
        spectral_model="no_loss",
        losses_model=losses_model,
        transposition_model="perez",
    )

    if hasattr(PV, "bifacial_irradiance"):
        mc.run_model_from_effective_irradiance(PV.bifacial_irradiance)
        logger.info(f"PVlibwrapper: {PV.name} triggered run_from")

    else:
        mc.run_model(PVlibweather(tmy))
        logger.info(f"PVlibwrapper: {PV.name} triggered run_model")


    normalized_power = mc.ac / total_module_power
    scaled_power = normalized_power * PV.installed
    # reset index
    scaled_power.index = PV.state.index

    if return_model_object:
        return mc, scaled_power
    else:
        return scaled_power


def bifacial(PV_instance, tmy, return_model=False):

    PV = PV_instance

    # get weather in correct format
    weather = PVlibweather(tmy)
    # define site location for getting solar positions
    tmy.site = location.Location(tmy.lat, tmy.lon, tmy.tz)
    # Get solar azimuth and zenith to pass to the transposition function
    sun = tmy.site.get_solarposition(times=tmy.index)
    # utility dataframe to supply arguments in correct dimensions
    setup = pd.DataFrame(index=tmy.index)
    setup["azimuth"] = 90
    setup["tilt"] = 90
    setup["axis"] = 0

    poa_front, poa_back, front, back = pvlib.bifacial.pvfactors_timeseries(
        solar_azimuth=sun.azimuth,
        solar_zenith=sun.zenith,
        surface_azimuth=setup.azimuth,
        surface_tilt=setup.tilt,
        axis_azimuth=setup.axis,
        timestamps=tmy.index,
        dni=weather.dni,
        dhi=weather.dhi,
        gcr=0.55,
        pvrow_height=2,
        pvrow_width=4,
        albedo=0.23,
        n_pvrows=3,
        index_observed_pvrow=1,
        rho_front_pvrow=0.03,
        rho_back_pvrow=0.05,
        horizon_band_angle=15.0,
    )

    front.index, back.index = PV.state.index, PV.state.index

    front.fillna(0, inplace=True)
    back.fillna(0, inplace=True)
    effective = front + back * PV.bifacial_factor
    poa = poa_front
    bifacial_irradiance = pd.DataFrame(index=PV.state.index)
    bifacial_irradiance["effective_irradiance"] = pd.Series(
        effective, index=PV.state.index
    )
    bifacial_irradiance["poa_global"] = pd.Series(poa, index=PV.state.index)
    bifacial_irradiance["wind_speed"] = pd.Series(
        tmy["WS"].values, index=PV.state.index
    )
    bifacial_irradiance["temp_air"] = pd.Series(tmy["T"].values, index=PV.state.index)

    return bifacial_irradiance


def PVlibweather(tmy):

    weather = tmy.copy(deep=True)
    weather.drop(labels=weather.columns[[1, 5, 7, 8, 9, 10]], axis=1, inplace=True)

    weather.columns = ["temp_air", "ghi", "dni", "dhi", "wind_speed"]

    return weather


def PVpower(PV_instance, tmy):
    """
    Input:      tmy['POA'] -- plane of array
                PV.efficiency
    Output:     PV.power

    This function could be updated to a more sophisticated power model!
    """
    PV = PV_instance

    # make sure the needed data is provided
    if not "POA" in tmy.columns:
        # calculate the poa using isometric conversion
        _calculate_poa(tmy, PV)

    # Generate the power
    power = PV.poa * PV.efficiency 

    # reset the indices to a future year based on starting year
    power.index = PV.state.index

    return power


def ninja_PVpower(PV_instance, tmy, **kwargs):
    """Simple wrapper for power profiles calculated with renewables.ninja"""
    PV = PV_instance
    # Generate the power curve using renewables.ninja
    ignore_cache = kwargs.get("ignore_cache", None)
    if ignore_cache is True:
        power = LESO.dataservice.api.get_renewable_ninja(PV, tmy, ignore_cache=True)
    else:
        power = LESO.dataservice.api.get_renewable_ninja(PV, tmy)
    # scale the curve to desired installed capacity
    power = power * PV.installed
    # reset the indices to a future year based on starting year
    if len(power.index) == len(PV.state.index):
        power.index = PV.state.index
    return power


def windpower(wind_instance, tmy):
    """
    Returns:
        wind.power == wind power time series according using windpowerlib chain

    Inputs:
            wind class
            TMY dataframe (converted to windpowerlib API
                               using _prepare_wind_data)
    """
    from windpowerlib.modelchain import ModelChain
    from windpowerlib.wind_turbine import WindTurbine

    wind = wind_instance

    #### prepare wind data
    wind_df = _prepare_wind_data(tmy, wind)

    #### setup turbine
    turbinespec = {
        "turbine_type": "E-126/4200",  # turbine type as in oedb turbine library
        "hub_height": 135,  # in m
    }

    # initialize WindTurbine object
    turbine = WindTurbine(**turbinespec)

    #### Run wind ModelChain
    # wind speed    : Hellman
    # temperature   : linear gradient
    # density       : ideal gass
    # power output  : power curve

    modelchain_data = {
        "wind_speed_model": "logarithmic",  # 'logarithmic' (default),
        # 'hellman' or
        # 'interpolation_extrapolation'
        "density_model": "ideal_gas",  # 'barometric' (default), 'ideal_gas'
        #  or 'interpolation_extrapolation'
        "temperature_model": "linear_gradient",  # 'linear_gradient' (def.) or
        # 'interpolation_extrapolation'
        "power_output_model": "power_curve",  # 'power_curve' (default) or
        # 'power_coefficient_curve'
        "density_correction": True,  # False (default) or True
        "obstacle_height": 0,  # default: 0
        "hellman_exp": None,
    }  # None (default) or None

    # initialize ModelChain with own specifications and use run_model method to
    # calculate power output
    mc = ModelChain(turbine, **modelchain_data).run_model(wind_df)

    # write power output time series to wind object
    power = mc.power_output / mc.power_output.max() * wind.installed
    if hasattr(wind, "transport_efficiency"):
        power *= wind.transport_efficiency
    power.index = wind.state.index
    return power


def ninja_windpower(wind_instance, tmy):
    """Simple wrapper for power profiles calculated with renewables.ninja"""
    wind = wind_instance
    # Generate the power curve using renewables.ninja
    power = LESO.dataservice.api.get_renewable_ninja(wind, tmy)
    power = power * wind.installed
    # reset the indices to a future year based on starting year
    power.index = wind.state.index
    return power


def _calculate_poa(tmy, PV):
    """
    Input:      tmy irradiance data
    Output:     PV.poa -- plane of array

    Remember, PV GIS (C) defines the folowing:
    G(h): Global irradiance on the horizontal plane (W/m2)                        === GHI
    Gb(n): Beam/direct irradiance on a plane always normal to sun rays (W/m2)     === DNI
    Gd(h): Diffuse irradiance on the horizontal plane (W/m2)                      === DHI
    """
    # define site location for getting solar positions
    tmy.site = location.Location(tmy.lat, tmy.lon, tmy.tz)
    # Get solar azimuth and zenith to pass to the transposition function
    solar_position = tmy.site.get_solarposition(times=tmy.index)
    # Use get_total_irradiance to transpose, based on solar position
    POA_irradiance = irradiance.get_total_irradiance(
        surface_tilt=PV.tilt,
        surface_azimuth=PV.azimuth,
        dni=tmy["Gb(n)"],
        ghi=tmy["G(h)"],
        dhi=tmy["Gd(h)"],
        solar_zenith=solar_position["apparent_zenith"],
        solar_azimuth=solar_position["azimuth"],
    )
    # Return DataFrame
    PV.poa = POA_irradiance["poa_global"]
    return


def _prepare_wind_data(tmy, wind_instance):
    """
    Output:     wind_df
                in format of windpowerlib
                based on (tmy data 'WS, T, SP' and array of constant roughness length)

                date-time indices reset using _reset_times()
                multi-index header, variable name and height of variable

    Input:      tmy
                wind (only .roughness is used now)
    """
    wind = wind_instance
    # temp store the data in np arrays
    wind_speed = tmy["WS"].values.reshape(-1, 1)
    temperature = (tmy["T"] + 273.15).values.reshape(
        -1, 1
    )  # temperature to Kelvin (+273.15)
    pressure = tmy["SP"].values.reshape(-1, 1)
    roughness_length = np.array([wind.roughness] * 8760).reshape(-1, 1)

    # horizontally stack the variables in the right order of column headers
    data_array = np.hstack([wind_speed, temperature, pressure, roughness_length])

    wind_df = pd.DataFrame(
        data_array,
        columns=[
            # Variable names columns [ multi-col 1]
            np.array(["wind_speed", "temperature", "pressure", "roughness_length"]),
            # Speed columns [ multi-col 2]
            np.array([tmy.wind_height, tmy.temperature_height, tmy.pressure_height, 0]),
        ],
    )

    wind_df.columns.names = ["variable_name", "height"]
    wind_df.index = wind.state.index

    return wind_df

def _weeks():
    """
    Returns a 8760x1 array of weeknumbers per hour of the year.
    --
    Used for grouping timeseries to weekly totals.
    """
    indices = np.arange(0, 8760)  # actually 52.17
    weeks = pd.DataFrame(index=indices).index // 168
    weeks = np.where((weeks == 52), 51, weeks)
    return weeks


def _reset_times(df, starting_year):
    """
    Sets the indices of the df to 8760 hourly points starting at the given
    starting_year. Always starts at 1 jan, due to matching TMY data.

    Default starting year is 2021.
    """

    defaultyear = 2021
    # if no start_future is supplied by user, use this default
    if starting_year == None:
        start_future = f"1/1/{defaultyear}"
    else:
        start_future = f"1/1/{starting_year}"

    df.index = pd.date_range(start_future, periods=8760, freq="1h")

    return None


def _timeserie_totals(df):
    """
    Currently unused.

    Could be used to calculate ALL relevant totals in one function.
    Makes it easiear to add new totals / indicators.


    """
    df.yearly = df.power.sum()
    df.weekly = df.power.groupby(_weeks()).sum()
    df.max = df.power.groupby(_weeks()).sum()
    return None
