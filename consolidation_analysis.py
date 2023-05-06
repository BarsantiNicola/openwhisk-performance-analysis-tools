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


def subsample_blocks( blocks: list ) -> list:
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


def evaluate_mean_and_ci(values: list[list], size: int, block_size:int) -> (list,list):
    splitted = [[] for _ in range(0, size)]
    ci = []
    means = []
    for value in values:
        for index in range(0, len(value)):
            splitted[index].append(value[index]/block_size)
    for index in range(0, len(splitted)):
        means.append(basics_tool.list_mean(splitted[index]))
        ci.append(basics_tool.ci(splitted[index], 0.99))
    return means,ci


def extract_values(blocks:list) -> list:
    result = []
    for block in blocks:
        result.append(block[1])
    return result


def groupByInvoker( values: (list,list), size:int) -> list[tuple[list[Any], list[Any]]]:
    results = []

    for index in range(0,size):
        res = []
        ci = []
        for value in values:
            res.append(value[0][index])
            ci.append(value[1][index])
        results.append((res,ci))
    return results


def analize_consolidation(path: str, title: str, host, port, db_name, tags: list[int], invokers: list[str]):
    merged_results = []
    for tag in tags:
        client = mongo_connection(host, port, db_name, "exp5_burst_"+str(tag) + "_iat_5_et_20ms_rep_5000", True)
        data = client.fetch_data("container_creation")
        creations = extract_containers_creation(data)
        blocks = split(creations, 100)
        blocks = subsample_blocks(blocks)
        blocks = extract_values(blocks)
        invokers_values = compute_invokers(blocks, len(invokers))
        merged_results.append(evaluate_mean_and_ci(invokers_values, len(invokers), 100))
    merged_results = groupByInvoker(merged_results, len(invokers))
    plot_multivalues(path, title, tags, merged_results,["invoker 0", "invoker 1", "invoker 2", "invoker 3", "invoker 4", "invoker 5"], "Burst Size")


def plot_multivalues(path: str, title: str, tags: list[int], values: list[tuple[list,list]], legend: list[str],
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