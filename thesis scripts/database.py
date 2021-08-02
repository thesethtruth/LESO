
# database.py
# import LESO
import numpy as np
import json
import pandas as pd
from tinydb import TinyDB, Query
from attrdict import AttrDict

in_filepath = 'C:\\Users\\Sethv\\#Universiteit Twente\\GIT\\LESO\\cache\\2030RES_Achterhoek.json'

db = TinyDB('db_test.json')
Result = Query()


with open(in_filepath) as infile:
    simu = json.load(infile)

simu = AttrDict(simu)


if False:
    eM = LESO.System(52, 5)
    filepath = None

    print('proceeding to hacky method of splitting power to pos/neg')
    for component in eM.components:
        component.split_states()

    # small helper function
    def _date_to_string(component):
        return np.datetime_as_string(component.state.index.values).tolist()

    save_info = dict()
    for component in eM.components:
        _key = component.__str__()
        state = component.state

        compdict = {
            _key: 
            {
            'state': {column: state[column].values.tolist() for column in state.columns if column != 'power'},
            'styling': component.styling,
            'settings': { key: getattr(component, key) for key in component.default_values if key != 'styling'},
            'name': component.name,
            }
        }
        styling = dict(styling = component.styling)
        compdict[_key].update(styling)

        save_info.update(compdict)

    sysdict = {
        'system': 
        {
        'dates': _date_to_string(eM.components[0]),
        'name': eM.name,
        'date': datetime.now().isoformat(),
        'last_call': eM.last_call,
        'optimization result': getattr(eM, 'optimization_result', 'Not available')
        }
    }

    save_info.update(sysdict)

    if filepath is None:
        name = save_info['system']['name'].replace("\/:*?<>|",'')
        date =  save_info['system']['date'][:17].replace(':','')
        last_call = eM.last_call
        filepath = f"cache/{name}__{date}__{last_call}.json"

    with open(filepath, "w") as outfile: 
        json.dump(save_info, outfile)