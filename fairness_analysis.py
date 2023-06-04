import numpy

import basics_tool
from matplotlib import pyplot as plt
import pandas as pd

import response_time
from mongo_connection import mongo_connection


def extract_response_time(data: list[dict]) -> (list, list):
    values = []
    timestamps = []
    print("[ResponseTime-Analysis] Extracting needed information from stored data...", end="")
    for d in data:
        values.append(d["response_time"])
        timestamps.append(d["timestamp"])

    m = min(timestamps)
    normalized_timestamps = [d-m for d in timestamps]
    return normalized_timestamps, values

def analyze_fairness(path:str, host:str, scenario_name:str):
    client = mongo_connection(host,27017, "test",scenario_name, True)
    data = client.fetch_data("normalized_service_response_time")
    rt = extract_response_time(data)
    steady = basics_tool.steady_state(rt[1])
    print("Max value: " + str(max(rt[1][steady:])))
    plot_boxplot(rt[1][steady:])
    return compute_fearness(path + "/"+scenario_name+"_fearness.png", rt[1][steady:])

def plot_boxplot(values: list):
    df = pd.DataFrame({'Response Time': values})
    myFig = plt.figure()
    #plt.ylim(0,600)
    bpdict = df.boxplot(whis=[0, 99], return_type='dict')
    annotate_boxplot(bpdict)
    plt.show()
    plt.clf()

def annotate_boxplot(bpdict, annotate_params=None,
                     x_offset=0.1, x_loc=0,
                     text_offset_x=35,
                     text_offset_y=30):
    if annotate_params is None:
        annotate_params = dict(xytext=(text_offset_x, text_offset_y), textcoords='offset points',
                               arrowprops={'arrowstyle': '->'})
    plt.annotate('       95%: ' + str("{:.2f}".format(bpdict['caps'][(x_loc * 2) + 1].get_ydata()[0])),
                 (x_loc + 1 + x_offset, bpdict['caps'][(x_loc * 2) + 1].get_ydata()[0]), **annotate_params)


def lorenz_curve(X):
    X_lorenz = X.cumsum() / X.sum()
    X_lorenz = numpy.insert(X_lorenz, 0, 0)
    return X_lorenz

def compute_fearness( path:str, data: list[int]):
    data.sort()
    lc= lorenz_curve(numpy.array(data))
    lcg = max([x/len(data) - lc[x] for x in range(0,len(data))])
    create_fearness_graph(path, lc)

    return lcg

def create_fearness_graph( path:str, fearness: list):
    plt.plot([0,1], [0,1], color='r', linestyle="dashed")
    plt.plot([x/len(fearness) for x in range(0,len(fearness))],fearness)
    plt.savefig(path , dpi=100, bbox_inches='tight')
    plt.show()
    plt.clf()


