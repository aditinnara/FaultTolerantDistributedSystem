import socket
import select
from time import localtime, strftime, time, sleep
import sys
import threading

last_heartbeat_acked = time()
heartbeat_count = 0
gfd_heartbeat_count = 0
last_sent_time = time()
last_received_time = time()

def send_heartbeat(heartbeat_freq, lfd_socket, lfd_name, s_name):
    global last_sent_time, heartbeat_count

    if time() - last_sent_time >= heartbeat_freq: 
        heartbeat = f"<{lfd_name},{s_name},{heartbeat_count},heartbeat>"
        
        # Use ANSI color for sending heartbeat
        heartbeat_text = f"\033[1;35m[{strftime('%Y-%m-%d %H:%M:%S', localtime())}] [{heartbeat_count}] {lfd_name} sending heartbeat to {s_name}\033[0m"
        print(heartbeat_text)
       
        try:
            last_sent_time = time()
            lfd_socket.sendall(heartbeat.encode())

            # inc heartbeat number
            heartbeat_count += 1
        except Exception as e:
            print("exception: ", e)
            pass

# Heartbeat function for GFD
def send_gfd_heartbeat(gfd_socket, lfd_name, s_name):
    global gfd_heartbeat_count
    heartbeat_message = f"<{lfd_name},GFD,{gfd_heartbeat_count},heartbeat>"
    try:
        gfd_socket.send(heartbeat_message.encode())
        print(f"\033[1;36m[{strftime('%Y-%m-%d %H:%M:%S', localtime())}] [{gfd_heartbeat_count}] {lfd_name} sending heartbeat to GFD\033[0m")
        gfd_heartbeat_count += 1
    except Exception as e:
        print("exception: ", e)
        pass

def receive_gfd_messages(gfd_socket, lfd_name):
    to_read_buffer, _, _ = select.select([gfd_socket], [], [], heartbeat_freq / 10) 
    if to_read_buffer:
        try:
            gfd_message = gfd_socket.recv(1024).decode("utf-8")
            # non-blocking for receiving a heartbeat ACK from GFD
            if gfd_message:
                heartbeat_count_str = gfd_message.strip('<').split(',')[2].strip()
                print(f"\033[36m[{strftime('%Y-%m-%d %H:%M:%S', localtime())}] [{heartbeat_count_str}] {lfd_name} received heartbeat ACK from GFD\033[0m")
        except Exception as e:
            pass

def receive_heartbeat(lfd_socket, heartbeat_freq, gfd_socket, lfd_name, s_name):
    global last_received_time
    to_read_buffer, _, _ = select.select([lfd_socket], [], [], heartbeat_freq / 10)  
    if to_read_buffer:
        try:
            heartbeat_ack = lfd_socket.recv(1024).decode("utf-8")
            # If it's a heartbeat message, update the last heartbeat received time
            if "heartbeat" in heartbeat_ack:
                heartbeat_count_str = heartbeat_ack.strip('<').split(',')[2].strip()
                print(f"\033[35m[{strftime('%Y-%m-%d %H:%M:%S', localtime())}] [{heartbeat_count_str}] {lfd_name} receives heartbeat ACK from {s_name}\033[0m")

                last_received_time = time()

                # After the first successful heartbeat, send "LFDx: add replica Sx" to GFD
                if heartbeat_count == 1:
                    add_text = f"<{lfd_name},GFD,add replica,{s_name}>"
                    gfd_socket.send(add_text.encode())
                    print(f"\033[36m[{strftime('%Y-%m-%d %H:%M:%S', localtime())}] {lfd_name}: add replica {s_name}\033[0m")
        except Exception as e:
            pass

def send_receive_check_heartbeat(lfd_socket, heartbeat_freq, heartbeat_timeout, gfd_socket, lfd_name, s_name):
    global last_sent_time, heartbeat_count, last_received_time, gfd_heartbeat_count
    heartbeat_count = 0
    gfd_heartbeat_count = 0

    last_received_time = time()
    last_sent_time = time()
    last_gfd_sent_time = time()  

    while True:
        
        send_heartbeat(heartbeat_freq, lfd_socket, lfd_name, s_name)
        
        # if time() - last_gfd_sent_time >= heartbeat_freq:
        #     send_gfd_heartbeat(gfd_socket, lfd_name, s_name)
        #     last_gfd_sent_time = time()  # Update the last GFD sent time
        
        # receive_gfd_messages(gfd_socket, lfd_name)

        receive_heartbeat(lfd_socket, heartbeat_freq, gfd_socket, lfd_name, s_name)

        # CHECK TIMEOUT
        if time() - last_received_time > heartbeat_timeout:
            print(f"\033[1;31m[{strftime('%Y-%m-%d %H:%M:%S', localtime())}] {s_name} has died.\033[0m")
            # Send "LFDx: delete replica Sx" so GFD can remove the server as a member
            delete_txt = f"<{lfd_name},GFD,delete replica,{s_name}>"
            gfd_socket.sendall(delete_txt.encode())
            print(f"\033[1;36m[{strftime('%Y-%m-%d %H:%M:%S', localtime())}] Sending to GFD: {delete_txt}\033[0m")

            heartbeat_count = 0
            break

# def run_LFD(lfd_name, s_name, port, heartbeat_freq):
#     heartbeat_timeout = 2 * heartbeat_freq

#     # Connect with GFD -- TODO: should this happen in the while true loop??
#     gfd_socket = socket.socket()
#     gfd_port = 6881
#     gfd_ip = '127.0.0.1'  # TODO: replace with real GFD IP address
#     gfd_socket.connect((gfd_ip, gfd_port))

#     while True:
#         # connect with the server, and keep listening even if it dies 
#         try:
#             s_socket = socket.socket()
#             s_socket.settimeout(heartbeat_timeout)
#             s_port = port  
#             s_ip = '127.0.0.1'
#             s_socket.connect((s_ip, s_port))

#             send_receive_check_heartbeat(s_socket, heartbeat_freq, heartbeat_timeout, gfd_socket, lfd_name, s_name)

#         except Exception as e:  
#             # print(f"Error while trying to reconnect to server: {e}")
#             print("No new connections...: ", e)
#             sleep(heartbeat_timeout)  # Sleep before retrying the connection

# if __name__ == "__main__":
#     lfd_name = sys.argv[1]  # LFD1
#     s_name = sys.argv[2]    # S1
#     port = int(sys.argv[3])    # 6000    # TODO: is this how you do it????
#     heartbeat_freq = int(sys.argv[4])  # heartbeat frequency -- x secs
#     run_LFD(lfd_name, s_name, port, heartbeat_freq)



def run_LFD(lfd_name, s_name, port, heartbeat_freq):
    heartbeat_timeout = 2 * heartbeat_freq

    # Connect with GFD
    gfd_socket = socket.socket()
    gfd_port = 6881
    gfd_ip = '127.0.0.1'  # TODO: replace with real GFD IP address
    gfd_socket.connect((gfd_ip, gfd_port))

    # send GFD heartbeats in a thread
    gfd_heartbeat_thread = threading.Thread(target=send_gfd_heartbeat_loop, args=(gfd_socket, lfd_name, heartbeat_freq))
    gfd_heartbeat_thread.start()

    while True:
        # Connect with the server, and keep listening even if it dies 
        try:
            s_socket = socket.socket()
            s_socket.settimeout(heartbeat_timeout)
            s_port = port  
            s_ip = '127.0.0.1'
            s_socket.connect((s_ip, s_port))

            send_receive_check_heartbeat(s_socket, heartbeat_freq, heartbeat_timeout, gfd_socket, lfd_name, s_name)

        except Exception as e:  
            print("No new connections...: ", e)
            sleep(heartbeat_timeout)  # Sleep before retrying the connection

def send_gfd_heartbeat_loop(gfd_socket, lfd_name, heartbeat_freq):
    global gfd_heartbeat_count
    while True:
        # Send GFD heartbeats
        send_gfd_heartbeat(gfd_socket, lfd_name, "GFD")
        receive_gfd_messages(gfd_socket, lfd_name)
        sleep(heartbeat_freq)

if __name__ == "__main__":
    lfd_name = sys.argv[1]  # LFD1
    s_name = sys.argv[2]    # S1
    port = int(sys.argv[3])    # 6000    # TODO: is this how you do it????
    heartbeat_freq = int(sys.argv[4])  # heartbeat frequency -- x secs
    run_LFD(lfd_name, s_name, port, heartbeat_freq)
