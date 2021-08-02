import glob
import os
import numpy as np
import pandas as pd
import seaborn as sns
import plotly.graph_objects as go
import json


wd = os.getcwd()
filepaths = glob.glob(wd + "/results/2030*.json")
prenames = [os.path.split(filepath)[-1] for filepath in filepaths]
names = [prename.replace(".json", "").replace("2030RES_", "") for prename in prenames]


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


def extract_simulation_data_duration_curve(
    filepaths: list, names: list, comp_str="ETMdemand", col_str=None
):
    """
    Extract simulation/optimization data results for duration curves.
    Inputs:
        filepaths: list of filepaths to LESO.json files
        names: list of desired name labels
        comp_str: str to match with components (equal to hardcoded str in comp.__str__)
            e.g. 'pv', 'wind', 'ETMdemand', 'lithium', 'hydrogen', 'grid', etc
        col_str: str (exact!) in accordance with component.state.columns
            e.g. 'power [+]', 'power [-]', 'energy'
    Returns:
        fig_data: dict containing
            'data': np.array of *absolute* timeseries
            'colors': list of component colors
            'names': list of supplied names
    """
    styler = {"power [+]": 0, "power [-]": 1, "energy": 2}
    grouper = {"power": "power [+]", "load": "power [-]", "energy": "energy"}
    data, colors = [], []

    for filepath in filepaths:

        with open(filepath) as infile:
            d = json.load(infile)
        keys = list(d["components"].keys())

        match_indices = [i for i, name in enumerate(keys) if comp_str in name]
        match_keys = [keys[mi] for mi in match_indices]

        if not isinstance(match_keys, list):
            match_keys = [match_keys]

        if not match_keys:
            return None

        for key in match_keys:

            component = d["components"][key]
            if col_str is None:
                col_str = grouper(
                    component["styling"][styler.get(col_str)]["group"]
                    if isinstance(component["styling"], list)
                    else component["styling"]["group"]
                )
            data.append(np.abs(np.array(component["state"][col_str])))
            colors.append(
                component["styling"][styler.get(col_str)]["color"]
                if isinstance(component["styling"], list)
                else component["styling"]["color"]
            )

    fig_data = {"data": data, "names": names, "colors": colors}

    return fig_data


def plot_duration_curve(data, names, colors, unit, normalize=False):

    fig = go.Figure()

    if not isinstance(data, list):
        data = [data]

    colors = sns.color_palette("cubehelix", n_colors=len(data)).as_hex()

    for i, d in enumerate(data):

        magnitude = np.sort(d)[::-1]
        percentile = np.arange(1.0, len(magnitude) + 1) / len(magnitude)
        if normalize:
            magnitude = kotzur_normalize(magnitude)

        fig.add_trace(
            go.Scatter(
                x=percentile,
                y=magnitude,
                line_smoothing=1.3,
                line_color=colors[i],
                name=names[i],
                opacity=0.8,
            )
        )

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


def make_duration_curve(
    filepaths,
    names,
    unit="MW",
    normalize=False,
    comp_str="ETMdemand",
    col_str=None,
):

    fig_data = extract_simulation_data_duration_curve(
        filepaths, names, comp_str=comp_str, col_str=col_str
    )
    if fig_data is not None:
        fig = plot_duration_curve(**fig_data, unit=unit, normalize=normalize)

    return fig


wl = [
    "pv",
    "wind",
    "ETMdemand",
    "lithium",
    "hydrogen",
    "grid",
    "Balance",
    "pva",
    "pv-bi",
    "windoffshore",
    "fastcharger",
    "consumer",
]

normalize = False
component = 'hydrogen'
col_str = 'power [+]'

fig = make_duration_curve(
    filepaths=filepaths,
    names=names,
    unit="MW",
    normalize=normalize,
    comp_str=component,
    col_str=col_str
)

import plotly.io as pio

if normalize:
    pio.write_image(
        fig, f"images/2030_RES_cumdist_{component}_norm.svg", engine="kaleido"
    )
else:
    pio.write_image(
        fig, f"images/2030_RES_cumdist_{component}.svg", engine="kaleido"
    )

fig.show()

from plotly.subplots import make_subplots
import plotly.graph_objects as go

fig = make_subplots(rows=1, cols=2)