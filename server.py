import socket
from time import localtime, strftime, time, sleep
import sys
import select
import threading

# as a primary, checkpoint the backups given a checkpointing frequency
def checkpoint_backups(backup_socket, checkpt_freq, server_id):
    
    # connected = False
    # # connect to the backup server
    # while not connected:
    #     try:
    #         backup_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #         backup_socket.connect((backup_ip, backup_port))
    #         print(f"{server_id} connected to backup server at {backup_ip}:{backup_port}")
    #         connected = True
    #     except Exception as e:
    #         print(f"Error connecting to backup server: {e}")
    #         backup_socket.close()
    #         sleep(3)
    
    # send checkpoint to the backup server

    checkpoint_count = 0

    global my_state 
    try:
        print("CHECKPOINTING BACKUPS")
        checkpoint_msg = f"<{server_id}-{checkpoint_count}-checkpoint-{my_state}>" # joined with - instead of ,
        backup_socket.sendall(checkpoint_msg.encode())
        print(f"\033[1;32m[{strftime('%Y-%m-%d %H:%M:%S', localtime())}] [CHECKPOINT NUM {checkpoint_count}] {server_id} sending checkpoint {my_state} to backup server\033[0m")
        checkpoint_count += 1
        sleep(checkpt_freq)
    except Exception as e:
        print(f"Error when checkpointing: {e}")
        backup_socket.close()
        return -1
        sleep(checkpt_freq)


# as a backup, receive checkpoint from primary
def receive_checkpoints(backup_socket, server_id):
        checkpoint_count = 0
        to_read_buffer, _, _ = select.select([backup_socket], [], [], 1 / 10) # 1/10 is arbitrary frequency for nonblocking op
        if to_read_buffer:
            try:
                # try to receive checkpt
                checkpoint_msg = backup_socket.recv(1024).decode("utf-8")
                # non-blocking for receiving a heartbeat ACK from GFD

                if checkpoint_msg:
                    checkpoint_msg = checkpoint_msg.strip('<>').split('-') # delimeter can't be part of string form of dist
                    received_server_id = checkpoint_msg[0]
                    received_checkpoint_count = int(checkpoint_msg[1])
                    received_state = eval(checkpoint_msg[3])  # turn state into dict from string

                    # update state and checkpt counter
                    checkpoint_count = received_checkpoint_count
                    global my_state 
                    my_state.update(received_state)  

                    # print checkpoint
                    print(f"\033[1;36m[{strftime('%Y-%m-%d %H:%M:%S', localtime())}] [RECEIVED CHECKPOINT NUM {checkpoint_count}] {server_id} updated state to {my_state} from {received_server_id}\033[0m")
            except Exception as e:
                print(f"Error when hearing from primary: {e}")



def client_handler(client_socket, addr, server_id):
    global is_primary, primary
    try:
        while True:
            request = client_socket.recv(1024).decode("utf-8")
            # print("request before split: ", request)
            request_split = request.strip('<').split(',')
            lfd_id = request_split[0].strip()
            print(request)

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
            # new primary election from LFD
            elif "new primary" in request:
                new_primary = request_split[-1].strip('>')
                print(new_primary)
                primary = new_primary
                print(f"{server_id} receives that {primary} is the New Primary")
                if primary == server_id:
                    is_primary = 1
                    print(f"\033[1;32m[{server_id} is the new primary\033[0m")
            # Receiving request from client
            else:   
                # print [timestamp] Received <client_id, server_id, request_num, request> 
                print(f"\033[1;38;5;214m[{strftime('%Y-%m-%d %H:%M:%S', localtime())}] Received {request}\033[0m")
                # TODO: newly recovered replica: receive and log incoming request numbers.
                # high_watermark_request_num[]
                
                if is_primary == 1:
                    global my_state
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


def peer_handler(peer_sock, server_id, checkpt_freq):
    global is_primary
    while True:
        if is_primary:
            res = checkpoint_backups(peer_sock, checkpt_freq, server_id)
            if res == -1:
                break
        else:
            receive_checkpoints(peer_sock, server_id)
        sleep(checkpt_freq)


def peer_listen_connections(host, backup_port, checkpt_freq):
    # open a socket
    while True:
        try:
            peer_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peer_server_socket.bind((host, backup_port))
            peer_server_socket.listen(10) # can listen for 2 connections
            print(f"Listening for peers on {host}:{backup_port}")
            break
        except Exception as e:
            peer_server_socket.close()
            print(f"Error open listen socket for peers: {e}")


    while True:
        # manage peer connections
        try:
            peer_sock, peer_addr = peer_server_socket.accept()
            print(f"Accepted peer connection from {peer_addr[0]}:{peer_addr[1]}")
            peer_thread = threading.Thread(target=peer_handler, args=(peer_sock, host, checkpt_freq))
            peer_thread.start()
        except Exception as e:
            print(f"Error accepting connection from peer server: {e}")
            sleep(checkpt_freq)


def peer_connect(peer_ip, peer_port, heartbeat_timeout, host):
    while True:
        try:
            print(f"Try to connect peer {peer_ip}:{peer_port}")
            peer_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peer_client_socket.connect((peer_ip, peer_port))
            peer_thread = threading.Thread(target=peer_handler, args=(peer_client_socket, host, checkpt_freq))
            peer_thread.start()
            return 
        except Exception as e:
            print(f"Error connecting to peer server: {e}")
            peer_client_socket.close()
            sleep(heartbeat_timeout)



def run_server(server_id, port, server_ip, peer_ips, checkpt_freq, peer_ports, backup_port):
    global my_state, i_am_ready, high_watermark_request_num, is_primary, primary
    primary = None
    active_peer_connections = 0
    my_state = {"C1": 0, "C2": 0, "C3": 0}
    # ready to start accepting and processing client requests
    i_am_ready = 0
    # log incoming request numbers
    high_watermark_request_num = []
    
    
    # establish connection with clients and LFD
    host = server_ip 
    # TODO: Port number for backup, change it

    # Maintain Connection with peer replicas

    # open socket, listen and accept connections
    peer_listen_thread = threading.Thread(target=peer_listen_connections, args=(host, backup_port, checkpt_freq))
    peer_listen_thread.start()
    
    # connect to peers
    for i in range(len(peer_ips)):
        peer_ip = peer_ips[i]
        peer_port = peer_ports[i]
        peer_connect_thread = threading.Thread(target=peer_connect, args=(peer_ip, peer_port, checkpt_freq, host))
        peer_connect_thread.start()
    

    # # Establish "back channel" communication from primary to backups (ONLY IF this server is primary)
    # # For backup, use port other than the client port for the primary to connect
    # if is_primary == 1: # Primary
    #     for i, backup_ip in enumerate(fellow_ips):
    #         backup_port = fellow_ports[i]
    #         primary_checkpt_thread = threading.Thread(target=checkpoint_backups, args=(backup_ip, backup_port, checkpt_freq, server_id))
    #         primary_checkpt_thread.start()

    # else: # Backup
    #     backup_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #     # bind socket with server IP and back_up port
    #     backup_socket.bind((host, backup_port))
    #     # open backup socket to listen for primary connection
    #     backup_socket.listen(1) # can listen for 1 connection: Primary
    #     print(f"Backup {server_id} Listening on {host}:{backup_port}")

    #     try:
    #         primary_sock, primary_addr = backup_socket.accept()
    #         print(f"Accepted primary connection from {primary_addr[0]}:{primary_addr[1]}")
    #         receive_checkpt_thread = threading.Thread(target=receive_checkpoints, args=(primary_sock, server_id))
    #         receive_checkpt_thread.start()
    #     except:
    #         print(f"Error connecting to primary server")

    # Establish connection with clients and LFD
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
            client_thread = threading.Thread(target=client_handler, args=(client_sock, addr, server_id))
            client_thread.start()


    except Exception as e:
        print(f"Error: {e}")
    finally:
        # clean up
        server_socket.close()

if __name__ == "__main__":
    # Command: python3 server.py <server_ID> <client_port_number> <server_IP> <is_primary> <checkpoint_freq>
    # TODO: specify backup_port_number as well?
    
    # server_id = sys.argv[1] # server id: S1
    # port = int(sys.argv[2]) # client port number
    # server_ip = sys.argv[3]
    # is_primary = int(sys.argv[4]) # if it's a primary (1) or backup (0)
    # checkpt_freq = 10 # default checkpoint frequency
    # if is_primary:
    #     checkpt_freq = int(sys.argv[5])  # only if this is a primary 
        
    # Command: python3 server.py <server_index (1,2,3)> <checkpoint_freq> <server_ip1> <server_ip2> <server_ip3> 
    global is_primary
    server_index = int(sys.argv[1])
    checkpt_freq = int(sys.argv[2])  
    peer_ips = [sys.argv[4], sys.argv[5]]
    
    if server_index == 1:
        server_id = "S1"
        server_ip = sys.argv[3]
        is_primary = 0
        peer_ports = [7011, 7012]
        backup_port = 7010
        port = 6000
    elif server_index == 2:
        server_id = "S2"
        server_ip = sys.argv[4]
        is_primary = 0
        peer_ports = [7010, 7012]
        backup_port = 7011
        port = 6001
    elif server_index == 3:
        server_id = "S3"
        server_ip = sys.argv[5]
        is_primary = 0
        peer_ports = [7010, 7011]
        backup_port = 7012
        port = 6002
    else:
        print("Wrong input command")
    run_server(server_id, port, server_ip, peer_ips, checkpt_freq, peer_ports, backup_port)


