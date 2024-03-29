import os
from cablepool_leso_handshake import RESULTS_FOLDER, RUNID
from ema_workbench import perform_experiments, save_results

from cablepool_ema_model_definition import model

# run experiments
results = perform_experiments(model, scenarios=200, policies=2)
# save results
results_file_name = os.path.join(RESULTS_FOLDER, f"cablepooling_ema_results_{RUNID}.tar.gz")
save_results(results, file_name=results_file_name)

