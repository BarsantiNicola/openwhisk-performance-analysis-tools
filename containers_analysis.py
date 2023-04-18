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
        required = d["enqueued"]
        availables[0].append(d["timestamp"])
        availables[1].append(available)
        unused[0].append(d["timestamp"])
        if available - required >= 0:
            unused[1].append(available - required)
        else:
            unused[1].append(0)

    normalized_timestamps_a = []
    normalized_timestamps_u = []
    m_a = min(availables[0])
    m_u = min(unused[0])
    normalized_timestamps_a.append([d - m_a for d in availables[0]])
    normalized_timestamps_u.append([d-m_u for d in unused[0]])
    print("done!")
    return (normalized_timestamps_a, availables[1]), (normalized_timestamps_u, unused[1])


def graph_container_state(path: str, client: mongo_connection) -> list[dict]:
    print("[Container-Analysis] Creating needed directoris into " + path + "...", end="")
    containers_path = path + "/containers"
    os.system("mkdir -p " + containers_path)
    print("done!")
    print("[Container-Analysis] Starting result analysis")
    results = []
    snapshots = client.fetch_data("supervisor_info")
    available, unused = extract_containers(snapshots)
    timestamps, available = basics_tool.subsample_to_independence(available[0], available[1], 0.99)
    timestamps2, unused = basics_tool.subsample_to_independence(unused[0], unused[1], 0.99)
    results.append(container_single_analysis("available containers", timestamps, available, containers_path))
    results.append(container_single_analysis("unused containers", timestamps2, unused, containers_path))
    print("[Container-Analysis] Result analysis completed. Results stored into " + containers_path)
    return results


def container_single_analysis(title: str, timestamp: list, data: list, path: str) -> dict:
    print("[Container-Analysis] --> Started analysis of " + title + "...", end="")
    plot_values(title + " values", path, timestamp, data)
    plot_epmf(title + " epmf", path, data)
    print("done!")
    return {
        "mean": basics_tool.list_mean(data),
        "ci": basics_tool.ci(data, 0.99),
        "median": basics_tool.list_median(data),
        "var": basics_tool.list_var(data),
        "std": basics_tool.list_std(data),
        "type": title
    }


def plot_values(t: str, path: str, timestamps: list, values: list):
    plt.scatter(timestamps, values)
    plt.xlabel('Time(clock)', fontsize=14)
    plt.ylabel('N.Containers', fontsize=14)
    plt.savefig(path + "/" + t, dpi=100, bbox_inches='tight')
    plt.clf()


def plot_epmf(t: str, path: str, values: list):
    mean = basics_tool.list_mean(values)
    weights = np.ones_like(values) / len(values)
    plt.hist(values, 30, color="lightblue", ec="blue", weights=weights)
    plt.ylabel('Probability', fontsize=14)
    plt.xlabel('N.Containers', fontsize=14)
    plt.annotate('Mean: ' + str(mean), xy=(mean, 1.2))
    plt.savefig(path + "/" + t, dpi=100, bbox_inches='tight')
    plt.clf()
