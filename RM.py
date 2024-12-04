# RM (Replication Manager)
import socket
import sys
import threading
import subprocess

membership = []
member_count = 0
# keep track of primary replica
primary = None
# Dictionary which maps server names to their corresponding shell scripts
server_scripts = {
    "S1": ["S1.sh", "ubuntu@ec2-34-222-115-228.us-west-2.compute.amazonaws.com"],
    "S2": ["S2.sh", "ubuntu@ec2-35-89-143-40.us-west-2.compute.amazonaws.com"],
    "S3": ["S3.sh", "ubuntu@ec2-34-217-83-10.us-west-2.compute.amazonaws.com"]
}
# NEW CODE -- try to recover server based on which server was removed
# def recover_server(removed_server):
#     if removed_server not in server_scripts:
#         raise ValueError(f"Invalid server name: {removed_server}")
#     shell_script, remote_host = server_scripts[removed_server]
#     ssh_command = [
#         "gnome-terminal", "--", "ssh", remote_host, f"bash {shell_script}"
#     ]
#     # now the server machines should log everything
#     print(f"Recovering {removed_server} on {remote_host}...")
#     subprocess.Popen(ssh_command)
    
def recover_server(removed_server):
    if removed_server not in server_scripts:
        raise ValueError(f"Invalid server name: {removed_server}")
    
    shell_script, remote_host = server_scripts[removed_server]
    session_name = f"replica_{removed_server}"
    
    # SSH command to start the server process in a tmux session
    ssh_command = [
        "ssh", "-t", remote_host, 
        f"tmux new-session -d -s {session_name} 'cd FaultTolerantDistributedSystem && bash {shell_script}; bash'"
    ]
    
    print(f"Recovering {removed_server} on {remote_host} in tmux session '{session_name}'...")
    try: 
        subprocess.run(ssh_command, check=True) 
    except subprocess.CalledProcessError as e: 
        print(f"Error: {e}") 
        print(f"Output: {e.output}") 
        print(f"Return code: {e.returncode}")
    print(f"To view logs, SSH to {remote_host} and attach to the tmux session:")
    print(f"tmux attach -t {session_name}")

def gfd_handler(gfd_socket, addr):
    global membership, member_count, primary, server_launch_time
    try:
        while True:
            request = gfd_socket.recv(1024).decode("utf-8")
            request_split = request.strip('<').strip('>').split(',')
            
            # Notice for addition/removal of servers
            if "add replica" in request_split:
                added_server = request_split[3].strip('>')
                if added_server in membership:
                    continue # ignore duplicates
                member_count += 1
                membership.append(added_server)
                # elect primary
                if member_count == 1:
                    primary = added_server
                    #print(f"RM: new primary is {primary}")
                    # notify GFD of the new primary
                    new_primary_text = f"<RM,GFD,new primary,{added_server}>"
                    gfd_socket.sendall(new_primary_text.encode())
                    #print(f"RM: send new primary {primary} to GFD")
                print(f"\033[1;32mAdding server {added_server}...\033[0m")
                print(f"\033[1;35mRM: {member_count} members: {', '.join(membership)}\033[0m")
            elif "delete replica" in request_split:
                removed_server = request_split[3].strip('>')
                if removed_server in membership:
                    member_count -= 1
                    membership.remove(removed_server)
                    # if primary fails, reelect primary
                    if member_count > 0 and removed_server == primary:
                        primary = membership[0]
                        #print(f"RM: new primary is {primary}")
                        # notify GFD of the new primary
                        new_primary_text = f"<RM,GFD,new primary,{primary}>"
                        gfd_socket.sendall(new_primary_text.encode())
                        #print(f"RM: send new primary {primary} to GFD")
                    print(f"\033[1;31mRemoving server {removed_server}...\033[0m")
                    print(f"\033[1;35mRM: {member_count} members: {', '.join(membership)}\033[0m")
                if recover_server(removed_server):
                    # tell GFD we are RECOVERING
                    recovered_server_text = f"<RM,GFD,recovered replica,{removed_server}>"
                    gfd_socket.sendall(recovered_server_text.encode())
                    # Add the recovered server back to membership
                    member_count += 1
                    membership.append(removed_server)
                    print(f"\033[1;32mRM: {removed_server} has rejoined.\033[0m")
                    print(f"\033[1;35mRM: {member_count} members: {', '.join(membership)}\033[0m")
            

            # if ("S1" in request_split) or ("S2" in request_split) or ("S3" in request_split):
            #     member_count = len(request_split)
            #     membership = request_split
            #     print(f"\033[1;35mRM: {member_count} members: {', '.join(request_split)}\033[0m")
                
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
        # enable reuse
        rm_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        rm_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
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