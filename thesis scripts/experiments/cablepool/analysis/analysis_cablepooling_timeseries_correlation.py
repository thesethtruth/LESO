#%%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

#%%
def crosscorr(datax, datay, lag=0, wrap=False):
    """Lag-N cross correlation.
    Shifted data filled with NaNs

    Parameters
    ----------
    lag : int, default 0
    datax, datay : pandas.Series objects of equal length
    Returns
    ----------
    crosscorr : float
    """
    if wrap:
        shiftedy = datay.shift(lag)
        shiftedy.iloc[:lag] = datay.iloc[-lag:].values
        return datax.corr(shiftedy)
    else:
        return datax.corr(datay.shift(lag))

def WTLCC(
    df, key1, key2, window_size=48, fps=1, step_size=4, seconds=24
):

    t_start = 0
    t_end = t_start + window_size
    rss = []

    while t_end < 8760:
        d1 = df[key1].iloc[t_start:t_end]
        d2 = df[key2].iloc[t_start:t_end]
        rs = [
            crosscorr(d1, d2, lag, wrap=False)
            for lag in range(-int(seconds * fps), int(seconds * fps + 1))
        ]
        rss.append(rs)
        t_start = t_start + step_size
        t_end = t_end + step_size

    rss = pd.DataFrame(rss)
    return rss

#%%
from LESO.experiments.analysis import gcloud_read_experiment

exp = gcloud_read_experiment(
    "cablepooling",
    'cablepooling_exp_186498666738090.json'
)
epath = r"C:\Users\Sethv\#Universiteit Twente\GIT\LESO\thesis scripts\experiments\cablepool\model\cablepool_price_kea_40ch4_85co2.csv"
edf = pd.read_csv(epath)

pricevalues = edf["Price (Euros)"].values
windvalues = np.array(exp.components.wind1.state["power [+]"])/exp.components.wind1.settings.installed
pvvalues = np.array(exp.components.pv1.state["power [+]"])/exp.components.pv1.settings.installed


#%%
df = pd.DataFrame(
    data = np.vstack([
        windvalues,
        pvvalues,
        pricevalues
    ]).T,
    columns=['wind', 'pv', 'price']
)



#%%
rss = WTLCC(
    df, 
    "wind", 
    "pv",
    window_size=48,
    step_size=24,
    seconds=3)

f, ax = plt.subplots(figsize=(10, 10))
sns.heatmap(rss, cmap="RdBu_r", ax=ax)
ax.set(
    title=f"Rolling Windowed Time Lagged Cross Correlation",
    xlabel="Offset",
    ylabel="Epochs",
)
# ax.set_xticks([0, 50, 100, 151, 201, 251, 301])
# ax.set_xticklabels([-150, -100, -50, 0, 50, 100, 150])

# %%
