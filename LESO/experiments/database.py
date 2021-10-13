import pymongo
import ssl
import pandas as pd
from .password import beast

PASSWORD = beast
USER = 'beast'

def insert_entry_in_mongo(database: str, collection: str, entry: dict, username=None, password=None):
    """
    Method for writing data to the mongo cluster.
        database: ["experiments"] description of the run of experiments
        collection: ["nametag"] the id entered at the start of the ema experiments
        entry: [db_entry] the data to be pushed to the cluster
    """
    if username is None:
        username = USER
    if password is None:
        password = PASSWORD
    
    connect_string = f"mongodb+srv://{username}:{password}@freeclusterthesis.k6h1x.mongodb.net/experiments?retryWrites=true&w=majority"
    client = pymongo.MongoClient(connect_string, ssl_cert_reqs=ssl.CERT_NONE)

    db = client[database]
    db[collection].insert_one(entry)

    pass


def send_ema_exp_to_mongo(collection, entry):
    """
        Convience method for writing data to the mongo cluster.
            collection: ["nametag"] the id entered at the start of the ema experiments
            entry: [db_entry] the data to be pushed to the cluster
    """
    return insert_entry_in_mongo(
        database="experiments", collection=collection, entry=entry
    )

def read_mongo(database: str, collection: str, query={}, username=None, password=None, no_id=True):
    """ Read from Mongo and Store into DataFrame """

    # Connect to MongoDB
    db = _connect_mongo(database=database, username=username, password=password)

    # Make a query to the specific DB and Collection
    cursor = db[collection].find(query)

    # Expand the cursor and construct the DataFrame
    df =  pd.DataFrame(list(cursor))

    # Delete the _id
    if no_id:
        del df['_id']

    return df

def _connect_mongo(database: str, username=None, password=None):
    if username is None:
        username = USER
    if password is None:
        password = PASSWORD
    
    connect_string = f"mongodb+srv://{username}:{password}@freeclusterthesis.k6h1x.mongodb.net/experiments?retryWrites=true&w=majority"
    client = pymongo.MongoClient(connect_string, ssl_cert_reqs=ssl.CERT_NONE)

    db = client[database]

    return db