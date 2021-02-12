import pandas as pd
# define color scales
colordict = {
        # Powers
        'PV power': '#ebd25b',
        'Wind power': '#8cc0ed',
        'Battery discharging':  '#7fc78f',
        'Grid import':'#f2b65c',
        'Underload': '#f25c5c',
        # Loads
        'Consumption load': '#f5645f',
        'Charging load': '#a5c0c2',
        'Battery charging': '#85a0d6',
        'Grid export': '#d18426',
        'Curtailment': '#454545',
        # Sinks
        'Battery energy': '#85a0d6',
        'Battery SOC': '#f25c5c'
    }

readfiles = False
if readfiles:
    # read timeseries
    filepath = "outputdata/timeseries_1000.0kWh_3chargers.pkl"
    timeseries = pd.read_pickle(filepath)
    timeseries = timeseries/1e3         # kWh
    
    # read yearly
    filepath = "outputdata/yearly_1000.0kWh_3chargers.pkl"
    yearly = pd.read_pickle(filepath)
    yearly = yearly/1e6         # kWh
    
    # read financials
    filepath = "outputdata/financials_1000.0kWh_3chargers.pkl"
    financials = pd.read_pickle(filepath)
    for label in timeseries.columns[0:5]:
        line_color = colordict[label]
        print(line_color)



# options for dropdown menu
weeks = {}
for i in range(1,53) :
    weeks['Week {:.0f}'.format(i)] = i
startingweek = list(weeks.values())[0]




    
    
# function to resync 
resync_outputdata = False
if resync_outputdata:
    import os
    # read folder for options
    folderlist = os.listdir("outputdata")
    # take off the extension
    folderlist =[ i.replace(".pkl", "") for i in folderlist]
    folderlist =[ i.replace("optionfame.csv", "") for i in folderlist]
    # remove underscore
    folderlist =[ i.split('_') for i in folderlist]
    # only count 1 variant of same data (yearly)
    optionframe = pd.DataFrame()
    
    optionframe['Chargers'] = [int(i[2].replace("chargers", "")) for i in folderlist if i[0] == 'yearly']
    optionframe['Battery size [kWh]'] = [int(i[1].replace(".0kWh", "")) for i in folderlist if i[0] == 'yearly']
    
    optionframe.to_csv("outputdata/optionframe.csv")


test_options = False
if test_options:
    optionframe = pd.read_csv("outputdata/optionframe.csv", index_col = 0)
    chargers = optionframe.drop_duplicates(subset= ['Chargers'])['Chargers']
    for charger in chargers:
        print(charger)
        correspondingbatteries = optionframe[optionframe['Chargers']==charger].iloc[:,1].values
        print(correspondingbatteries)
        




# Code dump belowwwww

if False:
    selectedoption = "{battery}.0kWh_{charger}chargers.pkl".format(battery = battery, charger = charger)
    # read timeseries
    filepath = "outputdata/{datatype}_{selectedoption}".format(selectedoption = selectedoption, datatype = 'timeseries')
    timeseries = pd.read_pickle(filepath)
    timeseries = timeseries/1e3         # kWh
    
    selectedoption = "{battery}.0kWh_{charger}chargers.pkl".format(battery = battery, charger = charger)
    # read yearly
    filepath = "outputdata/{datatype}_{selectedoption}".format(selectedoption = selectedoption, datatype = 'yearly')
    yearly = pd.read_pickle(filepath)
    yearly = yearly/1e6         # kWh
    
    selectedoption = "{battery}.0kWh_{charger}chargers.pkl".format(battery = battery, charger = charger)
    # read financials
    filepath = "outputdata/{datatype}_{selectedoption}".format(selectedoption = selectedoption, datatype = 'financials')
    financials = pd.read_pickle(filepath)


testdict = {'key': [1000, 'format']}

for key, value in testdict.items():
    print(key)
    print(value[1])

    

    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    