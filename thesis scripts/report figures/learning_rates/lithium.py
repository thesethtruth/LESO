from LESO.plotting import default_matplotlib_save, default_matplotlib_style
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


## NP REL ATB
# storage cost
ref_2020_s = 277 # $/kWh
storage_projection = np.array([
    [1.0, 1.0, 1.0], 
    [0.61, 0.69, 0.85], 
    [0.41, 0.53, 0.7], 
    [0.25, 0.37, 0.7]
]) # kWh from ATB sheet

ref_2020_p = 257 # $/kW
power_projection = np.array([
    [1.0, 1.0, 1.0], 
    [0.62, 0.77, 0.87], 
    [0.42, 0.77, 0.81], 
    [0.25, 0.71, 0.81]
]) # kW from ATB sheet

years = [2020, 2025, 2030, 2050]
scenarios = ["advanced", "moderate", "conservative"]
atb_storage = pd.DataFrame(storage_projection, index=years, columns=scenarios)
atb_power = pd.DataFrame(power_projection, index=years, columns=scenarios)

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
fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax)
add_range(atb_power, "conservative", "advanced", "olivedrab", label="ATB power capacity cost range")
add_single_line(atb_power, "moderate", "olivedrab", label="ATB power moderate scenario", dash=True)
add_range(atb_storage, "conservative", "advanced", "steelblue", label="ATB storage capacity cost range")
add_single_line(atb_storage, "moderate", "steelblue", label="ATB storage moderate scenario", dash=True)
ax.set_ylabel("projected cost factor (-)")

default_matplotlib_save(fig, "cost_lithium_factor.png")

## cost absolut
fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax)
atb_power *= ref_2020_s
atb_storage *= ref_2020_p

add_range(atb_power, "conservative", "advanced", "olivedrab", label="ATB power capacity cost range")
add_single_line(atb_power, "moderate", "olivedrab", label="ATB power moderate scenario", dash=True)
add_range(atb_storage, "conservative", "advanced", "steelblue", label="ATB storage capacity cost range")
add_single_line(atb_storage, "moderate", "steelblue", label="ATB storage moderate scenario", dash=True)
ax.set_ylim([0, atb_power.max().max()*1.05])
ax.set_ylabel("projected capacity cost (€/kW(h))")

default_matplotlib_save(fig, "cost_lithium_absolute.png")



#%%

fig, ax = plt.subplots(figsize=(5, 3))
add_range(atb_storage, "conservative", "advanced", "#133B63", label="test")

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






ax.set_ylim([0, atb_storage.max().max()*1.05])
ax.set_ylabel("€/kWh", weight="bold", size=14, color='#133B63')
plt.rcParams.update(rc)
ax.get_legend().remove()

default_matplotlib_save(fig, "cost_lithium_absolute_presentation.png")