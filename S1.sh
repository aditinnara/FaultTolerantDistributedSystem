#!/bin/sh

#run server 1 (primary replica)
#server id, port, server ip, primary/backup(1/0), checkpoint frequency

echo "running server 1" 
#python3 server.py S1 6000 172.19.190.89 1 5
python3 server.py 1 5 172.26.80.245 172.26.80.245 172.26.80.245