# GFD (Global Fault Detector) Pseudocode
import socket
import select
from time import localtime, strftime, time, sleep
import sys
import threading

membership = []
member_count = 0

def rm_handler(rm_socket, gfd_name):
    global membership, member_count
    try:
        while True:
            request = rm_socket.recv(1024).decode("utf-8")
            request_split = request.strip('<').strip('>').split(',')

            if "new primary" in request_split: 
                new_primary = request_split[3].strip('>')
                for server in lfd_sockets:
                    new_primary_text = f"<GFD,LFD,new primary,{new_primary}>@"
                    lfd_sockets[server].sendall(new_primary_text.encode())
                    print(f"GFD to {server}: New primary is {new_primary}")
    except Exception as e:
        print(e)
        pass


def lfd_handler(lfd_socket, addr, rm_socket):
    global membership, member_count, lfd_sockets
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
                # update lfd sockets
                lfd_sockets[added_server] = lfd_socket
                print(f"\033[1;32mAdding server {added_server}...\033[0m")
                print(f"\033[1;32mGFD: {member_count} members: {', '.join(membership)}\033[0m")
                # updates RM about membership change
                add_text = f"<GFD,RM,add replica,{added_server}>"
                rm_socket.sendall(add_text.encode())
            elif "delete replica" in request_split: # delete replica from membership 
                sending_lfd = request_split[0].strip() # LFD1
                removed_server = request_split[3].strip('>') # S1
                if removed_server in membership:
                    member_count -= 1
                    membership.remove(removed_server)
                    print(f"\033[1;31mRemoving server {removed_server}...\033[0m")
                    print(f"\033[1;31mGFD: {member_count} members: {', '.join(membership)}\033[0m")
                    # updates RM about membership change
                    delete_text = f"<GFD,RM,delete replica,{removed_server}>"
                    rm_socket.sendall(delete_text.encode())
    except Exception as e:
        print(e)
        pass
    finally:
        lfd_socket.close()
        print(f"Connection to LFD ({addr[0]}:{addr[1]}) closed")


def run_GFD(gfd_ip,rm_ip, rm_port):
    global lfd_sockets
    lfd_sockets = {} # for communication between RM and servers
    print(f"GFD: {member_count} members") # initial print 
    host = gfd_ip
    port = 6877
   
    print(f"Listening on {host}:{port}")
    
    try:
        # init rm socket and connect
        rm_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        rm_socket.connect((rm_ip, rm_port))
        print(f"GFD connected to RM at {rm_ip}:{rm_port}")
        # Need to receive RM messages for membership control(set i_am_ready, is_primary)
        message = f"RM: {member_count} members"
        rm_socket.sendall(message.encode())
        rm_thread = threading.Thread(target=rm_handler, args=(rm_socket, "GFD"))
        rm_thread.start()
        
        # init gfd socket and connect
        gfd_socket = socket.socket()
        gfd_socket.bind((host, port))
        gfd_socket.listen(3) # gfd listens to LFD1, LFD2, LFD3 

        while True:
            # accept LFD and start a new thread
            lfd_sock, addr = gfd_socket.accept()
            print(f"Accepted connection from {addr[0]}:{addr[1]}")
            lfd_thread = threading.Thread(target=lfd_handler, args=(lfd_sock, addr, rm_socket))
            lfd_thread.start()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print('hi')
        gfd_socket.close()
        rm_socket.close()

if __name__ == "__main__":
    gfd_ip = sys.argv[1] 
    rm_ip = sys.argv[2] 
    rm_port = int(sys.argv[3]) 
    run_GFD(gfd_ip, rm_ip, rm_port)