from math import floor

from mongo_connection import mongo_connection
from worker import Worker
import numpy
import os
import json
from os import listdir
from os.path import isfile, join

"""
Configuration for the creation of a worker. Each given configuration represents a worker that will be
executed in parallel. I have overloaded the mathematics operands + and *:
 - config+config/[config]: permits to concatenate two configuration or a configuration and a list of configuration
 - config*n: permits to create a list of n copies of the same configuration
"""


class WorkerConfig:
    def __init__(self, n_reqs, inter_arrival_time: int, random_distribution: str, execution_time: int,
                 et_distribution: str,
                 action: str):
        self.inter_arrival_time = inter_arrival_time
        self.random_distribution = random_distribution
        self.execution_time = execution_time
        self.n_reqs = n_reqs
        self.et_distribution = et_distribution
        self.action = action

    def __mul__(self, other: int):
        return [self for _ in range(0, other)]

    def __add__(self, other):
        if isinstance(other, list):
            return [self] + other
        if isinstance(other, WorkerConfig):
            return [self, other]


def launch_scenario(
        init_seed: int,
        db_addr: str,
        db_port: int,
        db_name: str,
        db_collection: str,
        config: WorkerConfig | list[WorkerConfig]):
    if isinstance(config, WorkerConfig):
        config = [config]
    numpy.random.seed(init_seed)

    try:
        client = mongo_connection(db_addr, db_port, db_name, db_collection)
    except UnboundLocalError as error:
        print(error.name)
        return

    workers = [
        Worker(
            index,
            client,
            floor((numpy.random.rand() * 1000)),
            config[index].n_reqs,
            config[index].inter_arrival_time,
            config[index].random_distribution,
            config[index].execution_time,
            config[index].et_distribution,
            config[index].action
        ) for index in range(0, len(config))]

    for worker in workers:
        worker.start()

    for worker in workers:
        worker.join()

    print("Test Execution completed! Starting results extraction")
    extract_results(db_name + "_" + db_collection)
    parse_and_store(db_name + "_" + db_collection, client)
    print("Ended")


def extract_results(scenario_name: str):
    os.system("mkdir -p /home/ubuntu/results/" + scenario_name + "/invoker")
    os.system("mkdir -p /home/ubuntu/results/" + scenario_name + "/scheduler")
    os.system("ssh root@kube-worker-0 '/root/extractor.sh' 2> /dev/null")
    os.system("ssh root@kube-worker-1 '/root/extractor.sh' 2> /dev/null")
    os.system("mv /home/ubuntu/results/*invoker*.log /home/ubuntu/results/" + scenario_name + "/invoker")
    os.system("mv /home/ubuntu/results/*scheduler*.log /home/ubuntu/results/" + scenario_name + "/scheduler")


def parse_merge_and_store(global_directory_path: str, client: mongo_connection):
    scheduler_pendings = parse_and_store(global_directory_path + "/scheduler", client)
    invoker_pendings = parse_and_store(global_directory_path + "/invoker", client)

def parse_and_store(directory_path: str):
    files = [join(directory_path, f) for f in listdir(directory_path) if isfile(join(directory_path, f))]
    results = []
    store = []
    for file in files:
        with open(file) as f:
            print("parsing file: " + file)
            terminated = True
            while terminated:
                line = f.readline()
                if not line:
                    terminated = False
                else:
                    header_index = line.find("[Framework-Analysis]")
                    if header_index >= 0 and "[Event]" not in line:
                        content_index = line.rfind("{")
                        header = line[header_index:content_index]
                        print(line[content_index:].replace("'", "\""))
                        content = json.loads(line[content_index:].replace("'", "\""))
                        if "[Data]" in header:
                            store.append(content)
                        elif "[Measure]" in header:
                            results.append(content)
    #client.insert_many(store)
    return results
