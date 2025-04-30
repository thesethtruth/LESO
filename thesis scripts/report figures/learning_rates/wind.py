from learning_rate_plotting import add_range, add_single_line
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
from LESO.plotting import default_matplotlib_save, default_matplotlib_style

pickle_folder = Path(__file__).parent / "pickles"


## NP REL ATB
# storage cost
ref_2014 = 1350 # €/kWp
etri14_factors = pd.read_pickle(pickle_folder/"wind_etri2014")
etri14_factors.index = [int(i) for i in etri14_factors.index]
etri14_values = etri14_factors*ref_2014

ref_2017 = 1350 # €/kWp
etri17_factors = pd.read_pickle(pickle_folder/"wind_etri2017")
etri17_factors.index = [int(i) for i in etri17_factors.index]
etri17_values = etri17_factors*ref_2017

## cost factor
all = [etri14_factors, etri17_factors]
fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax)

add_range(ax, etri17_factors, "min", "max", "olivedrab", label="ETRI2017 capacity cost range")
add_range(ax, etri14_factors, "low", "high", "steelblue", label="ETRI2014 capacity cost range")

add_single_line(ax, etri17_factors, "baseline", "olivedrab", label="ETRI2017 baseline scenario", dash=True)
add_single_line(ax, etri14_factors, "ref", "steelblue", label="ETRI2014 ref. scenario", dash=True)
ax.set_ylabel("projected cost factor (-)")
plt.locator_params(axis="x", integer=True)

default_matplotlib_save(fig, "cost_wind_factor.png")

## absolute
all = [etri14_values, etri17_values]
fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax)

add_range(ax, etri17_values, "min", "max", "olivedrab", label="ETRI2017 capacity cost range")
add_range(ax, etri14_values, "low", "high", "steelblue", label="ETRI2014 capacity cost range")

add_single_line(ax, etri17_values, "baseline", "olivedrab", label="ETRI2017 baseline scenario", dash=True)
add_single_line(ax, etri14_values, "ref", "steelblue", label="ETRI2014 ref. scenario", dash=True)
ax.set_ylabel("projected capacity cost (€/kW)")
plt.locator_params(axis="x", integer=True)

default_matplotlib_save(fig, "cost_wind_absolute.png")

#%%
# pd.read_clipboard().T.to_pickle("wind_etri2014")
# %%
fig, ax = plt.subplots(figsize=(5, 3))
add_range(ax, etri17_values, "min", "max", "#133B63", label="test")

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

default_matplotlib_save(fig, "cost_wind_absolute_presentation.png")