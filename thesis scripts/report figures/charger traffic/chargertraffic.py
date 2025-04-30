from LESO.plotting import default_matplotlib_save
import LESO
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path
import sys
from scipy.stats import truncexpon
from LESO import default_matplotlib_style


DATA_FOLDER = Path(r"C:\Users\Sethv\#Universiteit Twente\GIT\LESO\LESO\data")
# sys.path.append(DATA_FOLDER.absolute().__str__())

weekday = pd.read_csv(DATA_FOLDER / "weekday_deventer.csv")
weekendday = pd.read_csv(DATA_FOLDER / "weekendday_deventer.csv")

weekday = pd.Series(
    data=np.round(weekday.volume.values, 0), index=weekday.time, dtype="int"
)
weekendday = pd.Series(
    data=np.round(weekendday.volume.values, 0), index=weekendday.time, dtype="int"
)


def soc_trunc_filter(traffic, min_soc):
    socs = truncexpon.rvs(
        1, size=traffic
    )  # TODO random seed might be counter productive
    should_charge = len(socs[socs < min_soc])
    return should_charge


EV_share = 0.10
# mutliply by the EV share to
weekday_EV = (weekday * EV_share).round(0).astype("int")
weekendday_EV = (weekendday * EV_share).round(0).astype("int")

weekday = weekday - weekday_EV.values
weekendday = weekendday - weekendday_EV.values


def make_traffic_plot(x, y, labels, colors, show_legend=False, ymax=4200, alpha=0.8):
    fig, ax = plt.subplots()
    ax.stackplot(
        x,
        y,
        labels=labels,
        colors=colors,
        alpha=alpha,
    )
    if show_legend:
        ax.legend(loc="upper left", frameon=False)
    ax.set_xlim([x[0], x[-1]])
    ax.set_ylim([0, ymax])
    ax.set_ylabel("cars per hour")
    ticks = [weekday.index[i * 6 + 4] for i in range(4)]
    ax.set_xticks(ticks)
    return fig, ax


##  weekday EV shares
fig, ax = make_traffic_plot(
    x=weekday.index,
    y=[weekday.values, weekday_EV.values],
    labels=["Non-EV traffic", "EV traffic"],
    colors=["lightgrey", "firebrick"],
)

fig, ax = default_matplotlib_style(fig=fig, ax=ax, subplots=2)
default_matplotlib_save(fig, filename="weekday_deventer")

##  weekendday EV shares
fig, ax = make_traffic_plot(
    x=weekendday.index,
    y=[weekendday.values, weekendday_EV.values],
    labels=["Non-EV traffic", "EV traffic"],
    colors=["lightgrey", "firebrick"],
    show_legend=True,
)

fig, ax = default_matplotlib_style(fig=fig, ax=ax, subplots=2)
default_matplotlib_save(fig, filename="weekendday_deventer")

#%%

b = 1
fig, ax = plt.subplots()
x = np.linspace(truncexpon.ppf(0.001, b), truncexpon.ppf(0.999, b), 100)
rv = truncexpon(b)
ax.plot(x, rv.pdf(x), "crimson", lw=2)
r = truncexpon.rvs(b, size=10000)
ax.hist(
    r, density=True, histtype="stepfilled", alpha=0.8, bins=10, color=["powderblue"]
)
ax.legend(loc="best", frameon=False)
ax.set_xlim([x[0], x[-1]])
ax.set_ylabel("probability density")
ax.set_xlabel("state of charge")

fig, ax = default_matplotlib_style(fig=fig, ax=ax, subplots=2)
default_matplotlib_save(fig, filename="truncatedexponentialrvs")


minimal_charge = 0.4
# apply the filter
weekday_EV_charging = weekday_EV.apply(
    soc_trunc_filter,
    args=[minimal_charge],
)
weekendday_EV_charging = weekendday_EV.apply(
    soc_trunc_filter,
    args=[minimal_charge],
)
weekday_EV_s = weekday_EV - weekday_EV_charging
weekendday_EV_s = weekendday_EV - weekendday_EV_charging
##  weekendday EV shares
fig, ax = make_traffic_plot(
    x=weekday_EV_s.index,
    y=[weekday_EV_s.values, weekday_EV_charging.values],
    labels=["EVs moving past", "EVs charging"],
    colors=["coral", "firebrick"],
    show_legend=True,
    ymax=600,
    alpha=0.8,
)
fig, ax = default_matplotlib_style(fig=fig, ax=ax, subplots=2)
default_matplotlib_save(fig, filename="weekday_charging")

# %%
weekday_EV_charging_l = []
for i in range(5):
    day = weekday_EV.apply(
            soc_trunc_filter,
            args=[minimal_charge],
        )
    weekday_EV_charging_l.append(
        day
    )
weekendday_EV_charging_l = []
for i in range(2):
    day = weekendday_EV.apply(
            soc_trunc_filter,
            args=[minimal_charge],
        )
    weekendday_EV_charging_l.append(
        day
    )


weekcharge = pd.DataFrame(
    data=np.hstack([*[df.values for df in weekday_EV_charging_l], *[df.values for df in weekendday_EV_charging_l]]),
    index=pd.date_range(
        start="27/09/2021", periods=24*7, freq='h'
    )
)

weekload = weekcharge*25/0.85/1000
# %%
import matplotlib.dates as mdates
myFmt = mdates.DateFormatter('%A')

fig, ax = plt.subplots()
ax.plot(
    weekload.index,
    weekload.values,
    color='firebrick',
    alpha=0.6,
)
ax.fill_between(
    x=weekload.index,
    y1=weekload.values.flatten(),
    color='firebrick',
    alpha=0.2,
)

ax.set_xlim([weekload.index[0], weekload.index[-1]])
ax.set_ylim([0, 8])
ax.set_ylabel("charging load (MW)")
ticks = [weekload.index[i * 24 + 12] for i in range(7)]
ax.set_xticks(ticks)
ax.xaxis.set_major_formatter(myFmt)

fig, ax = default_matplotlib_style(fig, ax, height=2)
default_matplotlib_save(fig, filename="chargingDemandCurve")



# %%