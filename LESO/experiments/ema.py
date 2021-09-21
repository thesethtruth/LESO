from functools import wraps
from numpy import float64

def ema_pyomo_interface(handshake):
    """
    All kwargs are processed to python floats (to maintain functionality in 
    pyomo) and all outputs are forced to np.floats for stable interaction with
    ema_workbench.
    """
    def postprocess(func_results):
        """"""
        results = {
            key: float64(value) for key, value in func_results.items()
        }
        return results

    def preprocess(**kwargs):

        kwargs = {key:float(value) for key,value in kwargs.items()}
        return kwargs
    
    def wrapper(**kwargs):
        return postprocess(handshake(**preprocess(**kwargs)))
    
    return wraps(handshake)(wrapper)