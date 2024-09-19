# # MULTITHREADED SERVER CODE

# import socket
# from time import localtime, strftime, time, sleep
# import sys
# import threading

# def client_handler(client_socket, addr, my_state):
#     try:
#         while True:
            
#             request = client_socket.recv(1024).decode("utf-8")
#             request_split = request.strip('<').split(',')
#             if "heartbeat" in request:  # receive heartbeat from LFD:
#                 # get heartbeat_count
#                 heartbeat_count = request_split[2].strip()

#                 # print [timestamp] [heartbeat_count] S1 receives heartbeat from LFD
#                 print(f"[{strftime("%Y-%m-%d %H:%M:%S", localtime())}] [{heartbeat_count}] S1 receives heartbeat from LFD1")
#                 # print [timestamp] [heartbeat_count] S1 sending heartbeat acknowledgment to LFD
#                 print(f"[{strftime("%Y-%m-%d %H:%M:%S", localtime())}] [{heartbeat_count}] S1 sending heartbeat ACK to LFD1")
#                 # send heartbeat reply (just send the request back)
#                 client_socket.sendall(request.encode())
#             else:   # receive request from client:
#                 # print [timestamp] Received <client_id, server_id, request_num, request> 
#                 print(f"[{strftime("%Y-%m-%d %H:%M:%S", localtime())}] Received {request}")
                
#                 client_id = request_split[0]   # get the "C1"
#                 request_num = int(request_split[2])

#                 # print [timestamp] my_state_[S1] =  prev_state before processing <client_id, server_id, request_num, request>
#                 print(f"[{strftime("%Y-%m-%d %H:%M:%S", localtime())}] my_state_S1 = {my_state} before processing {request}")

#                 # update state (inc num hellos from this client)
#                 my_state[client_id] += 1

#                 # print [timestamp] my_state_[S1] =  new_state after processing <client_id, server_id, request_num, request>
#                 print(f"[{strftime("%Y-%m-%d %H:%M:%S", localtime())}] my_state_S1 = {my_state} after processing {request}")

#                 # process request to create a reply --> "Hello, client client_id!"  
#                 reply_str = f"Hello, Client {client_id}"
#                 # reply = <client_id, server_id, request_num, reply> 
#                 reply = f"<{client_id}, S1, {request_num}, {reply_str}>"
#                 # print [timestamp] Sending <client_id, server_id, request_num, reply> 
#                 print(f"[{strftime("%Y-%m-%d %H:%M:%S", localtime())}] Sending {reply}")
#                 # send the reply
#                 client_socket.sendall(reply.encode())

#     except Exception as e:
#         print(f"Error when handling client: {e}")
#     finally:
#         client_socket.close()
#         print(f"Connection to client ({addr[0]}:{addr[1]}) closed")
            


# def run_server():
#     # init my_state --> maybe (num of hellos C1, num hellos C2, num hellos C3), init to (0,0,0)
#     my_state = {"C1": 0, "C2": 0, "C3": 0}
#     # init i_am_ready = 1
#     i_am_ready = 1
#     # establish connection with client
#     host = '127.0.0.1'
#     port = 6000

#     try:
#         # initialize server
#         s1 = socket.socket()
#         s1.bind((host, port))
#         s1.listen(4)    # server can listen for 4 things at once: 3 clients, 1 LFD
#         print(f"Listening on {host}:{port}")

#         # initiate a connection with LFD (local fault detector) and
#         while True:
#             # accept a client and start a new thread --> are we allowed to use multithreading?
#             client_sock, addr = s1.accept()
#             print(f"Accepted connection from {addr[0]}:{addr[1]}")
#             client_thread = threading.Thread(target=client_handler, args=(client_sock, addr, my_state))
#             client_thread.start()

#     except Exception as e:
#         print(f"Error: {e}")
#     finally:
#         s1.close()

# if __name__ == "__main__":
#     run_server()


# ------------------------------------------------------------------------------------------------------------------------------------------------


# NONBLOCKING IO SERVER CODE

import socket
from time import localtime, strftime, time, sleep
import sys

def client_handler(client_socket, addr, my_state):
    try:
        request = client_socket.recv(1024).decode("utf-8")
        
        # if there was no request to be received, the client has disconnected (because we haven't seen a message from them) --> is this correct behavior?
        if not request:
            return False
        
        request_split = request.strip('<').split(',')
        if "heartbeat" in request:  # receive heartbeat from LFD:
            # get heartbeat_count
            heartbeat_count = request_split[2].strip()

            # print [timestamp] [heartbeat_count] S1 receives heartbeat from LFD
            print(f"[{strftime("%Y-%m-%d %H:%M:%S", localtime())}] [{heartbeat_count}] S1 receives heartbeat from LFD1")
            # print [timestamp] [heartbeat_count] S1 sending heartbeat acknowledgment to LFD
            print(f"[{strftime("%Y-%m-%d %H:%M:%S", localtime())}] [{heartbeat_count}] S1 sending heartbeat ACK to LFD1")
            # send heartbeat reply (just send the request back)
            client_socket.sendall(request.encode())
        else:   # receive request from client:
            # print [timestamp] Received <client_id, server_id, request_num, request> 
            print(f"[{strftime("%Y-%m-%d %H:%M:%S", localtime())}] Received {request}")
            
            client_id = request_split[0]   # get the "C1"
            request_num = int(request_split[2])

            # print [timestamp] my_state_[S1] =  prev_state before processing <client_id, server_id, request_num, request>
            print(f"[{strftime("%Y-%m-%d %H:%M:%S", localtime())}] my_state_S1 = {my_state} before processing {request}")

            # update state (inc num hellos from this client)
            my_state[client_id] += 1

            # print [timestamp] my_state_[S1] =  new_state after processing <client_id, server_id, request_num, request>
            print(f"[{strftime("%Y-%m-%d %H:%M:%S", localtime())}] my_state_S1 = {my_state} after processing {request}")

            # process request to create a reply --> "Hello, client client_id!"  
            reply_str = f"Hello, Client {client_id}"
            # reply = <client_id, server_id, request_num, reply> 
            reply = f"<{client_id}, S1, {request_num}, {reply_str}>"
            # print [timestamp] Sending <client_id, server_id, request_num, reply> 
            print(f"[{strftime("%Y-%m-%d %H:%M:%S", localtime())}] Sending {reply}")
            # send the reply
            client_socket.sendall(reply.encode())
        return True  # if we made it through the whole try block, our client is active, return True
    except BlockingIOError: # means we have no data to process -- try again later
        return True
    except Exception as e:  # error that causes client to break some other way -- close client and see if they reconnect --> is this correct behavior?
        print(f"Error when handling client: {e}")
        return False  
            


def run_server():
    # init my_state --> maybe (num of hellos C1, num hellos C2, num hellos C3), init to (0,0,0)
    my_state = {"C1": 0, "C2": 0, "C3": 0}
    # init i_am_ready = 1
    i_am_ready = 1
    # establish connection with client
    host = '127.0.0.1'
    port = 6000

    # initialize server
    s1 = socket.socket()
    s1.bind((host, port))
    s1.listen(4)    # server can listen for 4 things at once: 3 clients, 1 LFD
    s1.setblocking(False)  # we should make it nonblocking so it doesn't wait to receive
    print(f"Listening on {host}:{port}")
    
    # keep track of all client connections (including lfd)
    client_sockets = []
    try:
        while True:
            try:
                # accept a client and start a new thread --> are we allowed to use multithreading?
                client_sock, addr = s1.accept()
                client_sock.setblocking(False)  # client should not wait to receive either
                print(f"Accepted connection from {addr[0]}:{addr[1]}")
                client_sockets.append((client_sock, addr))  # add the new accepted client to client socket list
            except BlockingIOError: # no new clients to connect, pass
                pass    
            

            active_client_connections = []
            for client_sock, addr in client_sockets:
                is_active = client_handler(client_sock, addr, my_state)
                if is_active: # this is the client handler call
                    active_client_connections.append((client_sock, addr))
            # only keep the clients that haven't errored out, so we don't keep going back to them
            client_sockets = active_client_connections

    except Exception as e:
        print(f"Error: {e}")
    finally:
        # if error, close all clients and server
        s1.close()
        for client_sock, addr in client_sockets:
            client_sock.close()



if __name__ == "__main__":
    run_server()




