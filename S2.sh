#!/bin/sh

#run server 2 (passive replica)
#python3 server.py <server_index (1,2,3)> <checkpoint_freq> <server_ip1> <server_ip2> <server_ip3> 

echo "running server 2"
python3 server.py 2 5 192.168.0.176 192.168.0.176 192.168.0.176