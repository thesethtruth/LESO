import pandas as pd
import numpy as np
from curveheatmap import curve_to_heatmap
import plotly.graph_objects as go
from ets_price_reader import ets_prices_reader

force_list = lambda object : [object] if not isinstance(object, list) else object

filenames = ['2019', '2020', '2021']
df19, df20, df21 = ets_prices_reader(*filenames)
frames = [df19, df20, df21]

def extract_arrays(dfs, col_strs='NL.1'):
    
    dfs = force_list(dfs)
    
    col_strs = force_list(col_strs)
    if len(col_strs) != len(dfs) and len(col_strs)==1:
        col_strs = col_strs*len(dfs)
    
    arrays = list()
    for i, df in enumerate(dfs):
            
            col = col_strs[i]
            
            a = (df[col].fillna(0)
                .apply(lambda x: x.replace(",",".") if isinstance(x, str) else x)
                .astype(float)
                .values
            )
            sec_col = col+'.1'
            if sec_col in df.columns:
                a1 = (df[sec_col].fillna(0)
                    .apply(lambda x: x.replace(",",".") if isinstance(x, str) else x)
                    .astype(float)
                    .values
                )
            else:
                a1 = 0

            if df.index.year[0] != 2021:
                array = (a+a1)[:-1] # exclude end of year point
            else:
                array = (a+a1)
            arrays.append(array)

    return arrays

arrays = extract_arrays(frames, col_strs='NL')
a19, a20, a21 = arrays

mean = np.mean([np.mean(array) for array in arrays])
for i, array in enumerate(arrays):
    hm = curve_to_heatmap(array, normalize=False, absolute=False, colorscale='oxy')
    hm.zmin = -2*mean
    hm.zmax = 3*mean
    hm.zmid = mean
    fig = go.Figure(data=hm)

    fig.update_yaxes(title_text="<b>Time of the day</b>", nticks=5)
    fig.update_xaxes(title_text="<b>Day of the year</b>", tickformat="%B")
    fig.update_layout(title_text=filenames[i])
    fig.show()




