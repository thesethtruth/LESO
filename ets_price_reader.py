import pandas as pd
from functools import cache

@cache
def ets_prices_reader(*args, prefix = '../', sufix='.xlsx'):

    frames = list()

    for filename in args:
        filepath = prefix+filename+sufix
        frames.append(pd.read_excel(filepath, engine="openpyxl", index_col=0, header=2))

    return frames