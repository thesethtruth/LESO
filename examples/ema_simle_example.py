## simple experiment to demonstrate bare EMA functionalities

import os

RUNID = 100821


def ema_experiment(
    distance=None,
    km_fee=None, 
    fuel_price=None,
    speed=None,
    driver_salary_rate=None,
    startup_fee=None,
    ):

    milage = 10+(25-0.000011*speed**3)
    fuel_use = distance / milage
    fuel_cost = fuel_use * fuel_price
    income = startup_fee + km_fee * distance 
    time_spent = distance/speed
    salary_cost = time_spent * driver_salary_rate
    profit = income - fuel_cost - salary_cost


    results = {
        "profit": profit,
        "fuel_use": fuel_use,
        "time_spent": time_spent
    }

    return results



from ema_workbench import (
    RealParameter,
    ScalarOutcome,
    perform_experiments,
    Model,
    save_results
    )

# initiate model
model = Model(name='taxidriver', function=ema_experiment)

# levers
model.levers = [
    RealParameter("startup_fee", 2, 5),
    RealParameter("km_fee", 0.2, 0.5),
    RealParameter("speed", 90, 130),
]


# uncertainties
model.uncertainties = [
    RealParameter("distance", 3, 60),
    RealParameter("fuel_price", 1.1, 1.8),
    RealParameter("driver_salary_rate", 10, 20),
]

# specify outcomes
model.outcomes = [
    ScalarOutcome("profit"),
    ScalarOutcome("fuel_use"),
    ScalarOutcome("time_spent"),
    ]

# run experiments
results = perform_experiments(model, scenarios=10, policies=3)

# # save results
# results_file_name = os.path.join(RESULT_FOLDER, f"cabelpooling_ema_results_{RUNID}.tar.gz")
# save_results(results, file_name=results_file_name)