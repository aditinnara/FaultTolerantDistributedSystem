# GFD (Global Fault Detector) Pseudocode
import socket
import select
from time import localtime, strftime, time, sleep
import sys

membership = []
member_count = 0

def lfd_handler(lfd_socket, addr, my_state):
    
    try:
        while True:
            request = lfd_socket.recv(1024).decode("utf-8")
            #"<LFD1, GFD, {heartbeat_count}, heartbeat>"
            #"<LFD1, GFD, add replica, S1>"
            #"<LFD1, GFD, delete replica, S1>"
            request_split = request.strip('<').split(',')
            if "heartbeat" in request:  # receive heartbeat from LFD:
                #which LFD is sending?
                sending_lfd = request_split[0].strip() 
                # get heartbeat_count
                heartbeat_count = request_split[2].strip()
                # print [timestamp] [heartbeat_count] S1 receives heartbeat from LFD
                print(f"\033[1;35m[{strftime('%Y-%m-%d %H:%M:%S', localtime())}] [{heartbeat_count}] GFD receives heartbeat from {sending_lfd}\033[0m")
                # print [timestamp] [heartbeat_count] S1 sending heartbeat acknowledgment to LFD
                print(f"\033[35m[{strftime('%Y-%m-%d %H:%M:%S', localtime())}] [{heartbeat_count}] GFD sending heartbeat ACK to {sending_lfd}\033[0")
                # send heartbeat reply (just send the request back)
                lfd_socket.sendall(request.encode())
            elif "add replica" in request: #add replica to membership 
                sending_lfd = request_split[0].strip() #LFD1
                added_server = request_split[3].strip() #S1
                member_count += 1 
                membership.append(added_server) 
                print(f"GFD: {member_count} member: {", ".join(membership)}")
            elif "delete replica" in request: #add replica to membership 
                sending_lfd = request_split[0].strip() #LFD1
                removed_server = request_split[3].strip() #S1
                member_count -= 1 
                membership.remove(removed_server) 
                print(f"GFD: {member_count} member: {", ".join(membership)}")



# Allow GFD to always be listening -- LFD 1, LFD 2, LFD 3
# If GFD receives a message
    # If the message says "LFDx: add replica Sx"
        # member_count += 1
        # membership.append(Sx)
        # print “GFD: {membership_count} members: {membership}"
    # Else if the message says "delete replica Sx"    
        # If Sx is in membership:
            # member_count -= 1
            # remove Sx from membership
        # Else:
            # do nothing, this means LFD has connected to a server that hasn't registered

def run_GFD():
    
    
    print(f"GFD: {member_count} members") #initial print 
    host = '127.0.0.1' 
    port = 6001
   
    print(f"Listening on {host}:{port}")
    try:
        # init gfd socket and connect
        gfd_socket = socket.socket()
        gfd.bind((host, port))
        gfd.listen(3) # gfd listens to LFD1, LFD2, LFD3 
        # initiate a connection with LFD (local fault detector)
        while True:
            # accept LFD and start a new thread
            client_sock, addr = s1.accept()
            print(f"Accepted connection from {addr[0]}:{addr[1]}")
            lfd_thread = threading.Thread(target=lfd_handler, args=(lfd_sock, addr, my_state))
            lfd_thread.start()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        gfd.close()
    

if __name__ == "__main__":
    run_GFD()
        




