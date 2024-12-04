#!/bin/sh

#run server 2 (passive replica)
#python3 server.py <server_index (1,2,3)> <checkpoint_freq> <server_ip1> <server_ip2> <server_ip3> 

echo "running server 2"
python3 server.py 2 2 18.236.81.208 172.31.46.129 34.217.83.10