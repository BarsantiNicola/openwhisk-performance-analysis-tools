import math
import os

import basics_tool
import numpy as np
from matplotlib import pyplot as plt

from mongo_connection import mongo_connection


def extract_containers(data: list[dict]) -> ((list, list), (list, list)):
    unused = [], []
    availables = [], []
    print("[Container-Analysis] Extracting needed information from stored data...", end="")

    for d in data:
        available = d["containers"]
        unrequired = d["ready"]
        availables[0].append(d["timestamp"])
        availables[1].append(available)
        unused[0].append(d["timestamp"])
        unused[1].append(unrequired)

    normalized_timestamps_a = []
    normalized_timestamps_u = []
    m_a = min(availables[0])
    m_u = min(unused[0])
    normalized_timestamps_a.append([d - m_a for d in availables[0]])
    normalized_timestamps_u.append([d - m_u for d in unused[0]])
    print("done!")
    return (normalized_timestamps_a, availables[1]), (normalized_timestamps_u, unused[1])


def analyze_exp3(path: str, host, port, db_name, tags: list[str], identificators: list[int]):
    a_results: [tuple[list, list]] = []
    u_results: [tuple[list, list]] = []
    for tag in tags:
        a_values = []
        u_values = []
        a_ci = []
        u_ci = []
        for identificator in identificators:
            print("[ResponseTime-Analysis] Starting data extraction from mongoDb...", end="")
            if tag == "115" and identificator > 500:
                client = mongo_connection(host, port, db_name,
                                          "exp2_3_worker_" + tag + "_et_" + str(
                                              identificator) + "_time_500ms_rep_10000",
                                          True)
            else:
                client = mongo_connection(host, port, db_name,
                                          "exp3_worker_" + tag + "_et_" + str(identificator) + "_time_500ms_rep_10000",
                                          True)
            data = client.fetch_data("supervisor_info")
            print("done!")
            client.client.close()
            available, unused = extract_containers(data)
            a_steady = basics_tool.steady_state(available[1])
            u_steady = basics_tool.steady_state(unused[1])
            print(str(a_steady) + ":" + str(len(available[1])))
            print(str(u_steady) + ":" + str(len(available[1])))
            _, a_independent_values = basics_tool.subsample_to_independence(
                available[1][a_steady:], available[1][a_steady:], 0.99)
            _, u_independent_values = basics_tool.subsample_to_independence(
                unused[1][u_steady:], unused[1][u_steady:], 0.99)

            a_values.append(basics_tool.list_mean(a_independent_values))
            u_values.append(basics_tool.list_mean(u_independent_values))
            a_ci.append(basics_tool.ci(a_independent_values, 0.99))
            u_ci.append(basics_tool.ci(u_independent_values, 0.99))
        a_results.append((a_values, a_ci))
        u_results.append((u_values, u_ci))
    print(str(a_results))
    plot_multivalues(path, "available.png", identificators, a_results, tags, "Execution Time(ms)")
    plot_multivalues(path, "unused.png", identificators, u_results, tags, "Execution Time(ms)")


def analyze_exp4(path: str, host, port, db_name, tags: list[str]):
    a_results: [tuple[list, list]] = []
    u_results: [tuple[list, list]] = []
    for tag in tags:
        a_values = []
        u_values = []
        a_ci = []
        u_ci = []
        for num in range(1, 6):
            print("[ResponseTime-Analysis] Starting data extraction from mongoDb...", end="")
            client = mongo_connection(host, port, db_name,
                                      "exp3_worker_" + tag + "_clients_" + str(num) + "_et_450ms_time_500ms", True)
            data = client.fetch_data("supervisor_info")
            print("done!")
            client.client.close()
            available, unused = extract_containers(data)
            a_steady = basics_tool.steady_state(available[1])
            u_steady = basics_tool.steady_state(unused[1])
            print(str(a_steady) + ":" + str(len(available[1])))
            print(str(u_steady) + ":" + str(len(available[1])))
            _, a_independent_values = basics_tool.subsample_to_independence(
                available[1][a_steady:], available[1][a_steady:], 0.99)
            _, u_independent_values = basics_tool.subsample_to_independence(
                unused[1][u_steady:], unused[1][u_steady:], 0.99)

            a_values.append(basics_tool.list_mean(a_independent_values))
            u_values.append(basics_tool.list_mean(u_independent_values))
            a_ci.append(basics_tool.ci(a_independent_values, 0.99))
            u_ci.append(basics_tool.ci(u_independent_values, 0.99))
        a_results.append((a_values, a_ci))
        u_results.append((u_values, u_ci))
    print(str(a_results))
    plot_multivalues(path, "available.png", list(range(1, 6)), a_results, tags, "Parallel Clients")
    plot_multivalues(path, "unused.png", list(range(1, 6)), u_results, tags, "Parallel Clients")


def graph_container_state(path: str, client: mongo_connection) -> list[dict]:
    print("[Container-Analysis] Creating needed directoris into " + path + "...", end="")
    containers_path = path + "/containers"
    os.system("mkdir -p " + containers_path)
    print("done!")
    print("[Container-Analysis] Starting result analysis")
    results = []
    snapshots = client.fetch_data("supervisor_info")
    available, unused = extract_containers(snapshots)
    results.append(container_single_analysis("available containers", available[0], available[1], containers_path))
    results.append(container_single_analysis("unused containers", unused[0], unused[1], containers_path))
    print("[Container-Analysis] Result analysis completed. Results stored into " + containers_path)
    return results


def container_single_analysis(title: str, timestamp: list, data: list, path: str) -> dict:
    print("[Container-Analysis] --> Started analysis of " + title + "...", end="")
    plot_values(title + " values", path, timestamp, data)
    bars = plot_epmf(title + " epmf", path, data)
    print("done!")
    return {
        "mean": basics_tool.list_mean(data),
        "ci": basics_tool.ci(data, 0.99),
        "median": basics_tool.list_median(data),
        "var": basics_tool.list_var(data),
        "std": basics_tool.list_std(data),
        "type": title,
        "bars": str(bars)
    }


def plot_values(t: str, path: str, timestamps: list, values: list):
    plt.scatter(timestamps, values)
    plt.xlabel('Time(clock)', fontsize=14)
    plt.ylabel('N.Containers', fontsize=14)
    plt.savefig(path + "/" + t, dpi=100, bbox_inches='tight')
    plt.clf()


def plot_epmf(t: str, path: str, values: list):
    weights = np.ones_like(values) / len(values)
    ig, ax = plt.subplots(figsize=(16, 10))
    counts, _, bars = ax.hist(values, 30, color="lightblue", ec="blue", weights=weights)
    counter = 0
    for rect in ax.patches:
        height = rect.get_height()
        if counts[counter] > 0:
            ax.annotate("{:.2f}".format(round(counts[counter], 2)), xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 5), textcoords='offset points', ha='center', va='bottom')
        counter += 1
    plt.ylabel('Probability', fontsize=14)
    plt.xlabel('N.Containers', fontsize=14)
    plt.savefig(path + "/" + t, dpi=1000, bbox_inches='tight')
    plt.clf()
    return counts


def plot_multivalues(path: str, title: str, tags: list[int], values: list[tuple[list, list]], legend: list[str],
                     x_label: str):
    colors = ['b', 'm', 'c', 'g', 'y', 'k', 'w']
    stringed_legend = []
    max_value = 0
    min_value = -1
    for l in legend:
        stringed_legend.append("readyW: " + str(l[0]) + " minW: " + str(l[1]) + " maxW: " + str(l[2]))
    for index in range(0, len(values)):
        min_ci = []
        max_ci = []
        for i in range(0, len(values[index][0])):
            max_ci.append(values[index][0][i] + values[index][1][i])
            min_ci.append(values[index][0][i] - values[index][1][i])
        M = max(max_ci)
        m = min(min_ci)
        if M > max_value:
            max_value = M
        if m < min_value or min_value == -1:
            min_value = m

        plt.plot(tags, values[index][0], color=colors[index], label=stringed_legend[index])
        # plt.errorbar(tags, values[index][0], yerr=values[index][1], fmt="o", color="r")
        plt.plot(tags, max_ci, color=colors[index], linestyle='dashed')
        plt.plot(tags, min_ci, color=colors[index], linestyle='dashed')
        plt.fill_between(tags, min_ci, max_ci, alpha=0.2, color=colors[index])
        plt.ylabel('Containers', fontsize=14)
        plt.xlabel(x_label, fontsize=14)
    plt.legend(loc="upper left")
    plt.ylim(0, max_value + math.floor(max_value * 0.5))
    plt.grid()
    plt.savefig(path + "/" + title, dpi=1000, bbox_inches='tight')
    plt.clf()
