from pathlib import Path
import LESO


MODEL_FOLDER = Path(__file__).parent.parent / "model"
RESULTS_FOLDER = Path(__file__).parent.parent / "results"
RESULTS_FOLDER.mkdir(parents=True, exist_ok=True)

scenarios_2050 = {
    "Gelderland_2050_regional": {
        "id": 815695,
        "latlon": (52.06, 5.93),
        "target_re_share": 0.92,
        "target_re_share_ex_export": 0.71,
        "grid_cap": 2145.9,
        "price_curve": "regional_price_curve.pkl",
    },
    "Gelderland_2050_national": {
        "id": 815696,
        "latlon": (52.06, 5.93),
        "target_re_share": 1.01,
        "target_re_share_ex_export": 0.72,
        "grid_cap": 2145.9,
        "price_curve": "national_price_curve.pkl",
    },
    "Gelderland_2050_european": {
        "id": 815697,
        "latlon": (52.06, 5.93),
        "target_re_share": 0.58,
        "target_re_share_ex_export": 0.49,
        "grid_cap": 2145.9,
        "price_curve": "european_price_curve.pkl",
    },
    "Gelderland_2050_international": {
        "id": 815698,
        "latlon": (52.06, 5.93),
        "target_re_share": 0.56,
        "target_re_share_ex_export": 0.48,
        "grid_cap": 2145.9,
        "price_curve": "international_price_curve.pkl",
    },
}
MODELS = {
    modelname:MODEL_FOLDER / (modelname.lower() + ".pkl") for modelname in scenarios_2050.keys()
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



# this is needed due to the dependent but double variant uncertainty ranges given by ATB
def lithium_storage_linear_map(
    value,
):
    min, max = 0.25, 0.70  # @@
    map_min, map_max = 0.25, 0.81  # @@

    frac = (value - min) / (max - min)
    m_value = frac * (map_max - map_min) + map_min

    return m_value

if __name__ == "__main__":
    # use this to easily generate the metrics for installed capacity
    if True:  
        ref_system = LESO.System.read_pickle(list(MODELS.values())[0])
        m = []
        for c in ref_system.components:
            if not isinstance(c, (LESO.FinalBalance, LESO.ETMdemand)):
                out = c.name + " installed capacity"
                m.append(out)