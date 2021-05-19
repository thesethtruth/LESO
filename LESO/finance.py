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

def annuity(interest, lifetime):
    """
    Annuity
    """
    pass

def roi():
    """
    Return On Investment
    """
    pass

def tco(component, pM):
    """
    Total Cost of Ownership
    """

    unit_capex = component.crf * component.capex
    unit_opex = component.opex
    pyoVar = component.pyoVar
    variable_cost = component.get_variable_cost(pM)
    
    objective = (unit_capex + unit_opex)*pyoVar + variable_cost

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
        'lcoe': lcoe
    }

    return sdict[objective]

