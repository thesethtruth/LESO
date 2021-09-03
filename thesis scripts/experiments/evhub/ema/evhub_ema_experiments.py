from evhub_leso_handshake import RESULTS_FOLDER, RUNID
from ema_workbench import perform_experiments, save_results

from evhub_ema_model_definition import model

# run experiments
results = perform_experiments(model, scenarios=2, policies=2)
# save results
RESULTS_FOLDER.mkdir(parents=True, exist_ok=True)
results_file_name = RESULTS_FOLDER / f"cabelpooling_ema_results_{RUNID}.tar.gz"
save_results(results, file_name=results_file_name)

