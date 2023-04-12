#!/bin/sh

TOOL_MACHINE="user@host"

# extraction of scheduler logs including the compressed
sudo gunzip -d /var/log/pods/openwhisk_owdev-s*/scheduler/*.gz
# copy of the logs into the tool machine
sudo scp /var/log/pods/openwhisk_owdev-s*/scheduler/*.log* $TOOL_MACHINE:/home/ubuntu/results/loaded
# removing all the logs for not use them anymore, we cannot remove the 0.log(is used), but its old logs are filtered by the parser
sudo rm -r /var/log/pods/openwhisk_owdev-s*/scheduler/*.log.*

# extraction of invoker logs including the compressed
sudo gunzip -d /var/log/pods/openwhisk_owdev-in*/invoker/*.gz
# copy of the logs into the tool machine
sudo scp /var/log/pods/openwhisk_owdev-in*/invoker/*.log* $TOOL_MACHINE:/home/ubuntu/results/loaded
# removing all the logs for not use them anymore, we cannot remove the 0.log(is used), but its old logs are filtered by the parser
sudo rm -r /var/log/pods/openwhisk_owdev-in*/invoker/*.log.*

