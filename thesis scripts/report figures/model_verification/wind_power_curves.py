from LESO.plotting import default_matplotlib_save, default_matplotlib_style
import pandas as pd
import matplotlib.pyplot as plt


## Use once!
# df  = pd.read_clipboard()
# df = df.T
# df.index = [float(i) for i in df.index]
# df.columns =["Vestas V90/2000", "Enercon E-126/4200"]
# df.to_pickle("wind_power.pkl")


#%%
rc = {
    'font.family':'Open Sans',
    'font.size' : 10,
    'legend.fontsize' : 8
    }
plt.rcParams.update(rc)
PAD = 0.3



#%%
from LESO.plotting import olivedrab_05, steelblue_05, olivedrab_02, firebrick_02, firebrick_05

power = pd.read_pickle("wind_power.pkl")
cp = pd.read_pickle("wind_coeff.pkl")
turbines =["Vestas V90/2000", "Enercon E-126/4200"]
def plot_power_curve(power_series, cp_series, alt_color=False):

    fig, ax = plt.subplots(figsize=(3,2))
    plt.tight_layout(pad=PAD)

    power_series = power_series[~pd.isna(power_series)]
    cp_series = cp_series[~pd.isna(cp_series)]

    ax2=ax.twinx()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax2.spines['top'].set_visible(False)
    ax2.spines['left'].set_visible(False)

    if alt_color:
        light_color = firebrick_02
        dark_color = firebrick_05
    else:
        light_color = olivedrab_02
        dark_color = olivedrab_05
    
    ax.fill_between(
        power_series.index,
        power_series/1000,
        color=light_color,
    )
    ax.plot(
        power_series.index,
        power_series/1000,
        color = dark_color,
        linewidth=1,
    )
    ax.spines['left'].set_color(dark_color)
    ax.tick_params(axis='y', colors=dark_color)
    ax.yaxis.label.set_color(dark_color)


    ax2.plot(
        cp_series,
        color = steelblue_05,
        linewidth=1.5,
        linestyle='dashed'
    )

    ax2.spines['right'].set_color(steelblue_05)
    ax2.tick_params(axis='y', colors=steelblue_05)
    ax2.yaxis.label.set_color(steelblue_05)
    ax2.set_ylabel("$C_p$ [-]")
    ax.set_ylabel("power output [kW]")
    ax.set_xlabel(r"wind speed $[\frac{m}{s}]$")
    
    return ax, ax2

ax, ax2 = plot_power_curve(power[turbines[0]], cp[turbines[0]])
ax.set_xlim([2, 16])
ax.set_ylim([0, 2100])
ax2.set_ylim([0, 0.5])
default_matplotlib_save(ax, "wind_vestas_power.png")


ax, ax2 = plot_power_curve(power[turbines[1]], cp[turbines[1]], alt_color=True)
ax.set_xlim([2, 25])
ax.set_ylim([0, 4400])
ax2.set_ylim([0, 0.5])

default_matplotlib_save(ax, "wind_enercon_power.png")






# %%
