import pandas
import numpy
import json

PATH_TO_DATASET = "/home/nico/AzurePublicDataset/data/AzureFunctionsInvocationTraceForTwoWeeksJan2021.txt"


def get_dataset() -> pandas.DataFrame:
    return pandas.read_csv(PATH_TO_DATASET)


def evaluate_iat(data: pandas.DataFrame, app: str, func: str):
    start_times = []
    iat = []
    subsect = data.loc[(data.app == app) & (data.func == func)]
    for index, row in subsect.iterrows():
        start_times.append(row.end_timestamp-row.duration)

    start_times.sort()
    for index in range(0, len(start_times)-1):
        iat.append(start_times[index+1]-start_times[index])
    return numpy.mean(iat)


def get_actions(data: pandas.DataFrame) -> list[dict]:
    actions = []
    for index, row in data.iterrows():
        if row.app + "_" + row.func not in actions:
            actions.append(row.app + "_" + row.func)
    return [action.split("_") for action in actions]


def evaluate_mean_action_duration(data:pandas.DataFrame, app: str, func: str):
    durations = []
    subsect = data.loc[(data.app == app) & (data.func == func)]
    for index, row in subsect.iterrows():
        durations.append(row.duration*1000)
    return numpy.mean(durations)


def analyze():
    data = get_dataset()
    actions = get_actions(data)
    compacted = []
    for action in actions:
        compacted.append(
            {
                "name": action[0] + "-" + action[1],
                "iat": evaluate_iat(data, action[0], action[1]),
                "duration": evaluate_mean_action_duration(data, action[0], action[1])
            }
        )
    store(compacted)
    return compacted


def store(data: list[dict]):
    json.dump(data, open("/home/nico/Scrivania/data_set", 'w'))


def retrieve() -> list[dict]:
    return json.load(open("/home/nico/Scrivania/data_set", 'r'))
