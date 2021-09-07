from typing import Tuple
import ema_workbench
import LESO
import json
from tinydb import TinyDB
import pandas as pd
from LESO import AttrDict


def load_ema_leso_results(
    run_id: int, exp_prefix: str,
    results_folder: str, return_db_as_df=True
) -> Tuple[pd.DataFrame, dict, pd.DataFrame]:
    """Small helper function to load results easily from the document structure"""

    ema_results = f"{exp_prefix}_ema_results_{run_id}.tar.gz"
    experiments, outcomes = ema_workbench.load_results(results_folder / ema_results)

    db_file = f"{exp_prefix}_db{run_id}.json"
    db = TinyDB(results_folder / db_file)
    if return_db_as_df:
        db = convert_db_to_df(db)

    return experiments, outcomes, db


def convert_db_to_df(db: TinyDB):
    """Note that this is not stable for non-structured (e.g. document-type) dbs"""
    df = pd.DataFrame(
        {key: [document.get(key, None) for document in db] for key in db.all()[0]}
    )

    return df


def annualized_cost(component: LESO.Component, system: LESO.System) -> float:
    """Calculate the annualized cost of a LESO component"""
    LESO.finance.set_finance_variables(component, system)
    return component.capex * component.crf + component.opex


def quick_lcoe(component: LESO.Component, system: LESO.System) -> float:
    """Calculates the LCOE based on annualized cost and yearly production"""
    return annualized_cost(component, system) / component.state.power.sum()


def open_leso_experiment_file(filepath: str) -> AttrDict:
    """Open a LESO experiment file (json write-out) and return an AttrDict"""

    with open(filepath, "r") as infile:
        di = AttrDict(json.load(infile))

    return di
