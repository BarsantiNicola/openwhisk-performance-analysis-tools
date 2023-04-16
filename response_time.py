from matplotlib import pyplot as plt
import numpy
import os
from mongo_connection import mongo_connection


def analyze_scenario(host, port, db_name, scenario):
    client = mongo_connection(host,port,db_name, scenario, True)
    client_rt = client.fetch_data("client_response_time")
    graph_local_response_time(client_rt, "/home/nico/Desktop", scenario+"_rt")
    client_rt = client.fetch_data("minimum_response_time")
    graph_local_response_time(client_rt, "/home/nico/Desktop", scenario+"_min_rt")


def graph_local_response_time(data: list[dict], path: str, scenario_name: str):
    values = []
    actions = []
    timestamps = []
    values_path = path + "/" + scenario_name + "/values"
    cdf_path = path + "/" + scenario_name + "/cdf"
    boxplot_path = path + "/" + scenario_name + "/boxplot"
    extra_path = path + "/" + scenario_name + "/extra"
    os.system("mkdir -p " + values_path + " " + cdf_path + " " + boxplot_path + " " + extra_path)

    # grouping the data for actions
    for d in data:
        if d["action"] not in actions:
            actions.append(d["action"])
            values.append([])
            timestamps.append([])

        action_index = actions.index(d["action"])
        values[action_index].append(d["response_time"])
        timestamps[action_index].append(d["timestamp"])

    normalized_timestamps = []
    for timestamp in timestamps:
        m = min(timestamp)
        normalized_timestamps.append([d - m for d in timestamp])

    for index in range(0, len(values)):
        plot_values(actions[index] + " response time", values_path, values[index], normalized_timestamps[index])
        plot_ecdf(actions[index] + " cdf", cdf_path, values[index])
        plt_boxplot(actions[index] + " boxplot", boxplot_path, values[index])
    return timestamps, normalized_timestamps, values


def plot_values(title: str, path: str, values: list, timestamps: list):
    plt.plot(timestamps, values)
    plt.title = title
    plt.xlabel('Time(ms)', fontsize=14)
    plt.ylabel('Response Time(ms)')
    plt.savefig(path + "/" + title, dpi=100, bbox_inches='tight')
    plt.clf()


def plot_ecdf(title: str, path: str, values: list):
    values, counts = numpy.unique(values, return_counts=True)
    cum_sum = numpy.cumsum(counts)
    data = values, cum_sum / cum_sum[-1]
    plt.plot(data[0], data[1])
    plt.title = title
    plt.xlabel('Response Time(ms)', fontsize=14)
    plt.ylabel('Probability')
    plt.savefig(path + "/" + title, dpi=100, bbox_inches='tight')
    plt.clf()


def plt_boxplot(title: str, path: str, values: list):
    plt.boxplot(values)
    plt.title = title
    plt.ylabel('Response Time(ms)', fontsize=14)
    plt.savefig(path + "/" + title, dpi=100, bbox_inches='tight')
    plt.clf()