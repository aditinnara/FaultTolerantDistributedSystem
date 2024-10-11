import socket
from time import localtime, strftime, time, sleep
import sys
import threading

def client_handler(client_socket, addr, my_state, server_id):
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
    except KeyboardInterrupt:
            print("KeyboardInterrupt: Exiting...")
            client_socket.close() # Close the socket
            return 
    except Exception as e:
        print(f"Error when handling client: {e}")
    finally:
        client_socket.close()
        print(f"Connection to client ({addr[0]}:{addr[1]}) closed")

def run_server(server_id, port, server_ip):
   
    my_state = {"C1": 0, "C2": 0, "C3": 0}
    
    # establish connection with clients and LFD
    host = server_ip 
    num_client = 3

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
            client_thread = threading.Thread(target=client_handler, args=(client_sock, addr, my_state, server_id))
            client_thread.start()
    except KeyboardInterrupt:
            print("KeyboardInterrupt: Exiting...")
            server_socket.close() # Close the socket
            return 
    except Exception as e:
        print(f"Error: {e}")
        print("connection lost from the client")
    finally:
        server_socket.close()
        client_thread.close() 

if __name__ == "__main__":
    # Pass server ID and port number
    server_id = sys.argv[1] # server id: S1
    port = int(sys.argv[2]) # port: 6000
    server_ip = sys.argv[3]

    run_server(server_id, port, server_ip)


