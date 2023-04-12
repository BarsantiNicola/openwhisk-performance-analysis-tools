#!/bin/sh

# returns the last timestamp present. It is used before the stimulation to filter the old logs

# KEEP ONLY ONE OF THE TWO COMMANDS BASING ON OPENWHISK LABELS
# for machines hosting the scheduler
sudo tail -n 1 /var/log/pods/openwhisk_owdev-sc*/scheduler/0.log | awk '{print $1}'

# for machines hosting the invoker
sudo tail -n 1 /var/log/pods/openwhisk_owdev-invoker*/invoker/0.log | awk '{print $1}'