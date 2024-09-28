# CLIENT pseudocode

import socket
from time import localtime, strftime, time, sleep
import sys
    
def run_client(client_id, client_freq):
    # initialize client
    c = socket.socket()
    # init server id
    server_id = 1
    # connect client with server
    s1_port = 6000
    s1_ip = '127.0.0.1'
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
        request_str = f"<C{client_id}, S{server_id}, {c_request_num}, Hello Server!>"

        # send request
        c.send(request_str.encode())

        # get timestamp
        sent_timestamp_str = strftime("%Y-%m-%d %H:%M:%S", localtime())
        print(f"\033[1;38;5;214m[{sent_timestamp_str}] Sent {request_str}\033[0m")

        # TODO: should this also be a loop - looping across active servers and receiving replies from all active servers
        reply = c.recv(1024).decode()   
        recv_timestamp_str = strftime("%Y-%m-%d %H:%M:%S", localtime())

        # TODO: only print this for one of the servers' responses -- suppress duplicates by keeping 
        #       track of the last received request_num, and suppressing dups OR if received request_num
        #       is greater than the request num that we just sent. Is this the correct logic?
        print(f"\033[38;5;214m[{recv_timestamp_str}] Received {reply}\033[0m")

        # wait 2 seconds before sending another message
        sleep(client_freq)

if __name__ == "__main__":
    run_client(int(sys.argv[1]), int(sys.argv[2]))    # give the client id as a commandline parameter AND the frequency with which client should send messages