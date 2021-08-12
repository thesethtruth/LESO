import numbers
import pandas as pd
import numpy as np

from ema_workbench import (
    EMAError,
    Scenario, 
    Policy
)

from ema_workbench.em_framework import (
    MonteCarloSampler,
    FullFactorialSampler,
    LHSSampler,
    PartialFactorialSampler,
    SobolSampler, 
    MorrisSampler, 
    FASTSampler,
    sample_levers,
    sample_uncertainties,
    experiment_generator,
)

from ema_workbench.util import get_module_logger

from ema_workbench.em_framework.util import determine_objects


# TODO:: replace with enum
LHS = "lhs"
MC = "mc"
FF = "ff"
PFF = "pff"
SOBOL = "sobol"
MORRIS = "morris"
FAST = "fast"

# TODO:: better name, samplers lower case conflicts with module name
SAMPLERS = {
    LHS: LHSSampler,
    MC: MonteCarloSampler,
    FF: FullFactorialSampler,
    PFF: PartialFactorialSampler,
    SOBOL: SobolSampler,
    MORRIS: MorrisSampler,
    FAST: FASTSampler,
}

_logger = get_module_logger(__name__)

def printerfunc(**kwargs):
    for key, value in kwargs.items():
        print(key+f": {value}")
    return None

def generate_experiments(
    model,
    scenarios=0,
    policies=0,
    uncertainty_sampling=LHS,
    uncertainty_union=False,
    levers_sampling=LHS,
    lever_union=False,
):

    if not scenarios and not policies:
        raise EMAError(('no experiments possible since both '
                        'scenarios and policies are 0'))

    if not scenarios:
        scenarios = [Scenario("None", **{})]
        uncertainties = []
        n_scenarios = 1
    elif(isinstance(scenarios, numbers.Integral)):
        sampler = SAMPLERS[uncertainty_sampling]()
        scenarios = sample_uncertainties(model, scenarios, sampler=sampler,
                                            union=uncertainty_union)
        uncertainties = scenarios.parameters
        n_scenarios = scenarios.n
    else:
        try:
            uncertainties = scenarios.parameters
            n_scenarios = scenarios.n
        except AttributeError:
            uncertainties = determine_objects(model, "uncertainties",
                                                union=True)
            if isinstance(scenarios, Scenario):
                scenarios = [scenarios]

            uncertainties = [u for u in uncertainties if u.name in
                                scenarios[0]]
            n_scenarios = len(scenarios)

    if not policies:
        policies = [Policy("None", **{})]
        levers = []
        n_policies = 1
    elif(isinstance(policies, numbers.Integral)):
        policies = sample_levers(model, policies, union=lever_union,
                                 sampler=SAMPLERS[levers_sampling]())
        levers = policies.parameters
        n_policies = policies.n
    else:
        try:
            levers = policies.parameters
            n_policies = policies.n
        except AttributeError:
            levers = determine_objects(model, "levers", union=True)
            if isinstance(policies, Policy):
                policies = [policies]

            levers = [l for l in levers if l.name in policies[0]]
            n_policies = len(policies)
    try:
        n_models = len(model)
    except TypeError:
        n_models = 1

    nr_of_exp = n_models * n_scenarios * n_policies

    _logger.info(('performing {} scenarios * {} policies * {} model(s) = '
                  '{} experiments').format(n_scenarios, n_policies,
                                           n_models, nr_of_exp))

    return scenarios, policies


def experiment_runner(model, scenarios, policies, model_name):

    designs = scenarios.designs
    experiments = pd.DataFrame(data=scenarios.designs, columns=scenarios.params)
    
    if hasattr(scenarios, 'n'):
        experiments['scenario'] = list(range(scenarios.n))
    else:
        experiments['scenario'] = "None"
    
    policies = policies[0] if isinstance(policies, list) else policies

    if hasattr(policies, 'n'):
        experiments['policy'] = list(range(policies.n))
    else:
        experiments['policy'] = "None"
  
    experiments['model'] = model_name
    outcomes = dict()
    
    for i, design in enumerate(designs):
        
        outcome = model(*design)

        for key, value in outcome.items():
            
            try:
                outcomes[key][i] = value
                
            except KeyError:

                outcomes[key] = np.empty([1, scenarios.n]) #@Seth does not include policies
                outcomes[key][:] = np.nan
                outcomes[key][i] = value


    return experiments, outcomes



