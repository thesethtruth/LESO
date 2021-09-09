from LESO.plotly_extension import lighten_color
import pandas as pd
import numpy as np
import plotly.graph_objects as go

## NP REL ATB
# storage cost
ref_2020_s = 277 # $/kWh
storage_projection = np.array([
    [1.0, 1.0, 1.0], 
    [0.61, 0.69, 0.85], 
    [0.41, 0.53, 0.7], 
    [0.25, 0.37, 0.7]
]) # kWh from ATB sheet

ref_2020_p = 257 # $/kW
power_projection = np.array([
    [1.0, 1.0, 1.0], 
    [0.62, 0.77, 0.87], 
    [0.42, 0.77, 0.81], 
    [0.25, 0.71, 0.81]
]) # kW from ATB sheet

years = [2020, 2025, 2030, 2050]
scenarios = ["Advanced", "Moderate", "Conservative"]
atb_storage = pd.DataFrame(storage_projection, index=years, columns=scenarios)
atb_power = pd.DataFrame(power_projection, index=years, columns=scenarios)
print(atb_storage)
print(atb_power)