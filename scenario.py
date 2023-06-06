import random
import subprocess
import time
from datetime import datetime
from json import JSONDecodeError
from math import floor
from time import sleep

import azure_dataset
import response_time
from burst_worker import BurstWorker
from mongo_connection import mongo_connection
from worker import Worker, TracedWorker
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
        self.inter_arrival_time =  inter_arrival_time
        self.random_distribution = random_distribution
        self.execution_time =      execution_time
        self.n_reqs =              n_reqs
        self.et_distribution =     et_distribution
        self.action =              action

    def __mul__(self, other: int):
        return [self for _ in range(0, other)]

    def __add__(self, other):
        if isinstance(other, list):
            return [self] + other
        if isinstance(other, WorkerConfig):
            return [self, other]


class BurstWorkerConfig:
    def __init__(self, n_burst: int, burst_size: int, burst_inter_arrival_time: int, random_distribution: str,
                 execution_time: int,
                 et_distribution: str,
                 action: str):
        self.n_bursts =                 n_burst
        self.burst_size =               burst_size
        self.burst_inter_arrival_time = burst_inter_arrival_time
        self.burst_iat_distribution =   random_distribution
        self.mean_execution_time =      execution_time
        self.et_distribution =          et_distribution
        self.action =                   action

    def __mul__(self, other: int):
        return [self for _ in range(0, other)]

    def __add__(self, other):
        if isinstance(other, list):
            return [self] + other
        if isinstance(other, WorkerConfig):
            return [self, other]

class TracedWorkerConfig:
    def __init__(self, limit: int, trace: list[tuple[float,int]], action: str, azure_action: str):
        self.limit = limit
        self.trace = trace
        self.action = action
        self.azure_action = azure_action

    def __mul__(self, other: int):
        return [self for _ in range(0, other)]

    def __add__(self, other):
        if isinstance(other, list):
            return [self] + other
        if isinstance(other, TracedWorkerConfig):
            return [self, other]
def launch_traced_scenario(
        init_seed: int,
        db_addr: str,
        db_port: int,
        db_name: str,
        db_collection: str,
        n_actions: int,
        offset: int,
        duration: int,
        trace_path: str
):
    numpy.random.seed(init_seed)

    try:
        client = mongo_connection(db_addr, db_port, db_name, db_collection)
    except UnboundLocalError as error:
        print(error.name)
        return

    initial_timestamp = get_initial_time()
    actions = azure_dataset.retrieve(trace_path)[offset:offset+n_actions]

    config = []
    counter = 0
    for action in actions:
        config.append(TracedWorkerConfig(duration, action["trace"], "taskJS" + str(counter), action["name"]))
        counter += 1
    launch_traced(config, client)
    print("Test Execution completed! Waiting the system to be cleaned")
    time.sleep(600)
    print("Starting results extraction")
    scenario_name = db_name + "_" + db_collection
    extract_results(scenario_name)
    result = parse_merge_and_store("/home/ubuntu/results/" + scenario_name, initial_timestamp, client)
    print("Result extraction completed(" + str(
        len(result)) + " . Values already stored inside mongoDb at " + db_addr + ":" + str(
        db_port) + "(" + db_name + " -> " + db_collection + ")")
    return result

def launch_natural_scenario(
    init_seed: int,
    db_addr: str,
    db_port: int,
    db_name: str,
    db_collection: str,
    n_actions: int,
    n_reqs_per_action: int,
    user_to_iot_ratio: float,
    trace_path:str):

    if user_to_iot_ratio > 1 or user_to_iot_ratio < 0:
        print("Error, user_to_iot_ratio must be in 0,1 interval")
        return

    numpy.random.seed(init_seed)

    try:
        client = mongo_connection(db_addr, db_port, db_name, db_collection)
    except UnboundLocalError as error:
        print(error.name)
        return

    initial_timestamp = get_initial_time()
    actions = azure_dataset.retrieve(trace_path)[:n_actions]

    config = []
    counter = 0
    for action in actions:
        if random.uniform(0,1) > user_to_iot_ratio:
            print("Creating IOT action " + str(counter)+" duration: " + str(action["duration"]) + " iat: " + str(action["iat"]))
            config.append(WorkerConfig(n_reqs_per_action, action["iat"], "gaussian", action["duration"], "gaussian", "taskJS"+str(counter)))
        else:
            print("Creating USER action " + str(counter)+" duration: " + str(action["duration"]) + " iat: " + str(action["iat"]))
            config.append(WorkerConfig(n_reqs_per_action, action["iat"], "exponential", action["duration"], "exponential", "taskJS"+str(counter)))
        counter += 1
    launch_smooth(config, client)

    print("Test Execution completed! Starting results extraction")
    scenario_name = db_name + "_" + db_collection
    extract_results(scenario_name)
    result = parse_merge_and_store("/home/ubuntu/results/" + scenario_name, initial_timestamp, client)
    print("Result extraction completed(" + str(
        len(result)) + " . Values already stored inside mongoDb at " + db_addr + ":" + str(
        db_port) + "(" + db_name + " -> " + db_collection + ")")
    return result


def launch_scenario(
        init_seed: int,
        db_addr: str,
        db_port: int,
        db_name: str,
        db_collection: str,
        config: WorkerConfig | list[WorkerConfig] | BurstWorkerConfig | list[BurstWorkerConfig]):
    if isinstance(config, WorkerConfig) or isinstance(config, BurstWorkerConfig):
        config = [config]
    numpy.random.seed(init_seed)
    
    try:
        client = mongo_connection(db_addr, db_port, db_name, db_collection)
    except UnboundLocalError as error:
        print(error.name)
        return

    initial_timestamp = get_initial_time()
    if isinstance(config[0], WorkerConfig):
        launch_smooth(config, client)
    else:
        launch_burst(config, client)

    print("Test Execution completed! Starting results extraction")
    scenario_name = db_name + "_" + db_collection
    extract_results(scenario_name)
    result = parse_merge_and_store("/home/ubuntu/results/" + scenario_name, initial_timestamp, client)
    print("Result extraction completed(" + str(
        len(result)) + " . Values already stored inside mongoDb at " + db_addr + ":" + str(
        db_port) + "(" + db_name + " -> " + db_collection + ")")
    return result


def launch_multi_scenario(
        init_seed: int,
        db_addr: str,
        db_port: int,
        db_name: str,
        db_collection: str,
        config: WorkerConfig | list[WorkerConfig],
        repetition: int,
        delay: int):
    if isinstance(config, WorkerConfig):
        config = [config]
    numpy.random.seed(init_seed)

    try:
        client = mongo_connection(db_addr, db_port, db_name, db_collection)
    except UnboundLocalError as error:
        print(error.name)
        return

    initial_timestamp = get_initial_time()
    for conf in config:
        for _ in range(0, repetition):
            launch_smooth([conf], client)
            time.sleep(delay)

    print("Test Execution completed! Starting results extraction")
    scenario_name = db_name + "_" + db_collection
    extract_results(scenario_name)
    result = parse_merge_and_store("/home/ubuntu/results/" + scenario_name, initial_timestamp, client)
    print("Result extraction completed(" + str(
        len(result)) + " . Values already stored inside mongoDb at " + db_addr + ":" + str(
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

    print("N.Workers on launch: " + str(len(workers)))

    for worker in workers:
        worker.start()

    for worker in workers:
        worker.go()
        sleep(delay)

    for worker in workers:
        worker.join()


def launch_traced(config: list[TracedWorkerConfig], client: mongo_connection):
    workers = [
        TracedWorker(
            index,
            client,
            config[index].limit,
            config[index].trace,
            config[index].action,
            config[index].azure_action
        ) for index in range(0, len(config))]

    for worker in workers:
        worker.start()

    time.sleep(15)

    for worker in workers:
        worker.go()

    time.sleep(config[0].limit)

    for worker in workers:
        worker.stop()

    for worker in workers:
        worker.join()

def load_scenario(conf_file: str):
    os.system("scp " + conf_file + " ubuntu@kube-control-plane-0:/home/ubuntu/openwhisk_cluster.yaml")
    os.system("ssh ubuntu@kube-control-plane-0 '/home/ubuntu/uninstall_cluster'")
    time.sleep(120)
    os.system("ssh ubuntu@kube-control-plane-0 '/home/ubuntu/spawn_cluster'")
    time.sleep(300)
    os.system("ssh ubuntu@kube-control-plane-0 '/home/ubuntu/create_actions 10 Consolidate'")

def launch_burst(config: list[BurstWorkerConfig], client: mongo_connection):
    workers = [
        BurstWorker(
            index,
            client,
            floor((numpy.random.rand() * 1000)),
            config[index].n_bursts,
            config[index].burst_size,
            config[index].burst_inter_arrival_time,
            config[index].burst_iat_distribution,
            config[index].mean_execution_time,
            config[index].et_distribution,
            config[index].action
        ) for index in range(0, len(config))]

    for worker in workers:
        worker.start()

    for worker in workers:
        worker.go()

    for worker in workers:
        worker.join()


def extract_results(scenario_name: str) -> None:
    os.system("mkdir -p /home/ubuntu/results/" + scenario_name + "/invoker")
    os.system("mkdir -p /home/ubuntu/results/" + scenario_name + "/scheduler")
    os.system("mkdir -p /home/ubuntu/results/" + scenario_name + "/controller")
    os.system("ssh root@kube-worker-0 '/root/extractor.sh' 2> /dev/null")
    os.system("ssh root@kube-worker-2 '/root/extractor.sh' 2> /dev/null")
    os.system("ssh root@kube-worker-3 '/root/extractor.sh' 2> /dev/null")
    os.system("ssh root@kube-worker-5 '/root/extractor.sh' 2> /dev/null")
    os.system("ssh root@kube-worker-6 '/root/extractor.sh' 2> /dev/null")
    os.system("ssh root@kube-worker-7 '/root/extractor.sh' 2> /dev/null")
    os.system("mv /home/ubuntu/results/loaded/scheduler/* /home/ubuntu/results/" + scenario_name + "/scheduler")
    os.system("mv /home/ubuntu/results/loaded/invoker/* /home/ubuntu/results/" + scenario_name + "/invoker")
    os.system("mv /home/ubuntu/results/loaded/controller/* /home/ubuntu/results/" + scenario_name + "/controller")


def convert_timestamp(time: str) -> datetime:
    result = time[time.rfind("[")+1:time.rfind("Z") - 1]
    try:
        return datetime.strptime(result, "%Y-%m-%dT%H:%M:%S.%f")
    except:
        return datetime.fromtimestamp(0)

def get_initial_time() -> datetime:
    result1 = subprocess.run(["ssh", "root@kube-worker-0", "'/root/timer.sh'"], stdout=subprocess.PIPE)
    return convert_timestamp(result1.stdout.decode("utf-8"))


def extract_timestamp(line: str) -> datetime:
    try:
        return convert_timestamp(line[line.find("["):line.find("]")])
    except ValueError:
        return datetime.fromtimestamp(0)


def parse_merge_and_store(global_directory_path: str, initial_timestamp: datetime, client: mongo_connection) -> \
        list[dict]:
    parse_controller(global_directory_path + "/controller", initial_timestamp, client)
    scheduler_pending = parse_and_store(global_directory_path + "/scheduler", initial_timestamp, client)
    invoker_pending = parse_and_store(global_directory_path + "/invoker", initial_timestamp, client)
    resolved_pending = []
    print("Starting result merging")
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
                        "timestamp": s_pending["time"],
                        "activation_id": s_pending["activation_id"]
                    }
                )
                invoker_pending[0].remove(i_pending)
                break
    print("Merging concluded: " + str(len(resolved_pending)))
    if len(resolved_pending) > 0:
        client.insert_many(resolved_pending)
    response_time.create_normalized_response_time(client)
    return resolved_pending + scheduler_pending[1] + invoker_pending[1]


def parse_controller(directory_path: str, initial_timestamp: datetime, client: mongo_connection) -> None:
    files = [join(directory_path, f) for f in listdir(directory_path) if isfile(join(directory_path, f))]
    activations = []
    terminations = []
    resolved = []
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
                    if header_index > 0:
                        line = line[header_index:]
                        content_index = line.find("{")
                        try:
                            content = json.loads(line[content_index:line.find("}")+1].replace("'", "\""))
                            if content["event"] == "activation_published":
                                activations.append(content)
                            else:
                                terminations.append(content)
                        except JSONDecodeError:
                            pass

    for termination in terminations:
        for activation in activations:
            if termination["activation_id"] == activation["activation_id"]:
                resolved.append(
                    {
                        "kind": "service_response_time",
                        "response_time": termination["time"] - activation["time"],
                        "action": activation["action"],
                        "namespace": activation["namespace"],
                        "timestamp": activation["time"],
                        "activation_id": activation["activation_id"]
                    }
                )
                activations.remove(activation)
                break
    if len(resolved) > 0:
        client.insert_many(resolved)


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
                        line = line[header_index:]
                        content_index = line.find("{")
                        header = line[:content_index]
                        try:
                            content = json.loads(line[content_index:line.find("}")+1].replace("'", "\""))
                            if "[Data]" in line:
                                if "incomingMsgCount" in content:
                                    content = {
                                        "kind": "snapshot-info",
                                        "incomingMsgCount": int(content["incomingMsgCount"]),
                                        "currentMsgCount": int(content["currentMsgCount"]),
                                        "staleActivationNum": int(content["staleActivationNum"]),
                                        "existingContainerCountInNamespace": int(
                                            content["existingContainerCountInNamespace"]),
                                        "inProgressContainerCountInNamespace": int(
                                            content["inProgressContainerCountInNamespace"]),
                                        "averageDuration": float(content["averageDuration"]),
                                        "stateName": content["stateName"],
                                        "timestamp": int(content["timestamp"]),
                                        "iar": int(content["iar"]),
                                        "maxWorkers": int(content["maxWorkers"]),
                                        "minWorkers": int(content["minWorkers"]),
                                        "readyWorkers": int(content["readyWorkers"]),
                                        "containerPolicy": content["containerPolicy"],
                                        "activationPolicy": content["activationPolicy"]
                                    }
                                store.append(content)
                            elif "[Measure]" in line:
                                pending.append(content)
                        except JSONDecodeError:
                            pass
    print("Terminated parsing: " + str(len(store)))
    if len(store) > 0:
        client.insert_many(store)
    return [pending, store]
