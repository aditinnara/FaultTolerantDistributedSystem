# LFD (Local Fault Detector) Pseudocode
import socket
import select
from time import localtime, strftime, time, sleep
import sys

last_heartbeat_acked = time()

def send_heartbeat(heartbeat_freq, lfd_socket):
    global last_sent_time, heartbeat_count
    if time() - last_sent_time >= heartbeat_freq: 
        heartbeat = f"<LFD1,S1,{heartbeat_count},heartbeat>"
        
        # use ansi color
        heartbeat_text = f"\033[1;35m[{strftime('%Y-%m-%d %H:%M:%S', localtime())}] [{heartbeat_count}] LFD1 sending heartbeat to S1\033[0m"
        print(heartbeat_text)
       
        try:
            last_sent_time = time()
            lfd_socket.sendall(heartbeat.encode())

            # increment heartbeat number
            heartbeat_count += 1
        except Exception as e:
            pass

def receive_heartbeat(lfd_socket, heartbeat_freq, gfd_socket):
    global last_received_time
    to_read_buffer, _, _ = select.select([lfd_socket], [],[], heartbeat_freq/3) # TODO: change timeout later, for non blocking operation
    if to_read_buffer:
        try:
            heartbeat_ack = lfd_socket.recv(1024).decode("utf-8")
            # if it's a heartbeat message, update the last heartbeat received time
            if "heartbeat" in heartbeat_ack:
                heartbeat_count_str = heartbeat_ack.strip('<').split(',')[2].strip()
                print(f"\033[35m[{strftime('%Y-%m-%d %H:%M:%S', localtime())}] [{heartbeat_count_str}] LFD1 receives heartbeat ACK from S1\033[0m")

                last_received_time = time()

                # TODO: After the first successful heartbeat, send "LFD1: add replica S1" to GFD so GFD can register this server as a member
                if (heartbeat_count == 1):
                    add_text = f"<LFD1,GFD,add replica,S1>"
                    gfd_socket.send(add_text.encode())
                    print("send add to gfd")
                    pass #send add s1 to GFD
        except Exception as e: # Not sure if I should be exception handling
            pass

def send_receive_check_heartbeat(lfd_socket, heartbeat_freq, heartbeat_timeout, gfd_socket):
    global last_sent_time, heartbeat_count, last_received_time
    heartbeat_count = 0

    last_received_time = time()
    last_sent_time = time()


    while True:
        send_heartbeat(heartbeat_freq, lfd_socket)
        receive_heartbeat(lfd_socket, heartbeat_freq, gfd_socket)
                    
            
        # CHECK TIMEOUT
        if time() - last_received_time > heartbeat_timeout:
            # print("elapsed time from last received msg: ", time() - last_received_time)

            print(f"\033[1;31m[{strftime('%Y-%m-%d %H:%M:%S', localtime())}] S1 has died.\033[0m")
            # TODO: send "LFDx: delete replica Sx" too so GFD can remove the server as a member

            heartbeat_count = 0
            break
            


def run_LFD(heartbeat_freq):
    # initialize heartbeat info
    heartbeat_timeout = 2*heartbeat_freq
    # TODO: connect with GFD as well
    gfd_socket = socket.socket()
    gfd_port = 6881
    gfd_ip = '127.0.0.1' # TODO: replace with real GFD IP address
    gfd_socket.connect((gfd_ip, gfd_port))

    while True:
        try:
            # init s1 socket and connect
            s1_socket = socket.socket()
            s1_socket.settimeout(heartbeat_timeout)
            s1_port = 6000
            s1_ip = '127.0.0.1'
            s1_socket.connect((s1_ip, s1_port))

            send_receive_check_heartbeat(s1_socket, heartbeat_freq, heartbeat_timeout, gfd_socket)

            # shouldn't try to wait for the "s1 has died" to join because I haven't set a break
        except Exception as e:  
            # print(f"Error while trying to reconnect to server: {e}")
            sleep(heartbeat_timeout)    # idk if this is the correct behavior!!!!!!!!!!!
    


if __name__ == "__main__":
    run_LFD(int(sys.argv[1])) # configure the heartbeat frequency
        

       

   
    

