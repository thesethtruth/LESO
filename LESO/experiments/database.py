import pymongo
import ssl
from .password import beast as password


def insert_entry_in_mongo(database: str, collection: str, entry: dict):
    """
    Method for writing data to the mongo cluster.
        database: ["experiments"] description of the run of experiments
        collection: ["nametag"] the id entered at the start of the ema experiments
        entry: [db_entry] the data to be pushed to the cluster
    """

    connect_string = f"mongodb+srv://beast:{password}@freeclusterthesis.k6h1x.mongodb.net/experiments?retryWrites=true&w=majority"
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