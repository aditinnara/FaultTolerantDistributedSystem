#!/bin/sh

#run server 1 (primary replica)
#python3 server.py <server_index (1,2,3)> <checkpoint_freq> <server_ip1> <server_ip2> <server_ip3> 

echo "running server 1" 
python3 server.py 1 2 172.31.93.118 44.201.110.34 18.227.134.0 