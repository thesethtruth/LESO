import pandas as pd
from typing import Tuple, List
import os
import json
from google.cloud import datastore
from google.cloud import storage
from pathlib import Path

path = str((Path(__file__).parent / "gkey.json").absolute())
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = path
DSCLIENT = datastore.Client()
CSCLIENT = storage.Client()


def cloud_fetch_blob_as_dict(
    bucket_name: str,
    blob_name: str,
):
    """download a blob (as dict) from google cloud store"""
    bucket = CSCLIENT.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    return json.loads(blob.download_as_string())


def gcloud_read_experiment(
    collection: str,
    experiment_id: str,
) -> dict:
    """read an experiment id (previously the json filename) from gcloud as AttrDict
    collection == bucket_name
    experiment_id == blob_name
    """
    return cloud_fetch_blob_as_dict(bucket_name=collection, blob_name=experiment_id)


def datastore_query(
    kind: str,
    filter: Tuple = None,
    filters: List[Tuple] = None,
    order: List = None,
) -> datastore.Entity:
    """query for a set of entities based on at least the kind. Extra filters can be added using filter or filters"""
    query = DSCLIENT.query(kind=kind)
    if filter is not None:
        query.add_filter(*filter)
    if filters is not None:
        for filter in filters:
            query.add_filter(*filter)
    if order is not None:
        query.order = order
    return query.fetch()


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
