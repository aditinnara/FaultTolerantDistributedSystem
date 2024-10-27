#!/bin/sh

#run server 2 (passive replica)
#server id, port, server ip, primary/backup(1/0), checkpoint frequency

echo "running server 2" 
python3 server.py S2 6001 172.19.190.89 0