import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import csv
from scipy.signal import savgol_filter

from LESO.plotting import default_matplotlib_save, default_matplotlib_style




# read csv from ETM and convert into correct unit
with open(r"C:\Users\Sethv\#Universiteit Twente\GIT\LESO\thesis scripts\experiments\cablepool\model\cablepool_price_kea_31ch4_85co2.csv", newline='') as f:
    reader = csv.reader(f)
    data = list(reader)
    energy_market_price = [float(row[1]) for row in data[1:]]

#%% plot the energy price
edf = pd.DataFrame(
    index = pd.date_range(start="01/01/2021", periods=8760, freq='h'),
    data = [price for price in energy_market_price],
    columns= ['ETM price curve']
)

edf['Savgol smoothened price curve'] = savgol_filter(edf['ETM price curve'], 25, 4)
edf.index = pd.date_range(
    start='01/01/2030',
    freq='h',
    periods=8760
)
#%%
from copy import deepcopy as copy
plt.tight_layout(pad=0.3)

rc = {
    'font.family':'Open Sans',
    'font.size' : 10,
    'legend.fontsize' : 8
    }

plt.rcParams.update(rc)

fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax)
fig.set_size_inches(6,2.2)
start = 300
duration = 60
subset = edf.iloc[start:start+duration*24,:]
dt = copy(subset.index)

subset.index = [str(i) for i in subset.index]

subset.plot(
    color=['steelblue', 'firebrick'],
    ax=ax,
    style=['--', '-'],
    linewidth=2
)
# plt.axhline(0, color='darkgrey')

xtick = {
    i*240: dt.strftime("%d %B")[i*240]
    for i in range(6)
}
ax.set_xticks(list(xtick.keys()))
ax.set_xticklabels(list(xtick.values()))
ax.set_xlim([0, duration*24-1])


ax.set_ylim([-10,120])
ax.set_ylabel("Energy price (€/MWh)")
ax.legend(frameon=False)

default_matplotlib_save(fig, "etm_pricecurve_year.png")

#%%
fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax)
fig.set_size_inches(3,2.2)
start = 348
duration = 5
subset = edf.iloc[start:start+duration*24,:]
subset.plot(
    color=['steelblue', 'firebrick'],
    ax=ax,
    style=['--', '-'],
    linewidth=2
)

plt.axhline(0, color='darkgrey')
ax.set_ylim([-10,120])
ax.set_ylabel("Energy price (€/MWh)")
ax.legend(loc= 'upper center', frameon=False)

default_matplotlib_save(fig, "etm_pricecurve_detail.png")

#%%
fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax)
fig.set_size_inches(3,2.2)

edf.plot.hist(
    color=['steelblue', 'firebrick'],
    alpha=0.5,
    bins=50,
    ax=ax
)

plt.axhline(0, color='darkgrey')
ax.set_ylim([0,3000])
ax.set_ylabel("frequency (h/y)")
ax.set_xlabel("Energy price (€/MWh)")
ax.legend(frameon=False)

default_matplotlib_save(fig, "etm_pricecurve_hist.png")

# edf.plot(kind='hist', bins=100)



# %%
