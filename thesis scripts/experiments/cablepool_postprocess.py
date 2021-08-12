import ema_workbench
import os
import pandas as pd
from tinydb import TinyDB
from models.experiments_overview import RESULT_FOLDER
import pandas as pd

ema_results = "cabelpooling_ema_results.tar.gz"
ema_results_path = os.path.join(RESULT_FOLDER, ema_results)
experiments, outcomes = ema_workbench.load_results(ema_results_path)

data = pd.DataFrame(outcomes)

data['total_installed_capacity'] = data.iloc[:,:3].sum(axis=1)
data['volume_per_peak'] = data.total_renewable_energy/data.total_installed_capacity


db_file = "cablepooling_db.json"
db_path = os.path.join(RESULT_FOLDER, db_file)
db = TinyDB(db_path)


def convert_db_to_df(db):
    """ Note that this is not stable for non-structured (e.g. document-type) dbs"""
    df = pd.DataFrame(
        {
            key: 
            [document.get(key, None) for document in db]
            for key in db.all()[0]
        }
    )

    return df

df = convert_db_to_df(db)