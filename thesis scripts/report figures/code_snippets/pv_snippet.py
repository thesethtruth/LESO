from LESO import System, PhotoVoltaic

modelname = "PV code snippet"
lat, lon = 52.24, 6.19 # latitude and longitude Arnhem

system = System(
    lat=lat, 
    lon=lon, 
    model_name=modelname)

pv_south = PhotoVoltaic(
    "South-PV",
    azimuth=180, # deg
    tilt=40,     # deg 
    installed=2, # MW
)

system.add_components([pv_south])
system.fetch_input_data()
system.calculate_time_series()