import math

import numpy as np
from matplotlib import pyplot as plt
import numpy
import os
from mongo_connection import mongo_connection
import basics_tool
import pandas as pd
import containers_analysis

def get_value(data:list[dict], id: str):
    for d in data:
        if d["activation_id"] == id:
            return d
    return None

def create_normalized_response_time(client:mongo_connection):
    global_rt = client.fetch_data("client_response_time")
    service_rt = client.fetch_data("service_response_time")
    normalized_service_rt = []
    for srt in service_rt:
        grt = get_value(global_rt,srt["activation_id"])
        normalized_service_rt.append({
            "kind": "normalized_service_time",
            "response_time": srt["response_time"] - grt["duration"],
            "action": srt["action"],
            "namespace": srt["namespace"],
            "timestamp": srt["timestamp"],
            "activation_id": srt["activation_id"]
        })
    client.insert_many(normalized_service_rt)

def extract_response_time(data: list[dict]) -> (list, list, list):
    values = []
    actions = []
    timestamps = []
    print("[ResponseTime-Analysis] Extracting needed information from stored data...", end="")
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
    print("done! " + str(len(values)))
    return actions, normalized_timestamps, values

def analyze_exp4(path: str, host, port, db_name, tags: list[str]):
    results : [tuple[list,list]] = []
    for tag in tags:
        values = []
        ci = []
        for num in range(1,6):
            print("[ResponseTime-Analysis] Starting data extraction from mongoDb ["+tag + ":"+str(num)+"]...", end="")
            client = mongo_connection(host, port, db_name, "exp3_worker_" + tag + "_clients_" + str(num) + "_et_450ms_time_500ms", True)
            data = client.fetch_data("service_response_time")
            print("done!")
            client.client.close()
            actions_client, timestamp_client, values_client = extract_response_time(data)
            steady = basics_tool.steady_state(values_client[0])
            _, independent_values = basics_tool.subsample_to_independence(
                timestamp_client[0][steady:], values_client[0][steady:], 0.99)
            values.append(basics_tool.list_mean(independent_values)-200)
            ci.append(basics_tool.ci(independent_values, 0.99))
        results.append((values, ci))
    plot_multivalues(path+"/response_time_parallel_clients.png", list(range(1,6)), results, tags, "Parallel Clients")
    containers_analysis.analyze_exp4(path, host, port, db_name, tags)

def analyze_exp3(path: str, host, port, db_name, tags: list[str], identificators: list[int]):
    results : [tuple[list,list]] = []
    for tag in tags:
        values = []
        ci = []
        for identificator in identificators:
            print("[ResponseTime-Analysis] Starting data extraction from mongoDb ["+tag + ":"+str(identificator)+"]...", end="")
            if tag == "115" and identificator > 500:
                client = mongo_connection(host, port, db_name,
                                          "exp2_3_worker_" + tag + "_et_" + str(identificator) + "_time_500ms_rep_10000",
                                          True)
            else:
                client = mongo_connection(host, port, db_name, "exp3_worker_" + tag + "_et_" + str(identificator) + "_time_500ms_rep_10000", True)
            data = client.fetch_data("service_response_time")
            print("done!")
            client.client.close()
            actions_client, timestamp_client, values_client = extract_response_time(data)
            steady = basics_tool.steady_state(values_client[0])
            _, independent_values = basics_tool.subsample_to_independence(
                timestamp_client[0][steady:], values_client[0][steady:], 0.99)
            values.append(basics_tool.list_mean(independent_values)-identificator)
            ci.append(basics_tool.ci(independent_values, 0.99))
        results.append((values, ci))
    plot_multivalues(path+"/response_time.png", identificators, results, tags, "Execution Time(ms)")
    containers_analysis.analyze_exp3(path, host, port, db_name, tags, identificators)

def analyze_scenario(host, port, db_name, scenario):
    client = mongo_connection(host, port, db_name, scenario, True)
    print("[ResponseTime-Analysis] Starting data extraction from mongoDb...", end="")
    client_rt = client.fetch_data("client_response_time")
    local_rt = client.fetch_data("minimum_response_time")
    service_rt = client.fetch_data("service_response_time")
    normalized_service_rt = client.fetch_data("normalized_service_time")
    print("done!")

    actions_client, timestamp_client, values_client = extract_response_time(client_rt)
    actions_local, timestamp_local, values_local = extract_response_time(local_rt)
    actions_service, timestamp_service, values_service = extract_response_time(service_rt)
    n_actions_service, n_timestamp_service, n_values_service = extract_response_time(normalized_service_rt)
    results = []
    print("[ResponseTime-Analysis] Starting analysis of client response time...", end="")
    for index in range(0, len(actions_client)):
        steady = basics_tool.steady_state(values_client[index])
        independent_timestamp, independent_values = basics_tool.subsample_to_independence(
            timestamp_client[index][steady:], values_client[index][steady:], 0.99)
        results.append(graph_response_time(timestamp_client[index][steady:], values_client[index][steady:], "/home/nico/Desktop",
                                           scenario + "/client_rt",
                                           actions_client[index]))
    print("done!")
    print("[ResponseTime-Analysis] Starting analysis of minimum response time...", end="")
    for index in range(0, len(actions_local)):
        steady = basics_tool.steady_state(values_local[index])
        independent_timestamp, independent_values = basics_tool.subsample_to_independence(
            timestamp_local[index][steady:], values_local[index][steady:], 0.99)
        results.append(
            graph_response_time(timestamp_local[index][steady:], values_local[index][steady:], "/home/nico/Desktop", scenario + "/local_rt",
                                actions_local[index]))
    print("done!")
    print("[ResponseTime-Analysis] Starting analysis of service response time...", end="")
    for index in range(0, len(actions_service)):
        steady = basics_tool.steady_state(values_service[index])
        independent_timestamp, independent_values = basics_tool.subsample_to_independence(
            timestamp_service[index][steady:], values_service[index][steady:], 0.99)
        results.append(graph_response_time(timestamp_service[index][steady:], values_service[index][steady:], "/home/nico/Desktop",
                                           scenario + "/service_rt",
                                           actions_service[index]))
    print("done!")
    for index in range(0, len(n_actions_service)):
        steady = basics_tool.steady_state(n_values_service[index])
        results.append(graph_response_time(n_timestamp_service[index][steady:], n_values_service[index][steady:], "/home/nico/Desktop",
                                           scenario + "/normalized_service_rt",
                                           actions_service[index]))
    print("done!")
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
        "ci": basics_tool.ci(values, 0.99),
        "median": basics_tool.list_median(values),
        "var": basics_tool.list_var(values),
        "std": basics_tool.list_std(values),
        "action": action,
        "type": scenario_name[scenario_name.rfind("/") + 1:]
    }


def plot_values(t: str, path: str, values: list, timestamps: list):
    plt.scatter(timestamps, values, c=values, cmap="viridis")
    plt.title = "mytitle"
    plt.xlabel('Time(ms)', fontsize=14)
    plt.ylabel('Response Time(ms)', fontsize=14)
    plt.ylim(0, 1000)
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


def plot_multivalues(path: str, tags: list[int], values: list[tuple[list,list]], legend: list[str], x_label: str):
    colors = ['b', 'm', 'c', 'g', 'y', 'k', 'w']
    stringed_legend = []
    max_value = 0
    min_value = -1
    for l in legend:
        stringed_legend.append( "readyW: " + str(l[0]) + " minW: " + str(l[1]) + " maxW: " + str(l[2]))
    for index in range(0, len(values)):
        min_ci = []
        max_ci = []
        for i in range(0, len(values[index][0])):
            max_ci.append(values[index][0][i]+values[index][1][i])
            min_ci.append(values[index][0][i]-values[index][1][i])
        M = max(max_ci)
        m = min(min_ci)
        if M > max_value:
            max_value = M
        if m < min_value or min_value == -1:
            min_value = m

        plt.plot(tags, values[index][0], color=colors[index], label=stringed_legend[index])
        #plt.errorbar(tags, values[index][0], yerr=values[index][1], fmt="o", color="r")
        plt.plot(tags, max_ci, color=colors[index], linestyle='dashed')
        plt.plot(tags, min_ci, color=colors[index], linestyle='dashed')
        plt.fill_between(tags, min_ci, max_ci, alpha=0.2, color=colors[index])
        plt.ylabel('Normalized Response Time(ms)', fontsize=14)
    plt.xlabel(x_label, fontsize=14)
    plt.legend(loc="upper left")
    plt.grid()
    plt.ylim(min_value-abs(math.floor(min_value*0.3)), max_value+math.floor(max_value*0.3))
    plt.savefig(path, dpi=100, bbox_inches='tight')
    plt.clf()
