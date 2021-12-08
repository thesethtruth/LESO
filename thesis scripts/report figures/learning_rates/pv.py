import pandas as pd
import numpy as np
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from LESO.plotting import default_matplotlib_save, default_matplotlib_style

years = [2030, 2040, 2050]
## Fraunhofer 2015 Current and Future Cost of Photovoltaics
ref_2015_f = 1 # €/Wp
fraunhofer = np.array([
    [0.7547738693467337, 0.5537688442211057], 
    [0.6743718592964826, 0.38492462311557796],
    [0.606030150753769, 0.27939698492462317]
]) # data from figure 42, page 53

fraunhofer_factors = pd.DataFrame(fraunhofer, index=years, columns=['max', 'min'])
fraunhofer_factors['ref'] = fraunhofer_factors.mean(axis=1)
fraunhofer_factors.loc[2015, :] = [1.03, .93, 1]
fraunhofer_factors.sort_index(inplace=True)
fraunhofer_values = fraunhofer_factors*ref_2015_f*1000



## ETRI 2014
ref_2014_e = 980 # €/kWp
etri_2014 = np.array([ 
    [720, 520], 
    [650, 470],
    [580, 420]
]) # data from table 7, page 20 €/kWp


etri14_values = pd.DataFrame(etri_2014, index=years, columns=['max', 'min'])
etri14_values['ref'] = [640, 580, 520]
etri14_values.loc[2015, :] = [*[ref_2014_e]*3]
etri14_values.loc[2020, :] = [900, 650, 800]
etri14_values.sort_index(inplace=True)
etri14_factors = etri14_values/ref_2014_e

etri_2017 = np.array([
    [720, 580, 500],
    [600, 450, 370],
    [450, 370, 320],
    [390, 310, 260],
    [870, 780, 730]]
).T # data from excel sheet €/kWp

etri17_colums = [
    "baseline",
    "diversified",
    "proRES",
    "min",
    "max",
]
ref_2017_e = 1020 # €/kWp
etri17_values = pd.DataFrame(etri_2017, index=years, columns=etri17_colums)
etri17_values.loc[2015, :] = [*[ref_2017_e]*5]
etri17_values.loc[2020, :] = [830, 790, 690, 650, 920]
etri17_values.sort_index(inplace=True)
etri17_factors = etri17_values/ref_2017_e


def add_single_line(df, column, color, label=None, dash=False, marker='o', alpha=1):

    ax.plot(
        column,
        data=df,
        marker=marker,
        linestyle= '-' if not dash else '--',
        mfc=color,
        color=color,
        label=label if label != None else "_d",
        alpha=alpha,
    )
    ax.legend(loc="best", frameon=False)

def add_range(df, lower_col, upper_col, color, label):

    ax.fill_between(
        df.index,
        upper_col,
        lower_col,
        data=df,
        color=color,
        label=label,
        alpha=0.2,
    )    
    add_single_line(df, lower_col, color, alpha=0.5, marker=None)
    add_single_line(df, upper_col, color, alpha=0.5, marker=None)
    
    ax.set_xlim([df.index[0]-1, df.index[-1]+1])
    ax.set_ylim([0, df.max().max()*1.05])
    
    
    ax.legend(loc="best", frameon=False)

## cost factor
all = [fraunhofer_factors, etri14_factors, etri17_factors]
fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax)

add_range(etri17_factors, "min", "max", "olivedrab", label="ETRI2017 power capacity cost range")
add_range(etri14_factors, "min", "max", "steelblue", label="ETRI2014 capacity cost range")
add_range(fraunhofer_factors, "min", "max", "firebrick", label="Fraunhofer capacity cost range")

add_single_line(etri17_factors, "baseline", "olivedrab", label="ETRI2017 baseline scenario", dash=True)
add_single_line(etri14_factors, "ref", "steelblue", label="ETRI2014 ref. scenario", dash=True)
add_single_line(fraunhofer_factors, "ref", "firebrick", label="Fraunhofer mean scenario", dash=True)
ax.set_ylabel("projected cost factor (-)")
plt.locator_params(axis="x", integer=True)

default_matplotlib_save(fig, "cost_pv_factor.png")

all = [fraunhofer_values, etri14_values, etri17_values]
fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax)

add_range(etri17_values, "min", "max", "olivedrab", label="ETRI2017 power capacity cost range")
add_range(etri14_values, "min", "max", "steelblue", label="ETRI2014 capacity cost range")
add_range(fraunhofer_values, "min", "max", "firebrick", label="Fraunhofer capacity cost range")

add_single_line(etri17_values, "baseline", "olivedrab", label="ETRI2017 baseline scenario", dash=True)
add_single_line(etri14_values, "ref", "steelblue", label="ETRI2014 ref. scenario", dash=True)
add_single_line(fraunhofer_values, "ref", "firebrick", label="Fraunhofer mean scenario", dash=True)
ax.set_ylabel("projected capacity cost (€/kWp)")
ax.set_ylim([0, 1050])
plt.locator_params(axis="x", integer=True)

default_matplotlib_save(fig, "cost_pv_absolute.png")



#%%

fig, ax = plt.subplots(figsize=(5, 3))
add_range(etri17_values, "min", "max", "#133B63", label="test")

plt.tight_layout(pad=0.3)
rc = {
    "font.family": "Open Sans",
    "font.weight": "bold",
    "font.style": "italic",
    "font.size": 14,
}

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

ax.spines['left'].set_color("#133B63")
ax.spines['bottom'].set_color("#133B63")
ax.tick_params(which='both', colors='#133B63')






ax.set_ylim([0, etri17_values.max().max()*1.05])
ax.set_ylabel("€/kW", weight="bold", size=14, color='#133B63')
plt.rcParams.update(rc)
ax.get_legend().remove()

default_matplotlib_save(fig, "cost_pv_absolute_presentation.png")