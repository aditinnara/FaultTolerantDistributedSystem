import socket
from time import localtime, strftime, time, sleep
import sys
import select
import threading

# as a primary, checkpoint the backups given a checkpointing frequency
def checkpoint_backups(backup_servers, checkpt_freq, my_state, server_id):
    checkpoint_count = 0
    while True:
        for backup_socket in backup_servers:
            checkpoint_msg = f"<{server_id}, {checkpoint_count}, checkpoint, {my_state}>"
            backup_socket.sendall(checkpoint_msg.encode())
            print(f"\033[1;32m[{strftime('%Y-%m-%d %H:%M:%S', localtime())}] [CHECKPOINT NUM {checkpoint_count}] {server_id} sending checkpoint {my_state} to backup server\033[0m")
        checkpoint_count += 1
        sleep(checkpt_freq)

# as a backup, receive checkpoint from primary
def receive_checkpoints(backup_socket, my_state, server_id):
        checkpoint_count = 0
        while True:
            to_read_buffer, _, _ = select.select([backup_socket], [], [], 1 / 10) # 1/10 is arbitrary frequency for nonblocking op
            if to_read_buffer:
                try:
                    # try to receive checkpt
                    checkpoint_msg = backup_socket.recv(1024).decode("utf-8")
                    # non-blocking for receiving a heartbeat ACK from GFD

                    if checkpoint_msg:
                        checkpoint_msg = checkpoint_msg.strip('<>').split(', ')
                        received_server_id = checkpoint_msg[0]
                        received_checkpoint_count = int(checkpoint_msg[1])
                        received_state = eval(checkpoint_msg[3])  # turn state into dict from string

                        # update state and checkpt counter
                        checkpoint_count = received_checkpoint_count
                        my_state.update(received_state)  

                        # print checkpoint
                        print(f"\033[1;36m[{strftime('%Y-%m-%d %H:%M:%S', localtime())}] [RECEIVED CHECKPOINT NUM {checkpoint_count}] {server_id} updated state to {my_state} from {received_server_id}\033[0m")
                except Exception as e:
                    # if we don't have anything from the primary, just pass
                    pass


def client_handler(client_socket, addr, my_state, server_id, primary_bool):
    try:
        while True:
            request = client_socket.recv(1024).decode("utf-8")
            request_split = request.strip('<').split(',')
            lfd_id = request_split[0].strip() 

            # receive heartbeat from LFD
            if "heartbeat" in request:  
                # get heartbeat_count
                heartbeat_count = request_split[2].strip()

                # print [timestamp] [heartbeat_count] Sx receives heartbeat from LFDx
                print(f"\033[1;35m[{strftime('%Y-%m-%d %H:%M:%S', localtime())}] [{heartbeat_count}] {server_id} receives heartbeat from {lfd_id}\033[0m")
                
                # print [timestamp] [heartbeat_count] Sx sending heartbeat acknowledgment to LFDx
                print(f"\033[35m[{strftime('%Y-%m-%d %H:%M:%S', localtime())}] [{heartbeat_count}] {server_id} sending heartbeat ACK to {lfd_id}\033[0")
                
                # send heartbeat ACK
                client_socket.sendall(request.encode())
            # Receiving request from client
            else:   
                # print [timestamp] Received <client_id, server_id, request_num, request> 
                print(f"\033[1;38;5;214m[{strftime('%Y-%m-%d %H:%M:%S', localtime())}] Received {request}\033[0m")
                
                if primary_bool == 1:
                    client_id = request_split[0]  
                    request_num = int(request_split[2])

                    # print [timestamp] my_state_[Sx] =  prev_state before processing <client_id, server_id, request_num, request>
                    print(f"\033[34m[{strftime('%Y-%m-%d %H:%M:%S', localtime())}] my_state_{server_id} = {my_state} before processing {request}\033[0m")

                    # update state (inc number of hellos from this client)
                    my_state[client_id] += 1

                    # print [timestamp] my_state_[Sx] =  new_state after processing <client_id, server_id, request_num, request>
                    print(f"\033[1;34m[{strftime('%Y-%m-%d %H:%M:%S', localtime())}] my_state_{server_id} = {my_state} after processing {request}\033[0m")

                    reply_str = f"Hello, Client {client_id}"
                    # reply = <client_id, server_id, request_num, reply> 
                    reply = f"<{client_id}, {server_id}, {request_num}, {reply_str}>"
                    
                    # print [timestamp] Sending <client_id, server_id, request_num, reply> 
                    print(f"\033[38;5;214m[{strftime('%Y-%m-%d %H:%M:%S', localtime())}] Sending {reply}\033[0m")
                    
                    # send the reply
                    client_socket.sendall(reply.encode())
                else:
                    print(f"\033[33m[{strftime('%Y-%m-%d %H:%M:%S', localtime())}] Backup server {server_id} received client request.\033[0m")

    except Exception as e:
        print(f"Error when handling client: {e}")
    finally:
        client_socket.close()
        print(f"Connection to client ({addr[0]}:{addr[1]}) closed")

def run_server(server_id, port, server_ip, primary_bool, checkpt_freq):
   
    my_state = {"C1": 0, "C2": 0, "C3": 0}
    
    # establish connection with clients and LFD
    host = server_ip 

    # establish "back channel" communication from primary to backups (ONLY IF this server is primary)
    if primary_bool == 1:
        backups = [("127.0.0.1", 7001), ("127.0.0.1", 7002)]  # ips of backups and ports of backups, fix this
        backup_servers = []
        for backup in backups:
            backup_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            backup_socket.connect(backup)
            backup_servers.append(backup_socket)
            print(f"{server_id} connected to backup server at {backup[0]}:{backup[1]}")
        
            # thread for checkpointing the backups
            if primary_bool == 1:
                # i THINK we're passing my_state here by reference -- so when client_handler modifies my_state, this will get sent to thebackups
                primary_checkpt_thread = threading.Thread(target=checkpoint_backups, args=(backup_servers, checkpt_freq, my_state, server_id))
                primary_checkpt_thread.start()
    else:
        backup_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        backup_socket.connect(("127.0.0.1", 6000))  # PRIMARY's IP and port!!! fix this

        receive_checkpt_thread = threading.Thread(target=receive_checkpoints, args=(backup_socket, my_state, server_id))
        receive_checkpt_thread.start()

    try:
        # initialize server
        server_socket = socket.socket()
        server_socket.bind((host, port))
        server_socket.listen(4)  # can listen for 4 connections: 3 clients, 1 LFD
        print(f"{server_id} Listening on {host}:{port}")

        while True:
            # accept a client and start a new thread for each connection
            client_sock, addr = server_socket.accept()
            print(f"Accepted connection from {addr[0]}:{addr[1]}")
            client_thread = threading.Thread(target=client_handler, args=(client_sock, addr, my_state, server_id, primary_bool))
            client_thread.start()


    except Exception as e:
        print(f"Error: {e}")
    finally:
        server_socket.close()

if __name__ == "__main__":
    # Pass server ID and port number
    server_id = sys.argv[1] # server id: S1
    port = int(sys.argv[2]) # port: 6000
    server_ip = sys.argv[3]
    primary_bool = int(sys.argv[4]) # if it's a primary (1) or backup (0)
    if primary_bool:
        checkpt_freq = sys.argv[5]  # only if this is a primary 

    run_server(server_id, port, server_ip, primary_bool)


