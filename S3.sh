#!/bin/sh

#run server 3 (passive replica)
#python3 server.py <server_index (1,2,3)> <checkpoint_freq> <server_ip1> <server_ip2> <server_ip3> 

echo "running server 3"
python3 server.py 3 2 18.236.81.208 35.89.143.40 172.31.37.26