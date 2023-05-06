import math
import os

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


def extract_containers(data: list[dict]) -> (list,list):
    containers = [], []
    print("[Containers-Analysis] Extracting needed information from stored data...", end="")
    for d in data:
        containers[0].append(d["timestamp"])
        containers[1].append(d["containers"])
    print("done!")
    return containers


def normalize_info(creations: (list,list), containers: (list,list)) -> ((list,list),(list,list)):
    m = min(min(creations[0]), min(containers[0]))
    updated_creations = [timestamp-m for timestamp in creations[0]]
    updated_containers = [timestamp-m for timestamp in containers[0]]
    return (updated_creations, creations[1]), (updated_containers, containers[1])


def analize_consolidation(path: str, host, port, db_name, scenario_name: str):
    client = mongo_connection( host, port, db_name, scenario_name, True)
    data = client.fetch_data("container_creation")
    data2 = client.fetch_data("supervisor_info")
    creations = extract_containers_creation(data)
    containers = extract_containers(data2)
    #creations, containers = normalize_info( creations, containers )
    #plt.scatter(containers[0], containers[1])
    #plt.show()
    #plt.clf()
    plt.scatter(creations[0], creations[1])
    plt.show()
    plt.clf()
    invoker_1 = sum(creations[1])
    total = len(creations[1])
    print("Invoker0: " + str((total-invoker_1)/total) + " Invoker1: " + str(invoker_1/total))
