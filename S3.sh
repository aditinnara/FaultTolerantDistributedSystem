#!/bin/sh

#run server 3 (passive replica)
#python3 server.py <server_index (1,2,3)> <checkpoint_freq> <server_ip1> <server_ip2> <server_ip3> 

echo "running server 3"
python3 server.py 3 5 3.80.211.150 44.201.110.34 172.31.13.20