import os
from cablepool_leso_handshake import RESULT_FOLDER, RUNID
from ema_workbench import perform_experiments, save_results

from cablepool_ema_model_definition import model

# run experiments
results = perform_experiments(model, scenarios=100, policies=3)
# save results
results_file_name = os.path.join(RESULT_FOLDER, f"cabelpooling_ema_results_{RUNID}.tar.gz")
save_results(results, file_name=results_file_name)

