#%% required packages
import pandas as pd
import matplotlib.pyplot as plt

#%% read file and find inputs / outputs
location = r"C:\\Users\\Sethv\\#Universiteit Twente\\GIT\\thesis-model\\LESO\\dataservice\\cache\\"
filename = "etmnoordveluwe2018.csv"

filepath = location + filename

df = pd.read_csv(filepath)

inputs, outputs = [], []
for col in df.columns:
    if ".input" in col:
        inputs.append(col)
    if ".output" in col:
        outputs.append(col)

#%% for input analysis ('sustainable') options only

generation_whitelist = [
'buildings_solar_pv_solar_radiation.output (MW)',
'energy_chp_combined_cycle_network_gas.output (MW)',
'energy_chp_local_engine_biogas.output (MW)',
'energy_chp_local_engine_network_gas.output (MW)',
'energy_chp_local_wood_pellets.output (MW)',
'energy_chp_supercritical_waste_mix.output (MW)',
'energy_flexibility_curtailment_electricity.output (MW)',
'energy_flexibility_hv_opac_electricity.output (MW)',
'energy_flexibility_mv_batteries_electricity.output (MW)',
'energy_flexibility_pumped_storage_electricity.output (MW)',
'energy_heat_flexibility_p2h_boiler_electricity.output (MW)',
'energy_heat_flexibility_p2h_heatpump_electricity.output (MW)',
'energy_hydrogen_flexibility_p2g_electricity.output (MW)',
'energy_power_combined_cycle_hydrogen.output (MW)',
'energy_power_geothermal.output (MW)',
'energy_power_hydro_mountain.output (MW)',
'energy_power_hydro_river.output (MW)',
'energy_power_nuclear_gen2_uranium_oxide.output (MW)',
'energy_power_nuclear_gen3_uranium_oxide.output (MW)',
'energy_power_solar_csp_solar_radiation.output (MW)',
'energy_power_solar_pv_solar_radiation.output (MW)',
'energy_power_supercritical_waste_mix.output (MW)',
'energy_power_turbine_hydrogen.output (MW)',
'energy_power_wind_turbine_coastal.output (MW)',
'energy_power_wind_turbine_inland.output (MW)',
'energy_power_wind_turbine_offshore.output (MW)',
'households_flexibility_p2p_electricity.output (MW)',
'households_solar_pv_solar_radiation.output (MW)',
'industry_chemicals_other_flexibility_p2h_hydrogen_electricity.output (MW)',
'industry_chemicals_refineries_flexibility_p2h_hydrogen_electricity.output (MW)',
'industry_other_food_flexibility_p2h_hydrogen_electricity.output (MW)',
'industry_other_paper_flexibility_p2h_hydrogen_electricity.output (MW)',
'transport_car_flexibility_p2p_electricity.output (MW)',
]

interconnectors = [
'energy_interconnector_1_imported_electricity.output (MW)',
'energy_interconnector_2_imported_electricity.output (MW)',
'energy_interconnector_3_imported_electricity.output (MW)',
'energy_interconnector_4_imported_electricity.output (MW)',
'energy_interconnector_5_imported_electricity.output (MW)',
'energy_interconnector_6_imported_electricity.output (MW)',
]

#%% generate the required data for LESO
allow_import = False
if allow_import:
    production = df[[*generation_whitelist, *interconnectors]].copy(deep=True)
else:
    production = df[generation_whitelist].copy(deep=True)

demand = df[inputs].copy(deep=True)

deficit = demand.sum(axis=1) - production.sum(axis=1)


#%% plot whole curves
# filter out categories <0.1% of yearly energy
p_plot = production.copy(deep=True)
for col in p_plot.columns:
    total = p_plot[col].sum()
    if  total < 850:
        p_plot.drop(col, inplace=True, axis=1)

d_plot = demand.copy(deep=True)
for col in d_plot.columns:
    total = d_plot[col].sum()
    if  total < 850:
        d_plot.drop(col, inplace=True, axis=1)

# import plotly.express as px

# fig = px.area(p_plot)
# fig.show()

# %%
