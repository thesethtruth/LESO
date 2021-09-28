from LESO.plotly_extension import lighten_color
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

def add_single_line(df, column, color, label=None, dash=False):
    ax.plot(
        column,
        data=df,
        marker='o',
        linestyle= '-' if not dash else '--',
        mfc=color,
        color=color,
        label=label if label != None else "_d",
        alpha=1,
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
    add_single_line(df, lower_col, color)
    add_single_line(df, upper_col, color)
    
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
ax.set_ylabel("capacity cost (€/MW(h))")

default_matplotlib_save(fig, "cost_lithium_absolute.png")




# ax.set_xlim([weekload.index[0], weekload.index[-1]])
# ax.set_ylim([0, 8])
# ax.set_ylabel("charging load (MW)")
# ticks = [weekload.index[i * 24 + 12] for i in range(7)]
# ax.set_xticks(ticks)
# ax.xaxis.set_major_formatter(myFmt)





# print(atb_storage)
# print(atb_power)

# storage_color = "#43709D" # Davos_4[1] from palettable.scientific.sequential
# power_color = '#99AD88' # Davos_4[2] from palettable.scientific.sequential
# if True:
#     fig = go.Figure()
#     fig.update_layout(template='simple_white')


#     fig.add_trace(go.Scatter(
#         x=list(atb_power.index) + list(atb_power.index)[::-1],
#         y=list(atb_power.Advanced) + list(atb_power.Conservative)[::-1],
#         fill='toself',
#         fillcolor=lighten_color(power_color, 0.3),
#         line_color= 'rgba(0,0,0,0)',
#         showlegend=True,
#         name='ATB power capacity cost range',    
#         opacity=1
#     ))
    
#     fig.add_trace(go.Scatter(
#         x=list(atb_storage.index) + list(atb_storage.index)[::-1],
#         y=list(atb_storage.Advanced) + list(atb_storage.Conservative)[::-1],
#         fill='toself',
#         fillcolor=lighten_color(storage_color, 0.3),
#         line_color= 'rgba(0,0,0,0)',
#         showlegend=True,
#         name='ATB storage capacity cost range',    
#         opacity=1
#     ))

#     for col in atb_storage.columns:
#         fig.add_trace(go.Scatter(
#             x=list(atb_storage.index), 
#             y=list(atb_storage[col]),
#             line_color=storage_color,
#             line_dash= 'dash' if 'Mod' in col else None,
#             mode='lines+markers',
#             name=f'ATB storage capacity {col} scenario',
#             showlegend = True if 'Mod' in col else False,
#             opacity=1
#         ))
#     for col in atb_power.columns:
#         fig.add_trace(go.Scatter(
#             x=list(atb_power.index), 
#             y=list(atb_power[col]),
#             line_color=power_color,
#             line_dash= 'dash' if 'Mod' in col else None,
#             mode='lines+markers',
#             name=f'ATB power capacity {col} scenario', 
#             showlegend = True if 'Mod' in col else False,
#             opacity=1
#         ))
#     # fig.update_traces(mode='lines')

#     fig.update_yaxes(title='projected cost factor', range=[0, 1])

#     from LESO.plotly_extension import thesis_default_styling
#     fig = thesis_default_styling(fig)
#     fig.update_layout(width=800)
    
#     if True:
#         fig.write_image("lithium.pdf")
#     else:
#         fig.show()