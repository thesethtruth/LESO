import pandas as pd
import csv
from pathlib import Path
from scipy.signal import savgol_filter


def postprocess_etm_curve(
    filename_etm_pricecurve_csv: str,
    filename_pickle_out: str,
    savgol_window = 25,
    savgol_order = 4,
):
    # read csv from ETM
    FOLDER = Path(__file__).parent
    with open(FOLDER / filename_etm_pricecurve_csv, newline='') as f:
        reader = csv.reader(f)
        data = list(reader)
        energy_market_price = [float(row[1]) for row in data[1:]]


    #%% plot the energy price
    edf = pd.DataFrame(
        index = pd.date_range(start="01/01/2021", periods=8760, freq='h'),
        data = [price*1e6 for price in energy_market_price],
        columns= ['energy_price']
    )
    edf['smoother_energy_price'] = savgol_filter(edf.energy_price, savgol_window, savgol_order)

    edf.smoother_energy_price.to_pickle(FOLDER / filename_pickle_out)


