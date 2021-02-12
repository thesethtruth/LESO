import requests
import json

def getPVGIS(lat, lon, outputformat = "json"):
    # Latitude, in decimal degrees, south is negative.
    # Longitude, in decimal degrees, west is negative.
    request_url = "https://re.jrc.ec.europa.eu/api/tmy?lat={lat}&lon={lon}&outputformat={outputformat}".format(lat=lat, lon=lon, outputformat=outputformat)
    response = requests.get(request_url)

    if not response.status_code == 200:
        raise ValueError 

    return response

def jprint(obj):
    # create a formatted string of the Python JSON object
    text = json.dumps(obj, sort_keys=True, indent=4)
    print(text)