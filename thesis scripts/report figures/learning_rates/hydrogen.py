#%%
from learning_rate_plotting import add_range, add_single_line
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
from LESO.plotting import default_matplotlib_save, default_matplotlib_style

pickle_folder = Path(__file__).parent / "pickles"
#%%

## Schmidt et. al.

# factors
hydrogen_factors = pd.read_pickle(pickle_folder/"hydrogen_factors")
hydrogen_factors.index = [int(i) for i in hydrogen_factors.index]

# seasonal
ref700 = 27117.0 # €/kWp
h700_values = pd.read_pickle(pickle_folder/"hydrogen_700")
h700_values.index = [int(i) for i in h700_values.index]

# subseasonal
ref350 = 16267.0 # €/kWp
h350_values = pd.read_pickle(pickle_folder/"hydrogen_350")
h350_values.index = [int(i) for i in h350_values.index]

## cost factor
fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax)

add_range(ax, hydrogen_factors, "lower", "upper", "steelblue", label="Schmidt et. al. capacity cost uncertainty range")
add_single_line(ax, hydrogen_factors, "center", "steelblue", label="Schmidt et. al. capacity cost center", dash=True)

ax.set_ylabel("projected cost factor (-)")
plt.locator_params(axis="x", integer=True)

default_matplotlib_save(fig, "cost_hydrogen_factor.png")

## absolute
fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax)

add_range(ax, h700_values, "lower", "upper", "steelblue", label="Seasonal H2 capacity cost uncertainty range")
add_range(ax, h350_values, "lower", "upper", "olivedrab", label="Sub-seasonal H2 capacity cost uncertainty range")
add_single_line(ax, h700_values, "center", "steelblue", label="Seasonal H2 capacity cost center", dash=True)
add_single_line(ax, h350_values, "center", "olivedrab", label="Sub-seasonal H2 capacity cost center", dash=True)

ax.set_ylim([0, 28000])
ax.set_ylabel("projected capacity cost (€/kW)")
plt.locator_params(axis="x", integer=True)

default_matplotlib_save(fig, "cost_hydrogen_absolute.png")

#%%
# pd.read_clipboard().T.to_pickle(pickle_folder / "hydrogen_factors")
# pd.read_clipboard().T.to_pickle(pickle_folder / "hydrogen_350")
# pd.read_clipboard().T.to_pickle(pickle_folder / "hydrogen_700")
# %% alternative route!


power_ref2015 = 5417 # € / kW
storage_ref2015 = 31 # € / kWh

storage_cost_350 = 350 * storage_ref2015
storage_cost_700 = 700 * storage_ref2015

hydrogen_factors = pd.read_pickle(pickle_folder/"hydrogen_factors")
hydrogen_factors.index = [int(i) for i in hydrogen_factors.index]
hydrogen_power = hydrogen_factors * power_ref2015

h350_power_values = hydrogen_power + storage_cost_350
h700_power_values = hydrogen_power + storage_cost_700

h350_storage_values = h350_power_values / 350
h700_storage_values = h700_power_values / 700

## absolute power
fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax)

add_range(ax, h700_power_values, "lower", "upper", "steelblue", label="Seasonal H2 capacity cost uncertainty range")
add_range(ax, h350_power_values, "lower", "upper", "olivedrab", label="Sub-seasonal H2 capacity cost uncertainty range")
add_single_line(ax, h700_power_values, "center", "steelblue", label="Seasonal H2 capacity cost center", dash=True)
add_single_line(ax, h350_power_values, "center", "olivedrab", label="Sub-seasonal H2 capacity cost center", dash=True)

ax.set_ylim([0, 28000])
ax.set_ylabel("projected capacity cost (€/kW)")
plt.locator_params(axis="x", integer=True)

default_matplotlib_save(fig, "cost_hydrogen_absolute_power_update.png")

## absolute energy
fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax)

add_range(ax, h700_storage_values, "lower", "upper", "steelblue", label="Seasonal H2 capacity cost uncertainty range")
add_range(ax, h350_storage_values, "lower", "upper", "olivedrab", label="Sub-seasonal H2 capacity cost uncertainty range")
add_single_line(ax, h700_storage_values, "center", "steelblue", label="Seasonal H2 capacity cost center", dash=True)
add_single_line(ax, h350_storage_values, "center", "olivedrab", label="Sub-seasonal H2 capacity cost center", dash=True)

# ax.set_ylim([0, 28000])
ax.set_ylabel("projected capacity cost (€/kWh)")
plt.locator_params(axis="x", integer=True)

default_matplotlib_save(fig, "cost_hydrogen_absolute_energy_update.png")