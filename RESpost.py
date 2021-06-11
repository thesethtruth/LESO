# RESpost.py

import json
import pandas as pd
import os
import glob

wd = os.getcwd()
simulations_raw = glob.glob(wd+'/cache/*.json')
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

ndf.drop(ndf.columns[-2::], axis=1, inplace=True)
production = ndf.iloc[:,:2].copy()
storage = ndf.iloc[:,2:].copy()


from RESposthelper import extract_plotting_specs, make_installed_capacity_chart
labels, colors = extract_plotting_specs(results[0])

storage.iloc[:,1] = storage.iloc[:,1]/25
fig = make_installed_capacity_chart(production, colors)
fig2 = make_installed_capacity_chart(storage, colors[2:])

if not os.path.exists("images"):
    os.mkdir("images")
    
fig.write_image("images/production.svg")
fig2.write_image("images/storage.svg")