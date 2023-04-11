from mongo_connection import mongo_connection
from worker import Worker
import numpy
import os

"""
Configuration for the creation of a worker. Each given configuration represents a worker that will be
executed in parallel. I have overloaded the mathematics operands + and *:
 - config+config/[config]: permits to concatenate two configuration or a configuration and a list of configuration
 - config*n: permits to create a list of n copies of the same configuration
"""


class WorkerConfig:
    def __init__(self, n_reqs, inter_arrival_time: int, random_distribution: str, execution_time: int,
                 action: str):
        self.inter_arrival_time = inter_arrival_time
        self.random_distribution = random_distribution
        self.execution_time = execution_time
        self.n_reqs = n_reqs
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
            config.index(conf),
            client,
            numpy.random.rand(),
            conf.n_reqs,
            conf.inter_arrival_time,
            conf.random_distribution,
            conf.execution_time,
            conf.action
        ) for conf in config]

    for worker in workers:
        worker.start()

    for worker in workers:
        worker.join()

    extract_results(db_name + "_" + db_collection)
    parse_and_store(db_name + "_" + db_collection)
    print("Ended")


def extract_results(scenario_name):
    os.system("mkdir -p /home/ubuntu/results/" + scenario_name+"/invoker")
    os.system("mkdir -p /home/ubuntu/results/" + scenario_name+"/scheduler")
    os.system("ssh root@kube-worker-0 '/root/extractor.sh' 2> /dev/null")
    os.system("ssh root@kube-worker-1 '/root/extractor.sh' 2> /dev/null")
    os.system("mv /home/ubuntu/results/*invoker*.log /home/ubuntu/results/"+scenario_name+"/invoker")
    os.system("mv /home/ubuntu/results/*scheduler*.log /home/ubuntu/results/"+scenario_name+"/scheduler")
def parse_and_store(scenario_name):
    return
