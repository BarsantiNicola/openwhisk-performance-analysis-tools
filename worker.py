#!/bin/python3

import subprocess
from subprocess import Popen
from threading import Thread
import time

class Worker(Thread):
    def __init__(self, seed, n_reqs, mean_interarrival_time, iat_distr, mean_execution_time, action):
        Thread.__init__(self)
        self.interarrival_time = mean_interarrival_time
        self.random_iat = iat_distr
        self.execution_time = mean_execution_time
        self.action = action
        self.error = 0
        self.completed = 0
        self.n_reqs = n_reqs
        self.seed = seed
        self.command = "wsk action"
        self.counter = 0
        
    def requestActivationAndWait(self):
        with Popen(["wsk","action", "invoke" , self.action, "-ir"],  stdout=subprocess.PIPE) as proc:
                result = proc.stdout.read().decode("utf-8")
                if "error" in result or len(result) == 0: 
                    self.error +=1
                else:
                    self.completed +=1

    def compute_time(self):
         return self.interarrival_time
    
    def run(self):
        while(self.counter<self.n_reqs):
            self.requestActivationAndWait()
            self.counter+=1
            time.sleep(self.compute_time())
        print("Test completed. Success: " + str(self.completed) + " Failures: " + str(self.error) )     
            