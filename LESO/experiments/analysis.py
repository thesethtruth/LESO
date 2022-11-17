from typing import Tuple
from pathlib import Path
import shutil
import ema_workbench
import LESO
import json
import pandas as pd
from LESO import AttrDict
from LESO.dataservice import (
    datastore_query,
    datastore_put_entry,
    cloud_fetch_blob_as_AttrDict,
    cloud_upload_dict_to_blob,
    cloud_upload_blob_from_filename,
)
from typing import Tuple, List
from LESO.leso_logging import get_module_logger

logger = get_module_logger(__name__)


def load_ema_leso_results(
    run_id: int,
    exp_prefix: str,
    results_folder: str,
    return_db_as_df=True,
    exclude_solver_errors=True,
) -> Tuple[pd.DataFrame, dict, pd.DataFrame]:
    """Small helper function to load results easily from the document structure"""
    from tinydb import TinyDB

    ema_results = f"{exp_prefix}_ema_results_{run_id}.tar.gz"
    experiments, outcomes = ema_workbench.load_results(results_folder / ema_results)

    db_file = f"{exp_prefix}_db{run_id}.json"
    db = TinyDB(results_folder / db_file)
    if return_db_as_df:
        db = convert_db_to_df(db)
        if exclude_solver_errors:
            db = db[db.solver_status == "ok"]

    return experiments, outcomes, db


def convert_db_to_df(db):
    """Note that this is not stable for non-structured (e.g. document-type) dbs"""
    from tinydb import TinyDB

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


def gdatastore_results_to_df(
    collection: str,
    filter: Tuple = None,
    filters: List[Tuple] = None,
    order: List = None,
) -> pd.DataFrame:
    """download a set of results from google datastore based using datastores syntax
    collection == kind
    filter follows the google datastore syntax e.g. ("key", "OPERATOR", <value>)
    order follows the google datastore syntax e.g:
        ascending is ["key"]
        descending is [-"key"]
        first and then by is ["key1", "key2"]
    """
    q = datastore_query(
        kind=collection,
        filter=filter,
        filters=filters,
        order=order,
    )
    return pd.DataFrame(q)


def gdatastore_put_entry(collection: str, entry: dict):
    """put an entry to google datastore
    collection == kind
    """
    logger.info("putting entry to google datastore")
    return datastore_put_entry(kind=collection, entry=entry)


def gcloud_read_experiment(
    collection: str,
    experiment_id: str,
) -> LESO.AttrDict:
    """read an experiment id (previously the json filename) from gcloud as AttrDict
    collection == bucket_name
    experiment_id == blob_name
    """
    return cloud_fetch_blob_as_AttrDict(bucket_name=collection, blob_name=experiment_id)


def gcloud_upload_experiment_dict(
    dicto: dict,
    collection: str,
    experiment_id: str,
):
    """upload an experiment dict to gcloud
    collection == bucket_name
    experiment_id == destination_blob_name
    """
    logger.info("sending exported result file to google cloud")
    return cloud_upload_dict_to_blob(
        dicto=dicto,
        bucket_name=collection,
        destination_blob_name=experiment_id,
    )


def gcloud_upload_log_file(
    filepath_to_log: Path,
    collection: str,
    log_id: str,
):
    """upload a log file to gcloud
    collection == bucket_name
    log_id == destination blob name
    """
    return cloud_upload_blob_from_filename(
        source_file_name=filepath_to_log,
        bucket_name=collection,
        destination_blob_name=log_id,
    )


def move_log_from_active_to_cold(
    active_folder: str,
    cold_folder: str,
    file_name: str,
):
    af = Path(active_folder)
    cf = Path(cold_folder)

    shutil.move(af / file_name, cf / file_name)
