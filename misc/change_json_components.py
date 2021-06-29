import os
import glob
import json

wd = os.getcwd()
simulations_raw = glob.glob(wd+'/cache/2030*.json')


wl = [
    'pv',
    'wind',
    'ETMdemand',
    'lithium',
    'hydrogen',
    'grid',
    'Balance',
    'pva',
    'pv-bi',
    'windoffshore',
    'fastcharger',
    'consumer',
]

for filename in simulations_raw:
    with open(filename) as infile:
        d = json.load(infile)

    cd = dict()
    for key in d.keys():
        if any(
            [white in key for white in wl]
        ):
            cd.update({key: d[key]})

    nd = dict()
    nd.update({ 
        'components': cd,
        'system': d['system']
    })

    _, tail = os.path.split(filename)
    with open(f"results/{tail}", "w") as outfile: 
        json.dump(nd, outfile)
