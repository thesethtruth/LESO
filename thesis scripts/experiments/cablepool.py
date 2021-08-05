import LESO
import pandas
import ETMeta
import os
from copy import deepcopy as copy

from models.experiments_overview import MODEL_FOLDER, RESULT_FOLDER
MODEL_NAME = 'cablepool.pkl'
model_to_open = os.path.join(MODEL_FOLDER, MODEL_NAME)
system = LESO.System.read_pickle(model_to_open)

def system_factory():

    fresh_system = copy(system)

    return fresh_system

def ema_leso():

    #content

    return None

