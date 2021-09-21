# extension.py
import LESO


def constrain_minimal_share_of_renewables(
    share_of_re: float,
    system: LESO.System,
    generators: list[LESO.SourceSink],
    storages: list[LESO.Storage],
    demands: list[LESO.SourceSink],
    exclude_export_from_share=True,
):
    """
    Based on the minimal share of RE this contrains the energy generated
    AND used wihtin the systems context
    """
    pyo_model = system.model
    time = pyo_model.time
    t_zero, t_final = time[0], time[-1]

    contributing_components = []

    for component in system.components:

        # catch generators
        is_generator = any(isinstance(component, generator) for generator in generators)
        if is_generator:

            # for this we can just sum the dataframe
            contributing_components.append(sum(component.state.power) * component.pyoVar)

        # catch storages
        is_storage = any(isinstance(component, storage) for storage in storages)
        if is_storage:
            ckey = component.__str__()
            energy = getattr(pyo_model, ckey + "_E", None)

            # if energy is buffered at the end of the year it does not contribute towards the goals; 
            # so it should be substracted from initial state of charge
            contributing_components.append(energy[t_zero] - energy[t_final])

        
        # cath final balance
        if isinstance(component, LESO.FinalBalance):
            ckey = component.__str__()
            curtailment = getattr(pyo_model, ckey + "_Pneg", None)

            # curtailment is negative by deffinition; so we can just add this to the sum
            contributing_components.append(sum(curtailment[t] for t in time))
        
        # catch grid
        if exclude_export_from_share:
            if isinstance(component, LESO.Grid):

                ckey = component.__str__()
                export = getattr(pyo_model, ckey + "_Pneg", None)

                # export is negative by deffinition; so we can just add this to the sum
                contributing_components.append(sum(export[t] for t in time))

    contraintlist = getattr(pyo_model, pyo_model.constraint_ID)

    contraintlist.add(
        sum(
            component for component in contributing_components
        ) / (
            sum(demand.state.power for demand in demands)
        ) >= share_of_re
    )