# AAAAHHHHH.py
from LESO.experiments import open_leso_experiment_file
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

FOLDER = Path(__file__).parent
FIG_FOLDER = FOLDER / "images"
RESULT_FOLDER = FOLDER.parent / "results"


ref_filenames = {
    0: 'evhub_exp_210285.json',
    0.5: 'evhub_exp_717774.json',
    1: 'evhub_exp_711889.json',
    1.5: 'evhub_exp_227895.json'
 }


thisone = "cablepooling_exp_162076137670371.json"
exp = open_leso_experiment_file(thisone)
# filename = "evhub_exp_227895.json"
# exp = open_leso_experiment_file(RESULT_FOLDER / filename)
for filename in ref_filenames.values():
    exp = open_leso_experiment_file(RESULT_FOLDER / filename)
    plt.figure()
    df = pd.DataFrame(exp.components.lithium2h_1.state)
    lst = []
    for i in range(8760):
        lst.append(-sum(df.loc[:i,'power [-]'])-sum(df.loc[:i,'power [+]']))
    df.plot()
    df['E check'] = lst

    plt.figure()
    df.loc[100:200,:].plot()

    plt.figure()
    df.plot()
    losses = sum(df['power [+]'] * (1-0.85** .5)  - df['power [-]'] * (1-0.85** .5)  +  df['energy'] * (1-0.995))
    plt.hlines([losses], 0, 8760)


    