# decorator_trial.py
from functools import wraps
from numpy import float64

def pyomo_float_forcer(function):

    def postprocess(func_results):
        results = {
            key: float64(value) for key, value in func_results.items()
        }
        return results

    def preprocess(**kwargs):

        kwargs = {key:float(value) for key,value in kwargs.items()}
        return kwargs
    
    def wrapper(**kwargs):
        return postprocess(function(**preprocess(**kwargs)))
    
    return wraps(function)(wrapper)

import numpy as np
inputs = {
    "int": int(1), 
    "float": float(0.4), 
    "np64": np.float64(12.3), 
    "np32": np.float32(12.345)
}


def without_floatforce(**kwargs):
    
    func_res = {
        "int": int(1), 
        "float": float(0.4), 
        "np64": np.float64(12.3), 
        "np32": np.float32(12.345)
    }
    
    for key, value in kwargs.items():
        print(f"{key} is a {type(value)}")
    
    return func_res

@pyomo_float_forcer
def with_floatforce(**kwargs):

    func_res = {
        "int": int(1), 
        "float": float(0.4), 
        "np64": np.float64(12.3), 
        "np32": np.float32(12.345)
    }
    
    for key, value in kwargs.items():
        print(f"{key} is a {type(value)}")
    
    return func_res



# print("Without float forcing")
# results = without_floatforce(**inputs)
# print(f"{key} is a {type(value)}"for key, value in results.items())

print("With float forcing")
results = with_floatforce(**inputs)
for key, value in results.items():
    print(f"{key} is a {type(value)}")
