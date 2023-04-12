# Openwhisk Hierarchical Schedule Performance Tool

OpenWhisk is a serverless functions platform for building cloud applications.
OpenWhisk offers a rich programming model for creating serverless APIs from functions,
composing functions into serverless workflows, and connecting events to functions using rules and triggers.
Learn more at [http://openwhisk.apache.org](http://openwhisk.apache.org).<br>  
Moreover our implementation consist into a plugin that enables a new kind of scheduling based
on two level of management for both the containers and requests:
- a first level of scheduling based on the concept of policies which uses only local information available to the MemoryQueue:
  - required minWorkers to assign to the MemoryQueue
  - required maxWorkers to assign to the MemoryQueue
  - required readyWorkers(workers ready to process a request) to be maintained by the MemoryQueue
  - a policy behavior(asRequested, steps, poly, inversePoly..) which defines how the containers has to be assigned for the containers, and the requests has to be accepted by the service(AcceptAll, RejectAll, AcceptTill, AcceptEvery)
- an upper level of scheduling which uses global information for piloting the lower level scheduling by changing the policies applied and the parameters<br>  
Learn more at http://github.com/BarsantiNicola/openwhisk-trackedPlugin

# How it works
The tool uses spawns a set of thread for execute requests to the service accordingly to a given configuration, you will be required to create a list
of configurations, then the tool will create an agent for every configuration. After the stimulation of the service it will then
collect locally all the logs produced by the service on the machines hosting the service. Finally it will parse all the logs
to extract the metrics produces and stores them into mongoDb(also returns them to you).

# Getting Started

This repository contains a simple tool for make performance analysis on our solution, to use it a set of manual steps is required:
- you need to add the content of the scripts directory in the /root directory of the kubernetes workers.
- you need to change the content of the scripts by adding the hostname of the machine hosting the tool
- you need to enable ssh communication without password requests(see ssh using RSA keys)
- you need to deploy a mongo database
- you need to install python3 and pip
- you need to install via pip the numpy library
<br>  
After have satisfied these requirements you are able to use the tool by using the
scenario.py script:
- create one or more WorkerConfig
- use the launch_scenario function which will require a set of information:
  - network information to reach the mongoDb instance
  - a name to be assigned to the analysis, this must be unique for keeping separated the results of the execution
If the same name is already being used, it will not launch the execution. The name is used to store the log files(directory name) and the results on mongoDb(collection name)
  - the worker configuration, each configuration correspond to a parallel worker