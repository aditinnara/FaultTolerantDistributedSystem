#!/bin/sh

#run server 1 (primary replica)
#python3 server.py <server_index (1,2,3)> <checkpoint_freq> <server_ip1> <server_ip2> <server_ip3> 

echo "running server 1" 
python3 server.py 1 5 172.31.35.155 35.89.143.40 34.217.83.10