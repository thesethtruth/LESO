#%% google.py
import os
import json
from typing import List, Tuple
from google.cloud import datastore
from google.cloud import storage
from LESO.attrdict import AttrDict

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gkey.json"
DSCLIENT = datastore.Client()
CSCLIENT = storage.Client()

## data store
# ================================================================================================

def datastore_put_entry(kind: str, entry: dict):
    """Puts an entry to the google datastore (which is configured using the .json key)"""
    entity = datastore.Entity(key=DSCLIENT.key(kind))
    entity.update(entry)
    DSCLIENT.put(entity)

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

## cloud storage
# ================================================================================================


def cloud_create_bucket(
    bucket_name: str, storage_class="STANDARD", location="europe-west1"
):
    """ function to create a new bucket, based on the project as defined in the key.json config """
    bucket = CSCLIENT.bucket(bucket_name=bucket_name)
    bucket.storage_class = storage_class
    CSCLIENT.create_bucket(bucket, location=location)


def cloud_upload_blob_from_filename(
    source_file_name: str, bucket_name: str, destination_blob_name: str, 
):
    """ upload a blob (based on a filename) to google cloud store """
    bucket = CSCLIENT.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

def cloud_upload_dict_to_blob(
    dicto: dict, bucket_name: str, destination_blob_name: str, 
):
    """ upload a blob (as dict) from google cloud store """
    bucket = CSCLIENT.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_string(json.dumps(dicto))

def cloud_fetch_blob_as_dict(
     bucket_name: str, blob_name: str, 
):
    """ download a blob (as dict) from google cloud store """
    bucket = CSCLIENT.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    return json.loads(blob.download_as_string())

def cloud_fetch_blob_as_AttrDict(
     bucket_name: str, blob_name: str, 
):  
    """ convience wrapper of cloud_fetch_blob_as_dict """
    return AttrDict(cloud_fetch_blob_as_dict(
        bucket_name=bucket_name,
        blob_name=blob_name
    ))


""" Keep this for future reference!
credentials = service_account.Credentials.from_service_account_info(service_account_info)
client = Client(credentials=credentials)
"""
