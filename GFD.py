# GFD (Global Fault Detector) Pseudocode
import socket
import select
from time import localtime, strftime, time, sleep
import sys
import threading

membership = []
member_count = 0

def lfd_handler(lfd_socket, addr):
    global membership, member_count
    
    try:
        while True:
            request = lfd_socket.recv(1024).decode("utf-8")
            request_split = request.strip('<').strip('>').split(',')

            if "heartbeat" in request_split: 
                # Get the LFD that's sending the message
                sending_lfd = request_split[0].strip() 
                heartbeat_count = request_split[2].strip()

                # S1 receives heartbeat from LFD1, for ex
                print(f"\033[1;36m[{strftime('%Y-%m-%d %H:%M:%S', localtime())}] [{heartbeat_count}] GFD receives heartbeat from {sending_lfd}\033[0m")
                # send the ACK
                print(f"\033[36m[{strftime('%Y-%m-%d %H:%M:%S', localtime())}] [{heartbeat_count}] GFD sending heartbeat ACK to {sending_lfd}\033[0")
                
                lfd_socket.sendall(request.encode())
            elif "add replica" in request_split: 
                sending_lfd = request_split[0].strip() # LFD1
                added_server = request_split[3].strip('>') # S1
                member_count += 1
                membership.append(added_server) 
                print(f"\033[1;32mAdding server {added_server}...\033[0m")
                print(f"\033[1;32mGFD: {member_count} members: {', '.join(membership)}\033[0m")
            elif "delete replica" in request_split: # delete replica from membership 
                sending_lfd = request_split[0].strip() # LFD1
                removed_server = request_split[3].strip('>') # S1
                if removed_server in membership:
                    member_count -= 1
                    membership.remove(removed_server)
                    print(f"\033[1;31mRemoving server {removed_server}...\033[0m")
                    print(f"\033[1;31mGFD: {member_count} members: {', '.join(membership)}\033[0m")

    except Exception as e:
        print(e)
        pass
    finally:
        lfd_socket.close()
        print(f"Connection to LFD ({addr[0]}:{addr[1]}) closed")


def run_GFD():
    print(f"GFD: {member_count} members") # initial print 
    host = '127.0.0.1' # TODO: replace with real IP address of GFD
    port = 6881
   
    print(f"Listening on {host}:{port}")
    try:
        # init gfd socket and connect
        gfd_socket = socket.socket()
        gfd_socket.bind((host, port))
        gfd_socket.listen(3) # gfd listens to LFD1, LFD2, LFD3 

        while True:
            # accept LFD and start a new thread
            lfd_sock, addr = gfd_socket.accept()
            print(f"Accepted connection from {addr[0]}:{addr[1]}")
            lfd_thread = threading.Thread(target=lfd_handler, args=(lfd_sock, addr))
            lfd_thread.start()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        gfd_socket.close()
    

if __name__ == "__main__":
    run_GFD()