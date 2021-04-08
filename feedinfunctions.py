import pandas as pd
from pvlib import irradiance
from pvlib import location
import numpy as np

def PVpower(PV_instance, tmy):
    """
    Input:      tmy['POA'] -- plane of array
                PV.efficiency
                PV.area
    Output:     PV.power
    
    This function should be updated to a more sophisticated power model!
    """ 
    PV = PV_instance
    
    # make sure the needed data is provided
    if not 'POA' in tmy.columns:
        # calculate the poa using isometric conversion
        _calculate_poa(tmy, PV)

    # Generate the power
    power = PV.poa   * PV.efficiency * PV.area
    
    # reset the indices to a future year based on starting year
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
    wind_df = _prepare_wind_data(tmy, wind, wind.start_date)
    
    #### setup turbine
    turbinespec = {
            'turbine_type': 'E-126/4200',  # turbine type as in oedb turbine library
            'hub_height': 135  # in m
        }
    
    # initialize WindTurbine object
    turbine = WindTurbine(**turbinespec)
    
    #### Run wind ModelChain
    # wind speed    : Hellman
    # temperature   : linear gradient
    # density       : ideal gass
    # power output  : power curve
    
    modelchain_data = {
        'wind_speed_model': 'logarithmic',      # 'logarithmic' (default),
                                                # 'hellman' or
                                                # 'interpolation_extrapolation'
        'density_model': 'ideal_gas',           # 'barometric' (default), 'ideal_gas'
                                                #  or 'interpolation_extrapolation'
        'temperature_model': 'linear_gradient', # 'linear_gradient' (def.) or
                                                # 'interpolation_extrapolation'
        'power_output_model': 'power_curve',    # 'power_curve' (default) or
                                                # 'power_coefficient_curve'
        'density_correction': True,             # False (default) or True
        'obstacle_height': 0,                   # default: 0
        'hellman_exp': None}                    # None (default) or None
    
    # initialize ModelChain with own specifications and use run_model method to
    # calculate power output
    mc = ModelChain(turbine, **modelchain_data).run_model(wind_df)
    
    # write power output time series to wind object
    power = mc.power_output / mc.power_output.max() * wind.installed
   
    return power

def _calculate_poa(tmy, PV):
    """
    Input:      tmy irradiance data
    Output:     tmy['POA'] -- plane of array
    
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
        surface_tilt= PV.tilt,
        surface_azimuth= PV.azimuth,
        dni=tmy["Gb(n)"],
        ghi=tmy["G(h)"],
        dhi=tmy["Gd(h)"],
        solar_zenith=solar_position['apparent_zenith'],
        solar_azimuth=solar_position['azimuth'])
    # Return DataFrame
    PV.poa = POA_irradiance['poa_global']
    return

def _prepare_wind_data(tmy, wind, starting_year):
    """
    Output:     wind_df 
                in format of windpowerlib
                based on (tmy data 'WS10m, T2m, SP' and array of constant roughness length)
                
                date-time indices reset using _reset_times()
                multi-index header, variable name and height of variable
                
    Input:      tmy
                wind (only .roughness is used now)    
    """
    
    # temp store the data in np arrays
    wind_speed = tmy['WS10m'].values.reshape(-1,1)
    temperature = (tmy['T2m']+273.15).values.reshape(-1,1) # temperature to Kelvin (+273.15)
    pressure = tmy['SP'].values.reshape(-1,1)
    roughness_length = np.array([wind.roughness] * 8760).reshape(-1,1)
    
    # horizontally stack the variables in the right order of column headers
    data_array = np.hstack([wind_speed, temperature, pressure, roughness_length])
    
    wind_df = pd.DataFrame(data_array,
                              columns=[
                                      # Variable names columns [ multi-col 1]
                                      np.array(['wind_speed',
                                                 'temperature',
                                                 'pressure',
                                                 'roughness_length']),
                                       # Speed columns [ multi-col 2]
                                       np.array([tmy.wind_height, 
                                                 tmy.temperature_height, 
                                                 tmy.pressure_height,
                                                 0])]
                                                 )
    
    wind_df.columns.names = ['variable_name', 'height']
    wind_df.index = wind.state.index
    
    return wind_df


def _weeks():
    """
    Returns a 8760x1 array of weeknumbers per hour of the year.
    --
    Used for grouping timeseries to weekly totals.
    """
    indices = np.arange(0,8760)                   # actually 52.17
    weeks = pd.DataFrame(index = indices).index // 168
    weeks = np.where((weeks== 52),51,weeks)
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
        start_future = f'1/1/{defaultyear}'
    else:
        start_future = f'1/1/{starting_year}'
   
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










