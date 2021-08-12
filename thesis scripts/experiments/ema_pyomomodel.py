import os
import pandas as pd
import numpy as np

from ema_workbench.em_framework.model import BaseModel, SingleReplication
from ema_workbench.util.ema_logging import _logger, method_logger
from emaleso_cable import Handshake, METRICS

class PyomoModel(SingleReplication):
    
    def __init__(self, name, leso_instance=None, **kwargs):
        self.leso_instance = leso_instance
        super().__init__(name, **kwargs)

    
    def model_init(self, policy):
        
        self.policy = policy

        pass
        

        
    
    def run_experiment(self, experiment):

        _logger.debug("running model")
        
        results = Handshake(**experiment)
        

        return {metric: np.random.random() for metric in METRICS}