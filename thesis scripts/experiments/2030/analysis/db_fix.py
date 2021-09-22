from LESO.experiments.analysis import convert_db_to_df, load_ema_leso_results
import pandas as pd
import numpy as np
import plotly.express as pe
from pathlib import Path
import sys
import plotly.graph_objects as go
from tinydb.utils import D
import LESO.defaultvalues as defs
from tinydb import TinyDB
#%% constants

FOLDER = Path(__file__).parent
RESULT_FOLDER = FOLDER.parent / "results"
sys.path.append(FOLDER.parent.absolute().__str__())
exp_prefix = "evhub"
run_id = 210907

# db_file = f"{exp_prefix}_db{run_id}.json"
# dbo = TinyDB(RESULT_FOLDER / db_file)
# df = pd.DataFrame(
#     {key: [document.get(key, None) for document in db if "10h battery installed capacity" in document.keys()] for key in db.all()[-1]}
# )

# run_id = "210907_fix"
# db_file = f"{exp_prefix}_db{run_id}.json"
# db = TinyDB(RESULT_FOLDER / db_file)
# for document in dbo:
#     if "10h battery installed capacity" in document.keys():
#         db.insert({
#             key: document.get(key, None) for key in document.keys()
#         })

#%%

*_, df = load_ema_leso_results(
    run_id=run_id, 
    exp_prefix=exp_prefix, 
    results_folder=RESULT_FOLDER
)

