# CLIENT pseudocode

import socket
from time import localtime, strftime, time, sleep
import sys
import threading

last_request_num = 0
    
def run_client(client_id, client_freq, server_id, mutex):
    # initialize client
    c = socket.socket()
    # init server id
    # server_id = 1
    # connect client with server
    s1_port = 6000
    s1_ip = '127.0.0.1' # TODO: replace with real IP address
    c.connect((s1_ip, s1_port))
    # initialize request number
    c_request_num = 0

    # while True
    while True:
        # keep track of request num
        c_request_num += 1


        # TODO: this section should be a loop, looping across all active servers and sending requests to all of them
        # send requests to server
        # request = <C1, S1, request_num, request> 
        request_str = f"<C{client_id},S{server_id},{c_request_num},Hello Server!>"

        # send request
        c.send(request_str.encode())

        # get timestamp
        sent_timestamp_str = strftime("%Y-%m-%d %H:%M:%S", localtime())
        print(f"\033[1;38;5;214m[{sent_timestamp_str}] Sent {request_str}\033[0m")

        # TODO: should this also be a loop - looping across active servers and receiving replies from all active servers
        reply = c.recv(1024).decode()  
        
        recv_timestamp_str = strftime("%Y-%m-%d %H:%M:%S", localtime())
        # print receipts of all responses
        print(f"\033[38;5;214m[{recv_timestamp_str}] Received {reply}\033[0m")

        # TODO: only print this for one of the servers' responses -- suppress duplicates by keeping 
        #       track of the last received request_num, and suppressing dups OR if received request_num
        #       is greater than the request num that we just sent. Is this the correct logic?
        reply_split = reply.strip('<').split(',') # reply = <client_id, server_id, request_num, reply>  
        request_num = int((reply_split[2]).strip())
        reply_server = reply_split[1].strip()

        # critical section in multithreading: mutate shared variables
        with mutex:
            if (request_num > last_request_num):
                last_request_num = request_num
            else:
                # discard duplicate responses
                print(f"\033[38;5;214m[request_num {request_num}]: Discarded duplicate reply from {reply_server}\033[0m")
            

        # wait 2 seconds before sending another message
        sleep(client_freq)

if __name__ == "__main__":
    # give the client id as a commandline parameter AND the frequency with which client should send messages
    client_id = int(sys.argv[1])
    client_freq = int(sys.argv[2])
    replica_num = 3
    # TODO: connect to 3 active replicas with threads, loop or threads?
    mutex = threading.Lock() # ensure mutual exclusion access to shared variable last_request_num
    for i in range(replica_num):
        client_thread = threading.Thread(target=run_client, args=(client_id, client_freq, i+1, mutex))
        client_thread.start()
