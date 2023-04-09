#!/bin/python3

from worker import Worker

class WorkerConfig:
    def __init__(self, seed, n_reqs, interarrival_time, random_distr, execution_time, action):
        self.interarrival_time = interarrival_time
        self.random_distr = random_distr
        self.execution_time = execution_time
        self.n_reqs = n_reqs
        self.action = action
        self.seed = seed
        
    def __mul__(self, other: int):
        return [self for x in range(0,other)]
    def __add__(self, other):
        if isinstance(other, list): return [self] + other
        if isinstance(other, WorkerConfig):
            result = [self]
            result.append(other)
            return result
   
def launchScenario(config):
    if isintance(config, WorkerConfig):
    	config = [config]	
    workers = [Worker(conf.seed, conf.n_reqs, conf.interarrival_time, conf.random_distr, conf.execution_time, conf.action) for conf in config]
    for worker in workers:
        worker.start()
    
    for worker in workers:
        worker.join()
    print("Ended")
    
    
