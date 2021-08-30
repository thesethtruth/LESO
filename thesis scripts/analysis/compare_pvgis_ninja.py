import LESO
import pandas as pd

system = LESO.System.read_pickle(r"C:\Users\Sethv\#Universiteit Twente\GIT\LESO\thesis scripts\experiments\models\cablepool.pkl")
lat = system.latitude # old
lon = system.longitude # old 

ninja_pv = LESO.PhotoVoltaic('ninja-pv', use_ninja=True, installed=1)
ninja_wind = LESO.Wind('ninja-wind', use_ninja=True, installed=1)
pvgis_pv = LESO.PhotoVoltaic('pvgis-pv', use_ninja=False, installed=1)
pvgis_wind = LESO.Wind('pvgis-wind', use_ninja=False, installed=1)

system = LESO.System(lat=lat, lon=lon)
system.fetch_input_data()
system.add_components([ninja_pv, pvgis_pv, ninja_wind, pvgis_wind])
system.calculate_time_series()

names = [component.name for component in system.components]
pre_df = {
    component.name: component.state.power for component in system.components
}
df = pd.DataFrame.from_dict(
    pre_df
)
startweek = 16
endweek = 25
info = df.describe()
info.drop('count', axis=0, inplace=True)
info[2:7] = info[2:7].apply(lambda x: round(x*100,2))
info.loc['Yearly yield [kWp/kWh]',:]= df.sum()

pv = df[[name for name in names if '-pv' in name]].plot.density(bw_method=0.05)
wind = df[[name for name in names if '-wind' in name]].plot.density(bw_method=0.05)
xlims= [-0.05, 1.05]
pv.set_xlim(xlims)
wind.set_xlim(xlims)
