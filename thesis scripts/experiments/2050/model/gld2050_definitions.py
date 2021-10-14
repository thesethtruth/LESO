#%% gld250_definitions.py

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