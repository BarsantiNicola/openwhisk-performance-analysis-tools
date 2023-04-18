
import numpy as np
from matplotlib import pyplot as plt, cm
import numpy
import os
from mongo_connection import mongo_connection
import basics_tool
import pandas as pd
import containers_analysis


def extract_response_time(data: list[dict]) -> (list, list, list):
    values = []
    actions = []
    timestamps = []

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

    return actions, normalized_timestamps, values


def analyze_scenario(host, port, db_name, scenario):
    client = mongo_connection(host, port, db_name, scenario, True)
    client_rt = client.fetch_data("client_response_time")
    local_rt = client.fetch_data("minimum_response_time")
    service_rt = client.fetch_data("service_response_time")

    actions_client, timestamp_client, values_client = extract_response_time(client_rt)
    actions_local, timestamp_local, values_local = extract_response_time(local_rt)
    actions_service, timestamp_service, values_service = extract_response_time(service_rt)
    results = []
    for index in range(0, len(actions_client)):
        steady = basics_tool.steady_state(values_client[index])
        independent_timestamp, independent_values = basics_tool.subsample_to_independence(
            timestamp_client[index][steady:], values_client[index][steady:], 0.99)
        results.append(graph_response_time(independent_timestamp, independent_values, "/home/nico/Desktop", scenario + "/client_rt",
                            actions_client[index]))

    for index in range(0, len(actions_local)):
        steady = basics_tool.steady_state(values_local[index])
        independent_timestamp, independent_values = basics_tool.subsample_to_independence(
            timestamp_local[index][steady:], values_local[index][steady:], 0.99)
        results.append(graph_response_time(independent_timestamp, independent_values, "/home/nico/Desktop", scenario + "/local_rt",
                            actions_local[index]))

    for index in range(0, len(actions_service)):
        steady = basics_tool.steady_state(values_service[index])
        independent_timestamp, independent_values = basics_tool.subsample_to_independence(
            timestamp_service[index][steady:], values_service[index][steady:], 0.99)
        results.append(graph_response_time(independent_timestamp, independent_values, "/home/nico/Desktop", scenario + "/service_rt",
                            actions_service[index]))

    return results + containers_analysis.graph_container_state("/home/nico/Desktop/" + scenario, client)


def graph_response_time(timestamps: list[dict], values: list[dict], path: str, scenario_name: str, action: str) -> dict:
    values_path = path + "/" + scenario_name + "/values"
    cdf_path = path + "/" + scenario_name + "/cdf"
    boxplot_path = path + "/" + scenario_name + "/boxplot"
    pmf_path = path + "/" + scenario_name + "/pmf"
    os.system("mkdir -p " + values_path + " " + cdf_path + " " + boxplot_path + " " + pmf_path)

    plot_values(action + " response time", values_path, values, timestamps)
    plot_ecdf(action + " cdf", cdf_path, values)
    plot_epmf(action + " pmf", pmf_path, values)
    plot_boxplot(action + " boxplot", boxplot_path, values)
    return {
        "mean": basics_tool.list_mean(values),
        "median": basics_tool.list_median(values),
        "var": basics_tool.list_var(values),
        "std": basics_tool.list_std(values),
        "action": action,
        "type": scenario_name[scenario_name.rfind("/")+1:]
    }

def plot_values(t: str, path: str, values: list, timestamps: list):
    plt.scatter(timestamps, values, c=values, cmap="viridis")
    plt.title = "mytitle"
    plt.xlabel('Time(ms)', fontsize=14)
    plt.ylabel('Response Time(ms)', fontsize=14)
    plt.savefig(path + "/" + t, dpi=100, bbox_inches='tight')
    plt.clf()


def plot_epmf(t: str, path: str, values: list):
    mean = basics_tool.list_mean(values)
    weights = np.ones_like(values) / len(values)
    plt.hist(values, 30, color="lightblue", ec="blue", weights=weights)
    plt.ylabel('Probability', fontsize=14)
    plt.xlabel('Response Time(ms)', fontsize=14)
    plt.annotate('Mean: ' + str(mean), xy=(mean, 1.2))
    plt.savefig(path + "/" + t, dpi=100, bbox_inches='tight')


def plot_ecdf(title: str, path: str, values: list):
    plt.clf()
    values, counts = numpy.unique(values, return_counts=True)
    cum_sum = numpy.cumsum(counts)
    data = values, cum_sum / cum_sum[-1]
    plt.plot(data[0], data[1])
    # plt.title = title
    plt.xlabel('Response Time(ms)', fontsize=14)
    plt.ylabel('Probability', fontsize=14)
    plt.savefig(path + "/" + title, dpi=100, bbox_inches='tight')
    plt.clf()


def plot_boxplot(title: str, path: str, values: list):
    plt.clf()
    df = pd.DataFrame({'Response Time': values})
    myFig = plt.figure()
    bpdict = df.boxplot(whis=[0, 99], return_type='dict')
    annotate_boxplot(bpdict)
    myFig.savefig(path + "/" + title, dpi=100, bbox_inches='tight')
    myFig.clf()


def annotate_boxplot(bpdict, annotate_params=None,
                     x_offset=0.1, x_loc=0,
                     text_offset_x=35,
                     text_offset_y=20):
    if annotate_params is None:
        annotate_params = dict(xytext=(text_offset_x, text_offset_y), textcoords='offset points',
                               arrowprops={'arrowstyle': '->'})

    plt.annotate('       Median: ' + str("{:.2f}".format(bpdict['medians'][x_loc].get_ydata()[0])),
                 (x_loc + 1 + x_offset, bpdict['medians'][x_loc].get_ydata()[0]), **annotate_params)
    plt.annotate('       25%: ' + str("{:.2f}".format(bpdict['boxes'][x_loc].get_ydata()[0])),
                 (x_loc + 1 + x_offset, bpdict['boxes'][x_loc].get_ydata()[0]), **annotate_params)
    plt.annotate('       75%: ' + str("{:.2f}".format(bpdict['boxes'][x_loc].get_ydata()[2])),
                 (x_loc + 1 + x_offset, bpdict['boxes'][x_loc].get_ydata()[2]), **annotate_params)
    plt.annotate('       5%: ' + str("{:.2f}".format(bpdict['caps'][x_loc * 2].get_ydata()[0])),
                 (x_loc + 1 + x_offset, bpdict['caps'][x_loc * 2].get_ydata()[0]), **annotate_params)
    plt.annotate('       95%: ' + str("{:.2f}".format(bpdict['caps'][(x_loc * 2) + 1].get_ydata()[0])),
                 (x_loc + 1 + x_offset, bpdict['caps'][(x_loc * 2) + 1].get_ydata()[0]), **annotate_params)
