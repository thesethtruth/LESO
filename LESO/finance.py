# finance.py

def wacc(interests, market_values):
    """
    Weighted Average Cost of Capital
    Best but perhaps to detailed representation for cost of capital. 
    (relates to multiple sources of capital, which are weighted by volume)
    """
    
    r = interests
    MV = market_values

    wi = sum([r[i]*MV[i] for i in range(len(r))]) / sum([MV[i] for i in range(len(r))])

    return wi

def rdr(interest, exp_inflation_rate, **kwargs):
    """
    Real Discount Rate
    This allows to factor out inflation out of economic analysis
    """

    i = interest
    f = exp_inflation_rate
    
    ri = (i-f)/(1+f)

    return ri

def crf(interest, lifetime):
    """
    Capital Recovery Factor
    Recommended use of rdr to calculate real discount rate (actual cost of interest)
    --> crf = 1/annuity
        --> CAPEX*crf == CAPEX / annuity
    """
    
    i = interest
    n = lifetime
    if n is None:
        ci = 1
    else:
        ci = (i*(1 + i)**n)/((1 + i)**n - 1)

    return ci

def roi():
    """
    Return On Investment
    """
    pass

def tco(component, eM):
    """
    Total Cost of Ownership
    """
    pM = eM.model # extract pyomo model from enery model
    system = eM # energy model is system
    
    if component.capex != 0:
        unit_capex =    component.capex + (
                        system.lifetime - component.lifetime ) / (
                        component.lifetime ) * component.replacement
                        # linear replacement assumption
    else:
        unit_capex = 0
    
    lifetime_fixed_cost = component.opex * system.lifetime #  fixed operation expences over lifetime
    pyoVar = component.pyoVar # scaling factor in optimization issue
    lifetime_variable_cost = component.get_variable_cost(pM) * system.lifetime # variable operation expences over lifetime
    
    objective = system.crf*(
                (unit_capex + lifetime_fixed_cost)*pyoVar +
                lifetime_variable_cost
                )
                # use crf to discount all cashflows over the system lifetime
                # and come to annualized cash flows
    
    return objective

def osc(component, eM):
    """
    Overnight system cost
    """
    pM = eM.model # extract pyomo model from enery model
    system = eM # energy model is system
    
    if component.capex != 0:
        unit_capex =    component.capex + (
                        system.lifetime - component.lifetime ) / (
                        component.lifetime ) * component.replacement
                        # linear replacement assumption
    else:
        unit_capex = 0
    
    fixed_cost = component.opex # without system lifetime, only the first year
    pyoVar = component.pyoVar # scaling factor in optimization issue
    variable_cost = component.get_variable_cost(pM) # without system lifetime, only the first year 
    
    objective = (system.crf*(unit_capex)+fixed_cost)*pyoVar + variable_cost
                # use crf to discount *only investment* over the system lifetime
                # and add all operation (yearly) cost to come to overnight system cost
    
    return objective

def lcoe():
    """
    Levelized Cost Of Energy
    """
    raise NotImplementedError('Lcoe does not exist (yet!)')
    pass

def functionmapper(objective):

    sdict = {
        'tco': tco,
        'lcoe': lcoe,
        'osc': osc
    }

    return sdict[objective]

def set_finance_variables(obj):

    f = obj.exp_inflation_rate
    i = obj.interest
    l = obj.lifetime

    if l is not None and l != 0:
        obj.rdr = rdr(i, f)
        r = obj.rdr
        obj.crf = crf(r, l)
        obj.annuity = 1/obj.crf
