import subprocess
from datetime import datetime
from math import floor
from time import sleep

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

    initial_timestamp = get_initial_time()
    launch_smooth(config, client)

    print("Test Execution completed! Starting results extraction")
    scenario_name = db_name + "_" + db_collection
    extract_results(scenario_name)
    result = parse_merge_and_store("/home/ubuntu/results/" + scenario_name, initial_timestamp, client)
    print("Result extraction completed. Values already stored inside mongoDb at " + db_addr + ":" + str(
        db_port) + "(" + db_name + " -> " + db_collection + ")")
    return result


def launch_smooth(config: list[WorkerConfig], client: mongo_connection):
    mean_iat = 0
    for conf in config:
        mean_iat += conf.inter_arrival_time
    mean_iat /= len(config)
    delay = mean_iat / len(config)
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
        worker.go()
        sleep(delay)

    for worker in workers:
        worker.join()


def launch_burst(burst_repetition: int, burst_iat: float, burst_reqs: int, execution_time: float, action: str, client: mongo_connection):
    workers = [
        Worker(
            index,
            client,
            floor((numpy.random.rand() * 1000)),
            burst_repetition,
            burst_iat,
            "constant",
            execution_time,
            "constant",
            action
        ) for index in range(0, burst_reqs)]

    for worker in workers:
        worker.start()

    for worker in workers:
        worker.go()

    for worker in workers:
        worker.join()


def extract_results(scenario_name: str) -> None:
    os.system("mkdir -p /home/ubuntu/results/" + scenario_name + "/invoker")
    os.system("mkdir -p /home/ubuntu/results/" + scenario_name + "/scheduler")
    os.system("ssh root@kube-worker-0 '/root/extractor.sh' 2> /dev/null")
    os.system("mv /home/ubuntu/results/loaded/* /home/ubuntu/results/" + scenario_name + "/scheduler")
    os.system("ssh root@kube-worker-1 '/root/extractor.sh' 2> /dev/null")
    os.system("mv /home/ubuntu/results/loaded/* /home/ubuntu/results/" + scenario_name + "/invoker")


def convert_timestamp(time: str) -> datetime:
    result = time[:time.rfind("+") - 3]
    return datetime.strptime(result, "%Y-%m-%dT%H:%M:%S.%f")


def get_initial_time() -> datetime:
    result1 = subprocess.run(["ssh", "root@kube-worker-0", "'/root/timer.sh'"], stdout=subprocess.PIPE)
    result1 = convert_timestamp(result1.stdout.decode("utf-8"))
    result2 = subprocess.run(["ssh", "root@kube-worker-1", "'/root/timer.sh'"], stdout=subprocess.PIPE)
    result2 = convert_timestamp(result2.stdout.decode("utf-8"))
    if result1 > result2:
        return result1
    else:
        return result2


def extract_timestamp(line: str) -> datetime:
    return convert_timestamp(line[:line.find(" ") - 1])


def parse_merge_and_store(global_directory_path: str, initial_timestamp: datetime, client: mongo_connection) -> \
        list[dict]:
    scheduler_pending = parse_and_store(global_directory_path + "/scheduler", initial_timestamp, client)
    invoker_pending = parse_and_store(global_directory_path + "/invoker", initial_timestamp, client)
    resolved_pending = []
    for s_pending in scheduler_pending[0]:
        for i_pending in invoker_pending[0]:
            if s_pending["activation_id"] == i_pending["activation_id"]:
                resolved_pending.append(
                    {
                        "kind": "local_response_time",
                        "response_time": i_pending["time"] - s_pending["time"],
                        "action": s_pending["action"],
                        "namespace": s_pending["namespace"],
                        "state": s_pending["state"],
                        "timestamp": s_pending["time"]
                    }
                )
                invoker_pending[0].remove(i_pending)
                break
    if len(resolved_pending) > 0:
        client.insert_many(resolved_pending)
    return resolved_pending + scheduler_pending[1] + invoker_pending[1]


def parse_and_store(directory_path: str, initial_timestamp: datetime, client: mongo_connection) -> list[list[dict]]:
    files = [join(directory_path, f) for f in listdir(directory_path) if isfile(join(directory_path, f))]
    pending = []
    store = []
    for file in files:
        with open(file) as f:
            print("Parsing file: " + file)
            terminated = True
            while terminated:
                line = f.readline()
                if not line:
                    terminated = False
                elif extract_timestamp(line) >= initial_timestamp:
                    header_index = line.find("[Framework-Analysis]")
                    if header_index > 0 and "[Event]" not in line:
                        content_index = line.rfind("{")
                        header = line[header_index:content_index]
                        content = json.loads(line[content_index:].replace("'", "\""))
                        if "[Data]" in header:
                            store.append(content)
                        elif "[Measure]" in header:
                            pending.append(content)
    if len(store) > 0:
        client.insert_many(store)
    return [pending, store]
