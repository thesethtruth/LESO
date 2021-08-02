# RESpost.py

import json
from numpy import product
import pandas as pd
import os
import glob

wd = os.getcwd()
simulations_raw = glob.glob(wd+'/cache/2030*.json')
extractor = lambda x: x.split('\\')[-1].replace(".json", '').replace("2030RES_", '')
simulations_keys = [extractor(x) for x in simulations_raw]

#%%
# sim_list = [json.load(sim) for sim in simulations_raw]
roundd = lambda x: [round(i,1) for i in x]
results = list()
for sim in simulations_raw:
    with open(sim) as infile:
        results.append(json.load(infile))

pv, wind, bat, h2, etm, grid = [], [], [], [], [], []
for res in results:
    for key in res.keys():
        if 'pv' in key:
            pv.append(res[key]['settings']['installed'])
        if 'wind' in key:
            wind.append(res[key]['settings']['installed'])
        if 'lith' in key:
            bat.append(res[key]['settings']['installed'])
        if 'hydro' in key:
            h2.append(res[key]['settings']['installed'])
        if 'dem' in key:
            etm.append(-min(res[key]['state']['power [-]']))
        if 'grid' in key:
            grid.append(res[key]['settings']['installed'])

predf = {
    "PV power capacity (MWp)": roundd(pv),
    "Wind power capacity (MWp)": roundd(wind),
    "Lithium storage capacity (MWh)": roundd(bat),
    "Hydrogen storage capacity (MWh)": roundd(h2),
    "Maximum power demand (MW)": roundd(etm),
    "Installed grid capacity (MW)": roundd(grid),
}

df = pd.DataFrame(predf, index=simulations_keys)
df['Total'] = df.sum()
ndf = df.copy()

ndf.drop(ndf.columns[-3::], axis=1, inplace=True)
production = ndf.iloc[:,:2].copy()
storage = ndf.iloc[:,2:].copy()


from RESposthelper import extract_plotting_specs, make_installed_capacity_chart
labels, colors = extract_plotting_specs(results[0])

ndf = df.copy()
ndf.drop(ndf.columns[-3::], axis=1, inplace=True)
production = ndf.iloc[:,:2].copy()
production.iloc[:,1] = production.iloc[:,1]*3.5
production.iloc[:,0] = production.iloc[:,0]*1.1

production = production.apply(lambda x: x/x.sum(), axis=1)

solar_ratio = [
        0.543269231,
        0.659883721,
        0.880851064,
        1,
        0.467532468,
        0.316455696
    ]

wind_ratio = [
        0.456730769,
        0.340116279,
        0.119148936,
        0,
        0.532467532,
        0.683544304,
    ]

production.columns = ["PV optimal yield %", "Wind optimal yield %"]

production["PV RES 1.0 yield %"] = solar_ratio
production["Wind RES 1.0 yield %"] = wind_ratio
colors = ['#ebd25b', '#8cc0ed', '#c4ae43', '#6894ba']

from RESposthelper import res_compare_pies
fig = res_compare_pies(production, colors)
fig.show()

# if not os.path.exists("images"):
#     os.mkdir("images")

# import plotly.io as pio
# pio.write_image(fig, "images/2030_RES_compare_pie.svg", engine="kaleido")





# || ====== >> bar chart plot << ====== || #

# ndf = df.copy()
# ndf.drop(ndf.columns[-3::], axis=1, inplace=True)
# production = ndf.iloc[:,:2].copy()
# production.iloc[:,1] = production.iloc[:,1]*3.5
# production.iloc[:,0] = production.iloc[:,0]*1.1

# production = production.apply(lambda x: x/x.sum(), axis=1)

# solar_ratio = [
#         0.543269231,
#         0.659883721,
#         0.880851064,
#         1,
#         0.467532468,
#         0.316455696
#     ]

# wind_ratio = [
#         0.456730769,
#         0.340116279,
#         0.119148936,
#         0,
#         0.532467532,
#         0.683544304,
#     ]

# production.columns = ["PV optimal yield %", "Wind optimal yield %"]

# production.insert(loc=1, column="PV RES 1.0 yield %", value=solar_ratio)
# production.insert(loc=3, column="Wind RES 1.0 yield %", value=wind_ratio)
# production.insert(loc=2, value=0, column="")

# colors = ['#ebd25b', '#c4ae43', '#ffffff', '#8cc0ed', '#6894ba']

# from RESposthelper import res_compare_pies
# fig = res_compare_pies(production, colors)
# fig.show()