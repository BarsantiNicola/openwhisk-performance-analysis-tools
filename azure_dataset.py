
import pandas
import numpy
import json


def get_dataset(path: str) -> pandas.DataFrame:
    return pandas.read_csv(path)


def evaluate_iat(data: pandas.DataFrame, app: str, func: str):
    start_times = []
    iat = []
    subsect = data.loc[(data.app == app) & (data.func == func)]
    for index, row in subsect.iterrows():
        start_times.append(row.end_timestamp-row.duration)

    start_times.sort()
    for index in range(0, len(start_times)-1):
        iat.append(start_times[index+1]-start_times[index])
    return numpy.mean(iat)/1000


def get_actions(data: pandas.DataFrame) -> list[dict]:
    actions = []
    for index, row in data.iterrows():
        if row.app + "_" + row.func not in actions:
            actions.append(row.app + "_" + row.func)
    return [action.split("_") for action in actions]


def extract_trace(data: pandas.DataFrame, app: str, func: str) -> list[tuple[float, int]]:
    results = []
    subsect = (data.loc[(data.app == app) & (data.func == func)]).sort_values("end_timestamp")
    for index, row in subsect.iterrows():
        results.append((row.end_timestamp-row.duration, int(round(row.duration))))
    results.sort(key=lambda a: a[0])
    return results


def evaluate_mean_action_duration(data: pandas.DataFrame, app: str, func: str):
    durations = []
    subsect = data.loc[(data.app == app) & (data.func == func)]
    for index, row in subsect.iterrows():
        durations.append(row.duration)
    return int(numpy.mean(durations).round())


def normalize_trace(compacted: list[dict]) -> list[dict]:
    m = 0
    for c in compacted:
        if m == 0:
            min(extract_time_trace(c["trace"]))
        else:
            m = min(m, min(extract_time_trace(c["trace"])))
    new_trace = []
    for c in compacted:
        m2 = 0
        for t in c["trace"]:
            t1 = t[0]-m
            new_trace.append((t1, t[1]))
            if m2 == 0:
                m2 = t1
            else:
                m2 = min(m2, t1)
        c["start_at"] = m2
        c["trace"] = new_trace
    return compacted


def extract_time_trace(trace: list[tuple[float, int]]):
    times = []
    for t in trace:
        times.append(t[0])
    return times


def analyze_trace(input_file: str, output_file: str, size: int):
    print("TraceAnalysis V2")
    data = get_dataset(input_file)
    actions = get_actions(data)[:size]
    compacted = []
    for action in actions:
        print("Extracting action: " + action[0] + "-" + action[1])
        compacted.append(
            {
                "name": action[0] + "-" + action[1],
                "iat": evaluate_iat(data, action[0], action[1]),
                "duration": evaluate_mean_action_duration(data, action[0], action[1]),
                "trace": extract_trace(data, action[0], action[1])
            }
        )
    extended = normalize_trace(compacted)
    store(extended, output_file)
    return compacted


def store(data: list[dict], path: str):
    json.dump(data, open(path, 'w'))


def retrieve(path: str) -> list[dict]:
    return json.load(open(path, 'r'))
