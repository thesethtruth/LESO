from .api import get_pvgis, get_dowa, get_renewable_ninja, get_etm_curve
from .api_static import renewable_ninja_turbines
from .google import (
    cloud_upload_dict_to_blob,
    cloud_upload_blob_from_filename,
    cloud_create_bucket,
    cloud_fetch_blob_as_AttrDict,
    cloud_fetch_blob_as_dict,
    datastore_put_entry,
    datastore_query
)
