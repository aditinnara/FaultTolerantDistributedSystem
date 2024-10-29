#!/bin/sh

#run server 3 (passive replica)
#server id, port, server ip, primary/backup(1/0), checkpoint frequency

echo "running server 3" 
#python3 server.py S3 6000 172.19.190.89 0
python3 server.py 3 5 172.26.80.245 172.26.80.245 172.26.80.245