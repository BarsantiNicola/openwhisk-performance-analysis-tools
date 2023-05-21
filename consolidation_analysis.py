import math
import os
from typing import List, Tuple, Any

import numpy

import basics_tool
import numpy as np
from matplotlib import pyplot as plt

import containers_analysis
from mongo_connection import mongo_connection


def extract_containers_creation(data: list[dict]) -> (list, list):
    creations = [], []
    print("[Consolidation-Analysis] Extracting needed information from stored data...", end="")

    for d in data:
        creations[0].append(d["timestamp"])
        creations[1].append(d["invoker"])
    print("done!")
    return creations


def extract_containers(data: list[dict]) -> (list, list):
    containers = [], []
    print("[Containers-Analysis] Extracting needed information from stored data...", end="")
    for d in data:
        containers[0].append(d["timestamp"])
        containers[1].append(d["containers"])
    print("done!")
    return containers


def normalize_info(creations: (list, list), containers: (list, list)) -> ((list, list), (list, list)):
    m = min(min(creations[0]), min(containers[0]))
    updated_creations = [timestamp - m for timestamp in creations[0]]
    updated_containers = [timestamp - m for timestamp in containers[0]]
    return (updated_creations, creations[1]), (updated_containers, containers[1])


def split(creations: (list, list), block_size: int) -> list:
    blocks = []
    for n in range(0, math.floor(len(creations[1]) / block_size)):
        blocks.append(
            (creations[0][n * block_size:(n + 1) * block_size], creations[1][n * block_size:(n + 1) * block_size]))
    return blocks


def subsample_blocks(blocks: list) -> list:
    results = []
    for block in blocks:
        results.append(basics_tool.subsample_to_independence(block[0], block[1], 0.99))
    return results


def compute_invokers(blocks: list, n_invoker: int) -> list:
    results = []
    for block in blocks:
        invokers = [0 for _ in range(0, n_invoker)]
        for invoker in block:
            invokers[invoker] += 1
        results.append(invokers)
    return results


def evaluate_mean_and_ci(values: list[list], size: int, block_size: int) -> (list, list):
    splitted = [[] for _ in range(0, size)]
    ci = []
    means = []
    for value in values:
        for index in range(0, len(value)):
            splitted[index].append(value[index] / block_size)
    for index in range(0, len(splitted)):
        means.append(basics_tool.list_mean(splitted[index]))
        ci.append(basics_tool.ci(splitted[index], 0.99))
    return means, ci


def extract_values(blocks: list) -> list:
    result = []
    for block in blocks:
        result.append(block[1])
    return result


def groupByInvoker(values: (list, list), size: int) -> list[tuple[list[Any], list[Any]]]:
    results = []

    for index in range(0, size):
        res = []
        ci = []
        for value in values:
            res.append(value[0][index])
            ci.append(value[1][index])
        results.append((res, ci))
    return results


def extract_memory(values: list) -> (list, list):
    timestamps = []
    ret_values = []
    setted = 0
    for value in values:
        timestamps.append(value["timestamp"])
        val = int(value["memory"])
        ret_values.append(val)
    return timestamps, ret_values


def normalize_series(values: list[tuple[list, list]]) -> (list, list):
    global_min = -1
    for value in values:
        if len(value[0]) > 0:
            m = numpy.min(value[0])
            if global_min == -1 or m < global_min:
                global_min = m
    normalized = []
    for value in values:
        normalized.append(([x - global_min for x in value[0]], value[1]))
    return normalized


def analyze_exp6(path: str, host, port, db_name, tags: list[int], invokers: list[int]):
    for tag in tags:
        client = mongo_connection(host, port, db_name, "exp6_consolidation_size_" + str(tag) + "_rep_50", True)
        series = []
        for invoker in invokers:
            data = client.fetch_data("invokers_memory", invoker)
            series.append(extract_memory(data))
        series = normalize_series(series)
        plot_memory(path + "/memory_" + str(tag) + ".png", "Invokers Usage", series,
                    ["Invoker " + str(invoker) for invoker in invokers])


def analyze_exp6_singles(path: str, host, port, db_name):
    for size in range(1, 40):
        os.system("mkdir -p /home/nico/Scrivania/consolidation/" + str(size))
        if size < 20:
            client = mongo_connection(host, port, db_name, "exp5_consolidation_size_" + str(size) + "_rep_50", True)
        else:
            client = mongo_connection(host, port, db_name, "exp6_consolidation_size_" + str(size) + "_rep_50", True)
        series = []
        for invoker in [0, 1, 2, 3, 4]:
            data = client.fetch_data("invokers_memory", invoker)
            series.append(extract_memory(data))
        series = normalize_series(series)
        for invoker in [0, 1, 2, 3, 4]:
            plot_memory(path + "/" + str(size) + "/memory_" + str(size) + "invoker_" + str(invoker) + ".png",
                        "Invoker " + str(invoker) + " Usage", series[invoker], ["invoker"])


def analyze_real(path: str, host, port, db_name):
    os.system("mkdir -p " + path)
    client = mongo_connection(host, port, db_name, "performance_evaluation_consolidation_10_2h", True)
    print("Extracted data")
    series = []
    for invoker in [0, 1, 2, 3, 4]:
        data = client.fetch_data("invokers_memory", invoker)
        series.append(extract_memory(data))
        print("Data Fetched")
    series = normalize_series(series)
    print("plotting")
    for invoker in [0, 1, 2, 3, 4]:
        plot_memory(path + "/invoker_" + str(invoker) + ".png",
                    "Invoker " + str(invoker) + " Usage", series[invoker], ["invoker"])


def generate(values: (list, list)) -> (list, list):
    final_timestamps = []
    final_values = []
    for i in range(0, len(values[0])):
        if i < len(values[0])-1:
            for a in range(values[0][i], values[0][i + 1] - values[0][i]):
                final_timestamps.append(a)
                final_values.append(values[1][i])
        else:
            final_timestamps.append(values[0][i])
            final_values.append(values[1][i])
    return final_timestamps, final_values


def analyze_exp7_singles(path: str, host, port, db_name):
    for size in range(1, 41):
        os.system("mkdir -p /home/nico/Scrivania/consolidation4/" + str(size))
        if size < 20:
            client = mongo_connection(host, port, db_name, "exp12_consolidation_size_" + str(size) + "_rep_3", True)
        else:
            client = mongo_connection(host, port, db_name, "exp12_consolidation_size_" + str(size) + "_rep_3", True)
        series = []
        for invoker in [0, 1, 2, 3, 4]:
            data = client.fetch_data("invokers_memory", invoker)
            series.append(extract_memory(data))
        series = normalize_series(series)
        for invoker in [0, 1, 2, 3, 4]:
            plot_memory(path + "/" + str(size) + "/memory_" + str(size) + "invoker_" + str(invoker) + ".png",
                        "Invoker " + str(invoker) + " Usage", series[invoker], ["invoker"])


def analize_consolidation(path: str, title: str, host, port, db_name, tags: list[int], invokers: list[str]):
    merged_results = []
    for tag in tags:
        client = mongo_connection(host, port, db_name, "exp5_burst_" + str(tag) + "_iat_5_et_20ms_rep_5000", True)
        data = client.fetch_data("container_creation")
        creations = extract_containers_creation(data)
        blocks = split(creations, 100)
        blocks = subsample_blocks(blocks)
        blocks = extract_values(blocks)
        invokers_values = compute_invokers(blocks, len(invokers))
        merged_results.append(evaluate_mean_and_ci(invokers_values, len(invokers), 100))
    merged_results = groupByInvoker(merged_results, len(invokers))
    plot_multivalues(path, title, tags, merged_results,
                     ["invoker 0", "invoker 1", "invoker 2", "invoker 3", "invoker 4", "invoker 5"], "Burst Size")


def plot_memory(path: str, title: str, values: list[tuple[list, list]], le: list[str]):
    colors = ['b', 'm', 'c', 'g', 'y', 'k', 'w']
    print("ok")
    if len(values[1]) == 0:
        return
    print("ok2")
    plt.ylabel('Containers', fontsize=14)
    plt.xlabel("Time(ms)", fontsize=14)
    plt.title(title)

    plt.ylim(0, 9)
    #plt.xlim(0,800000)
    plt.plot(values[0], values[1], color=colors[0])
    print("Creatingchart")
    plt.savefig(path, dpi=1000, bbox_inches='tight')
    plt.clf()


def plot_multivalues(path: str, title: str, tags: list[int], values: list[tuple[list, list]], legend: list[str],
                     x_label: str):
    colors = ['b', 'm', 'c', 'g', 'y', 'k', 'w']
    max_value = 0
    min_value = -1
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
        print(values)

        plt.plot(tags, values[index][0], color=colors[index], label=legend[index])
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
