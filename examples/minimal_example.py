# minima_example.py
import LESO

eM = LESO.system(lat=52, lon=5, name="git-example")
demand = LESO.ETMdemand(scenario_id=81589)
solar = LESO.PhotoVoltaic('PV-south', dof=True, azimuth=0)
grid = LESO.Grid('100KVA-grid', dof=False, installed=100)
wind = LESO.Wind('Enercon126', dof=True, )
deficit = LESO.FinalBalance()
eM.add_components([demand, solar, grid, wind, deficit])
output_file = 'minimal_example.json'
eM.optimize(
            objective='tco',        # total cost of ownership
            time=None,              # resorts to default; year 8760h
            store=True,             # write-out to json
            filepath=output_file,   # resorts to default: modelname+timestamp
            solver='gurobi',        # default solver
            nonconvex=False,        # solver option (warning will show if needed)
            solve=True,             # solve or just create model
            unit = 'M'              # currently not working as expected
)