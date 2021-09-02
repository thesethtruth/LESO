#%%

## Import relevant packages
from numpy import compat
import pandas as pd
from LESO import System
from LESO import PhotoVoltaic, Wind
import seaborn as sns
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import tsam.timeseriesaggregation as tsam
import numpy as np
from scipy.stats import kde
from durationcurves import kotzur_normalize
from scipy.signal import savgol_filter
import LESO.plotly_extension as pe

modelname = "ETM Noord-Veluwe trial 1"
lat, lon = 52.4, 5.8
system = System(lat, lon, model_name=modelname)
wind = Wind("Onshore turbine", lat=lat, lon=lon, installed=1, use_dowa=False)
pv = PhotoVoltaic("PV Full south", installed=1)

system.add_components([wind, pv])
system.fetch_input_data()
system.calculate_time_series()

source = "PVGIS-SARAH ERA-Interim 2005-2016 TMY"
#%% aggregation
raw = pd.DataFrame([wind.state.power, pv.state.power], index=["Wind", "PV"]).transpose()

aggregation = tsam.TimeSeriesAggregation(
    raw,
    noTypicalPeriods=8,
    hoursPerPeriod=24,
    clusterMethod="hierarchical",
    solver="gurobi",
)

typPeriods_c = aggregation.createTypicalPeriods()
accuracy = aggregation.accuracyIndicators()

low_to_high = typPeriods_c.groupby(level=0).mean().sum(axis=1).sort_values().index
low_to_high_map = {k: i for i, k in enumerate(low_to_high)}
low_to_high_get = lambda x: low_to_high_map.get(x)

raw["cluster"] = raw.apply(
    lambda row: low_to_high_get(aggregation.clusterOrder[row.name.dayofyear - 1]), axis=1
)

centers = [i+1 for i in aggregation.clusterCenterIndices]
center_order = [low_to_high_get(idx) for idx in aggregation.clusterPeriodIdx]
sorted_centers =  [x for _,x in sorted(zip(center_order, centers))]


mediod_idx = np.array([raw.index.dayofyear == center for center in sorted_centers]).any(axis=0)

typPeriods_m = raw[['PV', 'Wind','cluster']][mediod_idx]
typPeriods_m['index'] = np.arange(len(typPeriods_m))
typPeriods_m.sort_values(['cluster','index'],inplace=True, axis=0)
typPeriods_m.index = np.arange(len(typPeriods_m))
typPeriods_m.drop('index', inplace=True, axis=1)

#%% compare that shit

compare_that_shit = False
if compare_that_shit:
    fig = go.Figure()

    pp = [typPeriods_m.PV, typPeriods_c.PV, typPeriods_m.Wind, typPeriods_c.Wind]
    names = ['Medoid PV', 'Centroid PV', 'Medoid wind', 'Centroid Wind']

    for i, y in enumerate(pp):
        fig.add_trace(go.Scatter(
            x=typPeriods_m.index,
            y=y.values,
            name=names[i],
            mode='lines+markers'
        ))

    fig.add_trace(go.Scatter(
            x=typPeriods_m.index,
            y=kotzur_normalize(pp[0].values),
            name='normalized PV mediod',
            mode='lines+markers'
        ))
    fig.add_trace(go.Scatter(
            x=typPeriods_m.index,
            y=kotzur_normalize(pp[2].values),
            name='normalized Wind mediod',
            mode='lines+markers'
        ))


    fig.show()

typPeriods_m.index = typPeriods_c.index
typPeriods_m.drop('cluster', inplace=True, axis=1)


#%% cluster plots

yeardays = raw.groupby(raw.index.dayofyear).mean()
typDays_m = yeardays.loc[sorted_centers,:].sort_values('cluster')
weights = aggregation.clusterPeriodNoOccur
weights = {low_to_high_get(key): value for key, value in weights.items()}
yeardays["cluster_str"] = [
    f"Cluster {i+1} ({weights[i]} days)" for i in yeardays["cluster"].values
]

colors = sns.color_palette("viridis", n_colors=len(typDays_m)).as_hex()

fig = go.Figure()

for i, df in yeardays.groupby("cluster"):
    ## All days scatter
    c = df.cluster.values[0]
    fig.add_trace(
        go.Scatter(
            x=df.PV,
            y=df.Wind,
            mode="markers",
            name= df.cluster_str.values[0],
            marker=dict(size=10, color=colors[c], opacity=0.7),
            hovertemplate=("CF PV: %{x:.0%}<br>" + "CF Wind: %{y:.0%}<br>"),
        )
    )

## Mediod scatter
fig.add_trace(
    go.Scatter(
        x=typDays_m.PV,
        y=typDays_m.Wind,
        mode="markers",
        name="Cluster mediods",
        marker=dict(
            size=20, 
            color='rgba(0,0,0,0)', 
            opacity=1,
            line=dict(
                color='gray',
                width=3,
            )
            ),
        hovertemplate=(
            "<b>Cluster mediod</b><br>"+
            "CF PV: %{x:.0%}<br>" + 
            "CF Wind: %{y:.0%}<br>"+
            "<extra></extra>"),
        showlegend=True,
    )
)

fig.update_xaxes(
    title_text="<b>Capacity factor of PV</b>",
    tickformat="%",
    range=[-0.01, yeardays.PV.max() * 1.1],
)
fig.update_yaxes(
    title_text="<b>Capacity factor of wind</b>",
    tickformat="%",
    range=[-0.03, yeardays.Wind.max() * 1.1],
)
fig.update_layout(
    height=600,
    width=800,
    template="simple_white",
    title=dict(
        text="<b>Wind and solar capacity factor based on hierarchical clusters</b><br>(daily means)",
        xanchor="center",
        x=0.5,
    ),
    margin=dict(l=20, r=20, t=50, b=200),
    legend=dict(bordercolor="#e8e8e8", borderwidth=1, orientation="h", y=-0.2),
)

filename = "capacity-factor-scatter.html"
pe.add_author_source(fig, source=source)
fig.write_html(filename, auto_open=False, config={"displayModeBar": False})
pe.add_centering_to_plotly_html(filename)
pe.add_title_to_plotly_html(filename, "VRE clusters")
pe.open_html(filename)

#%% Typical days
fig = make_subplots(2, 1, shared_xaxes=True, horizontal_spacing=0.3)
wind_color, PV_color = "#8cc0ed", "#ebd25b"

clusters = aggregation.clusterPeriodIdx
visible = True


def toggle_visibility(idx):

    vis = []
    for c in clusters:
        lc = weights[c] * 2 + 2
        if c == idx:
            vis.extend([True] * lc)
        else:
            vis.extend([False] * lc)

    return vis


for i in clusters:

    curves_in_cluster = raw[raw.cluster == i]
    cluster_medoid = typPeriods_m.loc[i, :, :]
    first_legend = True
    for day, df in curves_in_cluster.groupby(curves_in_cluster.index.dayofyear):

        dic = weights[i]  # days in cluster

        ## PV scatter
        fig.add_trace(
            go.Scatter(
                x=pd.date_range(start="01/01/21", freq="h", periods=24),
                y=df.PV,
                mode="lines",
                line_color=PV_color,
                line_width=3,
                opacity=0.3,
                visible=visible,
                name=f"{dic} PV curves in cluster {i+1}",
                legendgroup=f"{dic} PV curves in cluster {i+1}",
                hoverinfo="none",
                showlegend=first_legend,
            ),
            1,
            1,
        )

        ## Wind scatter
        fig.add_trace(
            go.Scatter(
                x=pd.date_range(start="01/01/21", freq="h", periods=24),
                y=df.Wind,
                mode="lines",
                line_color=wind_color,
                line_width=3,
                opacity=0.3,
                visible=visible,
                name=f"{dic} wind curves in cluster {i+1}",
                legendgroup=f"Wind: {dic} days in cluster {i+1}",
                hoverinfo="none",
                showlegend=first_legend,
            ),
            2,
            1,
        )

        # disable legend if second time around
        first_legend = False

    ## PV medoid
    fig.add_trace(
        go.Scatter(
            x=pd.date_range(start="01/01/21", freq="h", periods=24),
            y=cluster_medoid.PV,
            mode="lines",
            line_color="gray",
            line_width=3,
            opacity=1,
            name=f"Medoids cluster {i+1}",
            visible=visible,
            hovertemplate=(
                f"<b>Medoid curve cluster {i+1}<b><br>"
                "Share of PV: %{y:.0%}<br>" + "Time of the day: %{x}<br>"
                # "<extra></extra>",
            ),
        ),
        1,
        1,
    )

    ## Wind medoid
    fig.add_trace(
        go.Scatter(
            x=pd.date_range(start="01/01/21", freq="h", periods=24),
            y=cluster_medoid.Wind,
            mode="lines",
            line_color="gray",
            line_width=3,
            opacity=1,
            visible=visible,
            showlegend=False,
            hovertemplate=(
                f"<b>Medoid curve cluster {i+1}<b><br>"
                "Share of PV: %{y:.0%}<br>" + "Time of the day: %{x}<br>"
                # "<extra></extra>",
            ),
        ),
        2,
        1,
    )

    # set visibility to false after first itteration
    visible = False

fig.update_layout(
    template="simple_white",
    legend=dict(bordercolor="#e8e8e8", borderwidth=1),
    title_text="<b>Mediod (reprensentative) curves of clusters and curves within clusters</b>",
    showlegend=True,
    legend_traceorder="reversed",
    margin=dict(l=20, r=20, t=50, b=120),
    height=600,
    width=1200,
    updatemenus=[
        dict(
            active=0,
            visible=True,
            xanchor="right",
            x=1,
            buttons=[
                {
                    "label": f"Cluster {i+1}",
                    "method": "update",
                    "args": [{"visible": toggle_visibility(i)}],
                }
                for i in clusters
            ],
        )
    ],
)

fig.update_xaxes(
    title_text="<b>Time of the day</b>", nticks=6, tickformat="%H:00", row=2, col=1
)

## PV y-axes
fig.update_yaxes(
    title_text="<b>CF solar PV</b>",
    nticks=3,
    range=[0, 1],
    tickformat="%",
    row=1,
    col=1,
)

## Wind x-axes
fig.update_yaxes(
    title_text="<b>CF wind</b>", nticks=3, range=[0, 1], tickformat="%", row=2, col=1
)

filename = "typical-days.html"
pe.add_author_source(fig, source=source, y=[-.2, -.15])
fig.write_html(filename, auto_open=False, config={"displayModeBar": False})
pe.add_centering_to_plotly_html(filename)
pe.add_title_to_plotly_html(filename, "Typical days")
pe.open_html(filename)
#%% 
hm = yeardays.copy(deep=True)
hm.index = pd.date_range('01/01/2021', freq='d', periods=365)
hm['cluster'] = hm['cluster']+1

fig = go.Figure(
    data=   go.Heatmap(
        x=hm.index,
        z=hm.cluster.values.reshape(1, -1),           
        colorscale=colors,
        showscale=False,
        hovertemplate=(
            "Day of the year: %{x} <br>"+
            "<b>Typical day: %{z:.0f}<b><br>"+
            "<extra></extra>"
        ),
    )
 
)

for i in clusters:
    fig.add_trace(
        go.Scatter(
            x=[1],
            y=[0],
            mode='markers',
            marker_symbol='square',
            name=f'Typical day {i+1}',
            marker_color=colors[i],
            marker_size=20,
        )
    )

fig.update_xaxes(
    title_text="<b>Day of the year</b>",
    tickformat="%-j",
    range=[hm.index.min(), hm.index.max()],
)

fig.update_yaxes(
    title_text="<b>Typical day</b>",
    showticklabels=False,
    tickwidth=0,
    tickcolor='rgba(0,0,0,0)'
)

fig.update_layout(
    height=400,
    width=1200,
    template="simple_white",
    title=dict(
        text=f"<b>Reconstructed typical meteorological year using {len(typDays_m)} typical days</b><br>",
        xanchor="center",
        x=0.5,
    ),
    margin=dict(l=20, r=20, t=50, b=150),
    legend=dict(bordercolor="#e8e8e8", borderwidth=1, orientation="h", y=-0.3, x=0.5, xanchor="center"),
)





filename = "typical-days-year.html"
pe.add_author_source(fig, source=source, y=[-.55, -.5])
fig.write_html(filename, auto_open=False, config={"displayModeBar": False})
pe.add_centering_to_plotly_html(filename)
pe.add_title_to_plotly_html(filename, "TPD year overview")
pe.open_html(filename)

#%% 
from collections import Counter as counter

s_days = 6

labels = []

co = aggregation.clusterOrder






# %% scatter cluster with contours
contour = False
if contour:
    yeardays = raw.groupby(raw.index.dayofyear).mean()
    weights = aggregation.clusterPeriodNoOccur
    yeardays["cluster_str"] = [
        f"Cluster {i+1} ({weights[i]} days)" for i in yeardays["cluster"].values
    ]
    nbins = 100

    fig = go.Figure()
    c = sns.color_palette("cubehelix", n_colors=len(typPeriods_m.loc[:, 1, :]))

    for i, (cluster, df) in enumerate(yeardays.groupby("cluster_str")):

        x = df.PV.values
        y = df.Wind.values
        k = kde.gaussian_kde([x, y])
        xi, yi = np.mgrid[x.min() : x.max() : nbins * 1j, y.min() : y.max() : nbins * 1j]
        zi = k(np.vstack([xi.flatten(), yi.flatten()]))
        xc = np.linspace(x.min(), x.max(), nbins)
        yc = np.linspace(y.min(), y.max(), nbins)

        colorscale = [
            [0, "rgba(0,0,0,0)"],
            [0.5, f"rgba{c[i][0], c[i][1], c[i][2], 0}"],
            [1, colors[i]],
        ]
        fig.add_trace(
            go.Contour(
                x=xc,
                y=yc,
                z=zi.reshape(xi.shape),
                colorscale=colorscale,
                line_width=0,
                hoverinfo="none",
                showlegend=False,
                showscale=False,
            )
        )

        fig.add_trace(
            go.Scatter(
                x=df.PV,
                y=df.Wind,
                mode="markers",
                name=cluster,
                marker=dict(size=10, color=colors[i], opacity=0.7),
                hovertemplate=("CF PV: %{x:.0%}<br>" + "CF Wind: %{y:.0%}<br>"),
            )
        )

    fig.update_xaxes(
        title_text="<b>Capacity factor of PV</b>",
        tickformat="%",
        range=[-0.01, yeardays.PV.max() * 1.1],
    )
    fig.update_yaxes(
        title_text="<b>Capacity factor of wind</b>",
        tickformat="%",
        range=[-0.03, yeardays.Wind.max() * 1.1],
    )
    fig.update_layout(
        height=600,
        width=800,
        template="simple_white",
        title=dict(
            text="<b>Wind and solar capacity factor based on hierarchical clusters</b><br>(daily means)",
            xanchor="center",
            x=0.5,
        ),
        margin=dict(l=20, r=20, t=50, b=120),
        legend=dict(bordercolor="#e8e8e8", borderwidth=1, orientation="h", y=-0.2),
    )
    filename = "dutch-CF-contours.html"
    fig.write_html(filename, auto_open=False, config={"displayModeBar": False})
    pe.add_centering_to_plotly_html(filename)
    pe.add_title_to_plotly_html(filename, "VRE clusters contours")
    pe.open_html(filename)