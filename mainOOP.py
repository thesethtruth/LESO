from LESO import System
from LESO import PhotoVoltaic, Wind, Lithium, FastCharger, Consumer, Grid



# model = System(52, 5, model_name = "VRE-ESS-EV-hub")
# # =============================================================================

# pv1 =           PhotoVoltaic('PV Full south')
# pv2 =           PhotoVoltaic('PV West', azimuth = 90)
# pv3 =           PhotoVoltaic('PV East', azimuth = -90)
# wind1 =         Wind('Windturbine Mikey')
# wind2 =         Wind('Windturbine   Johnson')
# bat1 =          Lithium('Li-ion EES')
# charger1 =      FastCharger('180 linkerbaan quick-charge 9000')
# petrolstation = Consumer('Total petrolstation')
# grid =          Grid('210 KVA', installed = 210e3)
# # =============================================================================


# component_list = [pv1, wind1, bat1, charger1, petrolstation, grid]

# model.add_components(component_list)

# model.run_merit_order()
  
# model.balance

system = System.from_pickle('LESO model')

components = system.components

def printer(fig, timeseries, start, end, component, styling, column):
    fig.add_trace(go.Scatter(
        x= timeseries.index[start:end],
        y= timeseries[label].iloc[start:end],
        stackgroup = styling['group'],
        mode = 'lines',
        name = styling['label'],
        line = dict(width = 0.3, color = styling['color']),
        ))


for component in components:
    _df = component.state

    plot_pos = hasattr(_df, 'power [+]')
    plot_neg = hasattr(_df, 'power [-]')
    plot_power = hasattr(_df, 'power') and not (plot_neg or plot_pos)

    if plot_pos:
        styling = component.styling[0]
        column = 'power [+]'
        printer(component, styling, column)

    if plot_neg:
        styling = component.styling[1]
        column = 'power [-]'
        printer(component, styling, column)
    
    if plot_power:
        styling = component.styling
        column = 'power'
        printer(component, styling, column)


    


        # fig.add_trace(go.Scatter(
        #     x= timeseries.index[start:end],
        #     y= timeseries[label].iloc[start:end],
        #     stackgroup = 'power',
        #     mode = 'lines',
        #     name = label,
        #     line = dict(width = linewidth, color = colordict[label]),
        #     ))