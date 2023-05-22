import subprocess
from math import floor
from multiprocessing.pool import ThreadPool
from subprocess import Popen
from threading import Thread
import time
import numpy

from mongo_connection import mongo_connection

"""
Thread for executing requests to a remote openwhisk service. It expects:
 - a wsk client available as a command
 - an auth apikey already set into the wsk client
 parameters:
     @seed int: seed by which initialize the source of randomisation
     @n_reqs int: number of requests to perform before shut down
     @mean_inter_arrival_time int: time expressed into milliseconds which represents the mean time between requests
     @iat_distribution string: distribution to be applied. 
                                Available values:
                                  - "constant": no randomisation, the mean inter-arrival time is used as a constant
                                  - "exponential": samples taken from an exponential distribution
                                  - "gaussian": samples taken from a uniform distribution
     @mean_execution_time int: mean time in milliseconds of the action execution
     @action string: name of the action to be executed                                                      
"""


class TracedWorker(Thread):
    def __init__(
            self,
            worker_id: int,
            client: mongo_connection,
            limit: int,
            trace: list[tuple[float,int]],
            action: str):

        Thread.__init__(self)
        self.limit = limit
        self.action = action
        self.trace = trace
        self.error = 0  # number of errors encountered
        self.completed = 0  # number of completed requests
        self.counter = 0
        self.client = client
        self.worker_id = "test-worker" + str(worker_id)
        self.ready = False
        self.pool = ThreadPool(processes=10)

    # thread behavior, will just make a request to openwhisk, wait for the response and evaluate it and repeat until
    # all the required requests are made
    def run(self):

        while self.ready is False:
            pass
        current_time = 0
        for t in self.trace:
            if self.ready is False:
                break
            time.sleep(abs((t[0]-current_time)/1000))
            current_time = t[0]
            self.counter += 1
            self.request_and_wait(t[1])

        print("Test completed. Success: " + str(self.completed) + " Failures: " + str(self.error))

    def go(self):
        self.ready = True

    def stop(self):
        self.ready = False

    # function to perform a request to openwhisk via wsk and wait its result
    def request_and_wait(self, et: int):
        start = time.time() * 1000
        with Popen(["wsk", "action", "invoke", self.action, "-ir", "--param", "time", str(min(19000, et))],
                   stdout=subprocess.PIPE) as proc:
            result = proc.stdout.read().decode("utf-8")
            if "error" in result or len(result) == 0:
                self.error += 1
            else:
                self.completed += 1
        end = time.time() * 1000
        self.client.insert_one(
            {
                "timestamp": end,
                "response_time": end - start,
                "kind": "global_response_time",
                "action": self.action,
                "actor": self.worker_id
            })


class Worker(Thread):
    def __init__(
            self,
            worker_id: int,
            client: mongo_connection,
            seed: int,
            n_reqs: int,
            mean_inter_arrival_time: float,
            iat_distribution: str,
            mean_execution_time: float,
            et_distribution: str,
            action: str):

        Thread.__init__(self)
        self.local_random_generator = numpy.random.RandomState(seed)
        self.mean_inter_arrival_time = mean_inter_arrival_time
        self.iat_distribution = iat_distribution
        self.et_distribution = et_distribution
        self.mean_execution_time = mean_execution_time
        self.n_reqs = n_reqs
        self.action = action
        self.error = 0  # number of errors encountered
        self.completed = 0  # number of completed requests
        self.counter = 0
        self.client = client
        self.worker_id = "test-worker" + str(worker_id)
        self.ready = False
        self.pool = ThreadPool(processes=10)

    # function to perform a request to openwhisk via wsk and wait its result
    def request_and_wait(self):
        start = time.time() * 1000
        with Popen(["wsk", "action", "invoke", self.action, "-ir", "--param", "time", str(min(19000, self.compute_et_time()))],
                   stdout=subprocess.PIPE) as proc:
            result = proc.stdout.read().decode("utf-8")
            if "error" in result or len(result) == 0:
                self.error += 1
            else:
                self.completed += 1
        end = time.time() * 1000
        self.client.insert_one(
            {
                "timestamp": end,
                "response_time": end - start,
                "kind": "global_response_time",
                "action": self.action,
                "actor": self.worker_id
            })

    # function to compute a random sample accordingly the given mean_inter_arrival_time and iat_distribution
    def compute_iat_time(self):
        match self.iat_distribution:
            case "constant":
                return self.mean_inter_arrival_time
            case "exponential":
                return abs(self.local_random_generator.exponential(self.mean_inter_arrival_time))
            case "gaussian":
                return abs(self.local_random_generator.normal(self.mean_inter_arrival_time))
            case _:
                return self.mean_inter_arrival_time

    # function to compute a random sample accordingly the given mean_execution_arrival_time and et_distribution
    def compute_et_time(self):
        match self.et_distribution:
            case "constant":
                return self.mean_execution_time
            case "exponential":
                return int(abs(floor(self.local_random_generator.exponential(self.mean_execution_time))))
            case "gaussian":
                return int(abs(floor(self.local_random_generator.normal(self.mean_execution_time))))
            case _:
                return self.mean_execution_time

    # thread behavior, will just make a request to openwhisk, wait for the response and evaluate it and repeat until
    # all the required requests are made
    def run(self):

        while self.ready is False:
            pass

        while self.counter < self.n_reqs:
            self.pool.apply_async(self.request_and_wait)
            self.counter += 1
            time.sleep(self.compute_iat_time())
        print("Test completed. Success: " + str(self.completed) + " Failures: " + str(self.error))

    def go(self):
        self.ready = True
