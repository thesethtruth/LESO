from LESO.plotly_extension import lighten_color
import pandas as pd
import numpy as np
import plotly.graph_objects as go


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
scenarios = ["Advanced", "Moderate", "Conservative"]
atb_storage = pd.DataFrame(storage_projection, index=years, columns=scenarios)
atb_power = pd.DataFrame(power_projection, index=years, columns=scenarios)
print(atb_storage)
print(atb_power)

storage_color = "#43709D" # Davos_4[1] from palettable.scientific.sequential
power_color = '#99AD88' # Davos_4[2] from palettable.scientific.sequential
if True:
    fig = go.Figure()
    fig.update_layout(template='simple_white')


    fig.add_trace(go.Scatter(
        x=list(atb_power.index) + list(atb_power.index)[::-1],
        y=list(atb_power.Advanced) + list(atb_power.Conservative)[::-1],
        fill='toself',
        fillcolor=lighten_color(power_color, 0.3),
        line_color= 'rgba(0,0,0,0)',
        showlegend=True,
        name='ATB power capacity cost range',    
        opacity=1
    ))
    
    fig.add_trace(go.Scatter(
        x=list(atb_storage.index) + list(atb_storage.index)[::-1],
        y=list(atb_storage.Advanced) + list(atb_storage.Conservative)[::-1],
        fill='toself',
        fillcolor=lighten_color(storage_color, 0.3),
        line_color= 'rgba(0,0,0,0)',
        showlegend=True,
        name='ATB storage capacity cost range',    
        opacity=1
    ))

    for col in atb_storage.columns:
        fig.add_trace(go.Scatter(
            x=list(atb_storage.index), 
            y=list(atb_storage[col]),
            line_color=storage_color,
            line_dash= 'dash' if 'Mod' in col else None,
            mode='lines+markers',
            name=f'ATB storage capacity {col} scenario',
            showlegend = True if 'Mod' in col else False,
            opacity=1
        ))
    for col in atb_power.columns:
        fig.add_trace(go.Scatter(
            x=list(atb_power.index), 
            y=list(atb_power[col]),
            line_color=power_color,
            line_dash= 'dash' if 'Mod' in col else None,
            mode='lines+markers',
            name=f'ATB power capacity {col} scenario', 
            showlegend = True if 'Mod' in col else False,
            opacity=1
        ))
    # fig.update_traces(mode='lines')

    fig.update_yaxes(title='projected cost factor', range=[0, 1])

    from LESO.plotly_extension import thesis_default_styling
    fig = thesis_default_styling(fig)
    fig.update_layout(width=800)
    
    if True:
        fig.write_image("lithium.pdf")
    else:
        fig.show()