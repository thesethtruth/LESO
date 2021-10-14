#%% gld2050_priceprofiles.py
import pandas as pd
from LESO import ETMdemand
from scipy.signal import savgol_filter
from pathlib import Path

#%%

def postprocess_etm_curve(
    df,
    filename_pickle_out: str,
    savgol_window = 25,
    savgol_order = 4,
):
    FOLDER = Path(__file__).parent
    df.columns = ["energy_price"]
    df['smoother_energy_price'] = savgol_filter(df.energy_price, savgol_window, savgol_order)

    df.smoother_energy_price.to_pickle(FOLDER / filename_pickle_out)

#%%

SCENARIOS = {
    "regional": 9184,
    "national": 9185,
    "european": 9186,
    "international": 9187,
}


for key, value in SCENARIOS.items():

    etm_api = ETMdemand(key, value, 2050).api
    scenario_id = etm_api.scenario_id

    url = f"https://engine.energytransitionmodel.com/api/v3/scenarios/{scenario_id}/curves/electricity_price.csv"
    df = pd.read_csv(url, index_col=0)
    
    filename_pickle_out = f"{key}_price_curve.pkl"
    postprocess_etm_curve(df, filename_pickle_out)
