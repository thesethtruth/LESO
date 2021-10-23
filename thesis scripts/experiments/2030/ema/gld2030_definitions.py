#%% cablepool_definitions.py
from pathlib import Path
import LESO
from google.cloud.exceptions import Conflict


COLLECTION = "gld2030"
OUTPUT_PREFIX = f"{COLLECTION}_exp_"

MODEL_FOLDER = Path(__file__).parent.parent / "model"
try:
    RESULTS_FOLDER = Path(r"D:\0. Seth\v2 results") / f"{COLLECTION}"
    RESULTS_FOLDER.mkdir(parents=True, exist_ok=True)
    # when on beast
except FileNotFoundError:
    RESULTS_FOLDER = Path(r"C:\Users\Sethv\#Universiteit Twente\GIT\LESO\thesis scripts\experiments\2030\results")
    RESULTS_FOLDER.mkdir(parents=True, exist_ok=True)
    # when on Seth's laptop


# create bucket if not already exist
if False:
    try:
        LESO.dataservice.google.cloud_create_bucket(COLLECTION)
    except Conflict as c:
        print(c)

# this is needed due to the dependent but double variant uncertainty ranges given by ATB
def linear_map_2030(value):
    min, max = 0.41, 0.70 # @@
    map_min, map_max = 0.42, 0.81 # @@

    frac = (value - min) / (max-min)
    m_value = frac * (map_max-map_min) + map_min

    return m_value

# for the linear map in 2050, we return the same value
def linear_map_2050(value):
    return value

scenarios_2030 = {
    "2030RES_Achterhoek": {
        "id": 815753,
        "latlon": (52, 6.4),
        "target_re_share": 0.92,
        "target_re_share_ex_export": 0.68,
        "grid_cap": 219.3,
    },
    "2030RES_ArnhemNijmegen": {
        "id": 815754,
        "latlon": (54.9, 5.9),
        "target_re_share": 0.43,
        "target_re_share_ex_export": 0.38,
        "grid_cap": 608.6,
    },
    "2030RES_Cleantech": {
        "id": 815755,
        "latlon": (52.2, 6.1),
        "target_re_share": 0.56,
        "target_re_share_ex_export": 0.4,
        "grid_cap": 299.1,
    },
    "2030RES_Foodvalley ": {
        "id": 815756,
        "latlon": (52.1, 5.7),
        "target_re_share": 0.54,
        "target_re_share_ex_export": 0.43,
        "grid_cap": 322.3,
    },
    "2030RES_NoordVeluwe": {
        "id": 815757,
        "latlon": (52.4, 5.8),
        "target_re_share": 0.58,
        "target_re_share_ex_export": 0.49,
        "grid_cap": 146.6,
    },
    "2030RES_Rivierenland": {
        "id": 815758,
        "latlon": (51.9, 5.3),
        "target_re_share": 0.58,
        "target_re_share_ex_export": 0.53,
        "grid_cap": 590.3,
    },
    "2030Gelderland_hoog": {
        "id": 815715,
        "latlon": (52.06, 5.93),
        "target_re_share": 0.87,
        "target_re_share_ex_export": 0.63,
        "grid_cap": 2145.9,
    },
    "2030Gelderland_laag": {
        "id": 815716,
        "latlon": (52.06, 5.93),
        "target_re_share": 0.65,
        "target_re_share_ex_export": 0.51,
        "grid_cap": 2145.9,
    },
}

MODELS = {
    modelname:MODEL_FOLDER / (modelname.lower() + ".pkl") for modelname in scenarios_2030.keys()
}

METRICS = [
    # components
    "PV South installed capacity",
    "PV West installed capacity",
    "PV East installed capacity",
    "Vestas V90 2000 installed capacity",
    "2h battery installed capacity",
    "6h battery installed capacity",
    "10h battery installed capacity",
    'H2 seasonal installed capacity',
    'H2 subseasonal installed capacity',
    "Grid connection installed capacity",
    # others
    "objective_result",
    "additional_renewable_energy",
    "curtailment",
    "additional_investment_cost",
    "return_on_investment",
    "net_profit",
    ]



if __name__ == "__main__":
    # use this to easily generate the metrics for installed capacity
    if True:  
        ref_system = LESO.System.read_pickle(list(MODELS.values())[0])
        m = []
        for c in ref_system.components:
            if not isinstance(c, (LESO.FinalBalance, LESO.ETMdemand)):
                out = c.name + " installed capacity"
                m.append(out)