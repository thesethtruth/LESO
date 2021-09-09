import glob
import os
import numpy as np
import pandas as pd
import seaborn as sns
import plotly.graph_objects as go
import json
from LESO.attrdict import AttrDict
from durationcurves import plot_duration_curve


################################################
##              function def                  ##
################################################


def kotzur_normalize(array):
    """
    Normalizes an array as proposed in DOI: 10.1016/j.renene.2017.10.017
        $$
        \mathrm{x}_{a, t}=\frac{\mathrm{x}_{a, t}^{\prime}-\min \mathrm{x}_{a}^{\prime}}{\max \mathrm{x}_{a}^{\prime}-\min \mathrm{x}_{a}^{\prime}} \quad \forall \quad a \in\left\{1, \ldots, N_{a}\right\}, \forall \quad t \in\left\{1, \ldots, N_{t}\right\}
        $$

    Input:
        array: np.array of times series

    Returns
        n_array: np.array of normalized time series (will be *absolute*)
    """

    array = np.abs(array)
    max_a = np.max(array)
    min_a = np.min(array)

    def norm(x):
        nx = (x - min_a) / (max_a - min_a)
        return nx

    vnorm = np.vectorize(norm)
    n_array = vnorm(array)

    return n_array

#================================================

def extract_component_timeseries(
    filepaths: list, names: list, comp_str="ETMdemand", col_str=None, all_comps=False
):
    """
    Extract simulation/optimization timeseries results for further processing.
    Inputs:
        filepaths: list of filepaths to LESO.json files
        names: list of desired name labels
        comp_str: str to match with components (equal to hardcoded str in comp.__str__)
            e.g. 'pv', 'wind', 'ETMdemand', 'lithium', 'hydrogen', 'grid', etc
        col_str: str (exact!) in accordance with LESO.component.state.columns
            e.g. 'power [+]', 'power [-]', 'energy'
    Returns:
        timeseries: AttrDict
    """

    timeseries = AttrDict()
    matched_names, components, curves = [], [], []

    force_list = lambda object : [object] if not isinstance(object, list) else object

    force_list(filepaths), force_list(names)
    for name, filepath in zip(names, filepaths):

        with open(filepath) as infile:
            d = AttrDict(json.load(infile))
        
        keys = list(d.components.keys())

        match_indices = [i for i, name in enumerate(keys) if comp_str in name]
        match_keys = [keys[mi] for mi in match_indices]

        force_list(match_keys)
        if match_keys:
            matched_names.append(name)
            tcurves = np.zeros((1, 8760))
            for key in match_keys:
                
                component = d.components[key]
                
                if col_str is None:
                    col_str =  'power [+]'

                tcurves += np.array(component.state[col_str])

            curves.append(tcurves)
          
        timeseries.update({
            'component': comp_str,
            'names': matched_names, 
            'curves': curves
        })

    return timeseries

#================================================

def curve_to_heatmap(curve, normalize=False, absolute=True, colorscale='Viridis', start=None):
    
    days = int(len(curve)/24)
    
    if start is None:
        if days > 365:
            start = '01/01/2020'
        else:
            start = '01/01/2021'
        
    
    if absolute:
        curve = np.abs(curve)
    
    matrix = curve.reshape(days, 24).transpose()
    
    if normalize:   
        matrix = kotzur_normalize(matrix)
    times = ["{:02d}:00".format(i) for i in [k+1 for k in range(24)]]
    
    days_months = pd.date_range(start, periods=days, freq='d')
    heatmap = go.Heatmap(
        z=matrix,
        x=days_months,
        y=times,
        colorscale=colorscale
    )

    return heatmap

#================================================

def make_duration_curve(
    filepaths,
    names,
    unit="MW",
    normalize=False,
    comp_str="ETMdemand",
    col_str=None,
):

    timeseries = extract_component_timeseries(
        filepaths, names, comp_str=comp_str, col_str=col_str
    )
    if timeseries is not None:
        scatter = plot_duration_curve(timeseries=timeseries, normalize=normalize)

    fig = go.Figure()
    fig.update_layout(
    template="simple_white",
    legend=dict(bordercolor="#e8e8e8", borderwidth=1),
    )
    fig.update_xaxes(title_text="<b>Cumulative duration</b>", tickformat="%")

    if normalize:
        fig.update_yaxes(title_text="<b>Normalized power</b>", nticks=5)
    else:
        fig.update_yaxes(title_text="<b>Power</b>", ticksuffix=" MW", nticks=5)

    return fig


################################################
##              defs and calls                ##
################################################


wd = os.getcwd()
filepaths = glob.glob(wd + "/results/2030*.json")
prenames = [os.path.split(filepath)[-1] for filepath in filepaths]
names = [prename.replace(".json", "").replace("2030RES_", "") for prename in prenames]

fp = filepaths[0]
name = names[0]


wl = [
    "pv",
    "wind",
    "ETMdemand",
    "grid",
]

normalize = False
component = 'ETMdemand'
col_str = 'power [-]'

timeseries = extract_component_timeseries(
    filepaths=filepaths,
    names=names,
    comp_str=component,
    col_str=col_str
)

# hm = curve_to_heatmap(timeseries.curves[0], normalize=True)
# go.Figure(data=hm)






# import plotly.io as pio

# if normalize:
#     pio.write_image(
#         fig, f"images/2030_RES_cumdist_{component}_norm.svg", engine="kaleido"
#     )
# else:
#     pio.write_image(
#         fig, f"images/2030_RES_cumdist_{component}.svg", engine="kaleido"
#     )

# fig.show()

# from plotly.subplots import make_subplots
# import plotly.graph_objects as go

# fig = make_subplots(rows=1, cols=2)