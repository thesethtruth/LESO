import pandas as pd
import numpy as np
from curveheatmap import curve_to_heatmap
import plotly.graph_objects as go
from ets_price_reader import ets_prices_reader

force_list = lambda object: [object] if not isinstance(object, list) else object

filenames = ["2019", "2020", "2021"]
df19, df20, df21 = ets_prices_reader(*filenames)
frames = [df19, df20, df21]


def extract_arrays(dfs, col_strs="NL.1"):

    dfs = force_list(dfs)

    col_strs = force_list(col_strs)
    if len(col_strs) != len(dfs) and len(col_strs) == 1:
        col_strs = col_strs * len(dfs)

    arrays = list()
    for i, df in enumerate(dfs):

        col = col_strs[i]

        a = (
            df[col]
            .fillna(0)
            .apply(lambda x: x.replace(",", ".") if isinstance(x, str) else x)
            .astype(float)
            .values
        )
        sec_col = col + ".1"
        if sec_col in df.columns:
            a1 = (
                df[sec_col]
                .fillna(0)
                .apply(lambda x: x.replace(",", ".") if isinstance(x, str) else x)
                .astype(float)
                .values
            )
        else:
            a1 = 0

        if df.index.year[0] != 2021:
            array = (a + a1)[:-1]  # exclude end of year point
        else:
            array = a + a1
        arrays.append(array)

    return arrays


arrays = extract_arrays(frames, col_strs="NL")


def stack_arrays(arrays, reshape=True, filter_zeros=True):
    iray = np.hstack(arrays)
    rray = iray.reshape(-1, 24)
    sray = rray.sum(axis=1)
    bray = sray != 0 if filter_zeros else np.ones(np.shape(sray))
    stacked_array = rray[bray] if reshape else rray[bray].flatten()
    return stacked_array
#%%
scale = 'rdbu_r'
one_array = stack_arrays(arrays, reshape=False)
start = "2019-07-04"

hm = curve_to_heatmap(one_array, colorscale=scale, start=start)
mean = round(np.mean(one_array), 0)

hm.zmin = -mean
hm.zmax = 3 * mean
hm.zmid = mean
hm.colorbar = dict(
    tick0=0,
    tickmode="array",
    tickvals=[i * mean for i in [-1, 0, 1, 2, 3]],
    ticksuffix=" €/MWh",
    outlinewidth=0,
)
months = round(len(set([x.strftime("%B%y") for x in hm.x])) / 2)
hm.hovertemplate = (
        "Spot price: €%{z:.2f}<br>" +
        "Time of the day: %{y}<br>" +
        "Month and year: %{x}" +
        "<extra></extra>"
)

#%%
fig = go.Figure(data=hm)

fig.add_annotation(x=pd.to_datetime("2020"), y="24:00", showarrow=True, text="2020")
fig.add_trace(
    go.Scatter(
        x=[pd.to_datetime("2020"), pd.to_datetime("2020")],
        y=["24:00", "01:00"],
        mode="lines",
        line_color="black",
        line_width=1

    )
)
fig.add_annotation(x=pd.to_datetime("2021"), y="24:00", showarrow=True, text="2021")
fig.add_trace(
    go.Scatter(
        x=[pd.to_datetime("2021"), pd.to_datetime("2021"), pd.to_datetime("2021")],
        y=["24:00", "01:00"],
        mode="lines",
        line_color="black",
        line_width=1
    )
)
fig.add_annotation(text="Seth van Wieringen",
                xref="paper", yref="paper",
                yanchor='bottom', xanchor='left',
                x=0, y=-0.45, showarrow=False)
fig.add_annotation(text="Source:",
                xref="paper", yref="paper",
                yanchor='bottom', xanchor='right',
                x=1, y=-0.4, showarrow=False)
fig.add_annotation(text="https://www.nordpoolgroup.com/historical-market-data/",
                xref="paper", yref="paper",
                yanchor='bottom', xanchor='right',
                font_size=10,
                x=1, y=-0.45, showarrow=False)


fig.update_yaxes(
    title_text="<b>Time of the day</b>",
    nticks=5,
    ticks="outside",
    tickwidth=2,
    tickcolor="grey",
    ticklen=7,
    range=[0, 23],
    tick0=0.5,
    fixedrange=True
)
fig.update_xaxes(
    title_text="<b>Day of the year</b>",
    tickformat="%B '%y",
    nticks=months,
    ticks="outside",
    tickwidth=2,
    tickcolor="grey",
    ticklen=7,
    tickangle=90,
)
fig.update_layout(
    template="simple_white",
    title=dict(
        text="<b>Historic Market Data Spot Prices </b> \n Netherlands (2019 - 2021)",
        xanchor="center",
        yanchor="top",
        x=0.5,
        y=0.9,
        font_family="Poppins",
    ),
    margin=dict(l=20, r=20, t=120, b=120),
    showlegend=False,
    width=int(1200),
    height=int(500)
)
filename = 'spot-prices.html'
fig.write_html(filename, auto_open=False, config = {'displayModeBar': False})
from LESO.plotly_extension import add_centering_to_plotly_html, add_title_to_plotly_html, open_html
add_centering_to_plotly_html(filename)
add_title_to_plotly_html(filename, 'ETS spot prices')
open_html(filename)



