from mongo_connection import mongo_connection
from worker import Worker
import numpy

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

    print("Ended")

