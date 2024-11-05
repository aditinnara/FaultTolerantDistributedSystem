# RM (Replication Manager)
import socket
import sys
import threading

def gfd_handler(gfd_socket, addr):
    try:
        while True:
            request = gfd_socket.recv(1024).decode("utf-8")
            request_split = request.strip('<').strip('>').split(',')
            
            # Notice for addition/removal of servers
            if ("S1" in request_split) or ("S2" in request_split) or ("S3" in request_split):
                member_count = len(request_split)
                print(f"\033[1;35mRM: {member_count} members: {', '.join(request_split)}\033[0m")
                
            else:
                # initial notification from GFD
                print(f"\033[1;35m{request_split[0]}\033[0m")
                
    except Exception as e:
        print(e)
        pass
    finally:
        gfd_socket.close()
        print(f"Connection to LFD ({addr[0]}:{addr[1]}) closed")

def run_RM(rm_ip):
    print("RM: 0 members") # initial print 
    host = rm_ip
    port = 6900
   
    print(f"Listening on {host}:{port}")
    try:
        # init rm socket and connect
        rm_socket = socket.socket()
        rm_socket.bind((host, port))
        rm_socket.listen(1) # rm listens to GFD

        while True:
            # accept GFD and start a new thread
            gfd_sock, addr = rm_socket.accept()
            print(f"Accepted connection from {addr[0]}:{addr[1]}")
            gfd_thread = threading.Thread(target=gfd_handler, args=(gfd_sock, addr))
            gfd_thread.start()
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print('hi')
        rm_socket.close()
    
if __name__ == "__main__":
    rm_ip = sys.argv[1] 
    run_RM(rm_ip)