# LESO
#### LESO: Local Energy Systems Optimzer
> A minimal and low-code multi-mode framework to investigate cost-optimal renewable energy systems and help guide policy and decission makers in the energy transition.

### Content
This project is a result of my thesis project. My thesis works with this framework, that I have developed myself. It combines various approaches in energy modelling to support policy and decision makers under deep uncertainty that is entailed in the energy transition. The features and how to get started with LESO is ennumerated below.

 * [Getting started](#getting-started)
 * [Optimization](#optimization)
 * [Explorative scenarios](#explorative-scenarios)
 * [Parametric experiments](#parametric-experiments)
 * [ETM integration](#etm-integration)

---
## Getting started

This project is currently being released to work with `pip` for an easy install.
To install ETMeta use the following command (in your `venv` of choice).

`pip install https://github.com/thesethtruth/LESO/archive/master.zip`

Dependencies are specified in the setup.py without versioning to retain flexibility for users. Please make sure that you have latest versions of the modules listed below.

* `ETMeta` (a sub-project released as package at https://github.com/thesethtruth/ETMeta)
* `pandas`
* `numpy`
* `plotly`
* `pyomo`
* `pvlib`
* `windpowerlib`
* `ema-workbench`
* `xarray`
* `requests`
* `beautifulsoup4`
* `xarray`
* `dash`
* `dash-table`
* `openpyxl`
* `pyproj`


## Optimization
Energy systems are inherently complex when relying on higher shares of renewable energy. Therefore, typical design processes do no longer suffice. Generating a discrete set of concepts does not sufficiently explore the solution space and is has insufficient resolution to embody complex system dynamics and synergies. A solution is to generalize the design objective by using a cost function and using mathmatical optimization to correctly represent the solution space. 

In LESO this is done using Pyomo. This module alows us to implement algebraic expressions that define the optimization problem at hand. Using a cost or goal function and various constraint functions for all instances of time the energy system is reflected as a linear problem. A commercial solver (Gurobi) is applied to solve the resulting matrices. However, open-source solvers  with (slightly) lower preformance can also be applied. GLPK for instance, although any solver supported by Pyomo should work.

**Minimal use example:**

Consider an energy system based in central Netherlands. The `system` component can contain any amount of energy sinks and supplies from the LESO library. The coordinates supplied will be used to automatically fetch TMY data. Using the `ETMdemand` component a demand curve is exported from the [ETM](https://pro.energytransitionmodel.com/). The `PhotoVoltaic` and `Wind` component are configurable objects that calculate feed-in power based on the TMY that they receive from `system`. These components are wrappers around `pvlib` and `windpowerlib`, respectively. Configuration can be specified using keyword arguments or by edditing the default values. Setting the `dof` key to `True` allows the optimizer to vary its installed capacity to find the optimal solution given constraints. 
```
eM = LESO.system(lat=52, lon=5, name="git-example")
demand = LESO.ETMdemand(scenario_id=81589)
solar = LESO.PhotoVoltaic('PV-south', dof=True, azimuth=0)
grid = LESO.Grid('100KVA-grid', dof=False, installed=100)
wind = LESO.Wind('Enercon126', dof=True, )
deficit = LESO.FinalBalance()
eM.add_components([demand, solar, grid, wind, deficit])
output_file = 'example.json'
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

```

A major down-side of optimization is that it does not make trade-offs insightful as it typically only gives a single solution as output. To prevent model-says reasoning, explorative scenario mode is included.

## Explorative scenarios
This operation mode is based on directly resolving a merit-order energy balance. The user defines the installed capacity of each of the components and their place in the merit-order. LESO then  calculates the energy balance for every hour of the year. It is a lot quicker than optimization but lacks intelligence. A strong use-case is to implement scenario exploration around obtained optima, to visualize 'what-ifs'. For instance; what if we'd increase the installed capacity of wind? what if more battery storage is used over grid connectivity? 

This can be crucial to inform stakeholders about trade-offs and to visualize impact of design variables.

## Parametric experiments
Optimization includes validation of various tipping points between possible solutions. There is no ready implementation to research those tipping points without exposing the optimization algorithm to varying conditions. For energy systems optimization a key component is the price level of competing technologies. Policies should be robust over longer timespans while great uncertainty exist over addoption and learning rates of technologies. To include this added complexity and to obtain insight in previously 'invisible' tipping points, parametric experiments are implemented. 

To this end, [EMA workbench](https://emaworkbench.readthedocs.io/en/latest/) is included in LESO as support package. This allows us to do apply Latin Hypercube Space Sampling quite straight-forward. With this information we can generate insights on no-regret investments, solution sensitivity and indentify high-impact drivers.
