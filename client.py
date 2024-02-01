import socket
import threading
import sys
import logging
import time
import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_unique_client_id():
    client_input_id = input("Enter your client ID: ").strip()
    unique_client_id = f"{client_input_id}-{int(time.time())}"
    return unique_client_id

def discover_leader_server():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.settimeout(5)
        try:
            s.sendto(b'DISCOVER', ('<broadcast>', config.DISCOVERY_PORT))
            data, addr = s.recvfrom(1024)
            leader_info = data.decode()
            if leader_info.startswith('LEADER:'):
                leader_id = leader_info.split(':')[1]
                return leader_id
        except socket.timeout:
            logging.error("Leader server discovery timeout.")
            return None

def send_msg(sock, stop_event, client_id):
    logging.info("Sending message thread started")
    print("\nAvailable Commands:")
    print("  - 'QUIT' to exit.")
    print("  - Any other message to send to the server.\n")
    while not stop_event.is_set():
        try:
            msg = input("Enter command or message: ")
            if msg == "QUIT":
                sock.sendall("QUIT".encode('utf-8'))
                logging.info("Client is shutting down.")
                stop_event.set()
                break
            else:
                complete_msg = f"{client_id}: {msg}"
                logging.info(f"Sending message: {complete_msg}") 
                sock.sendall(complete_msg.encode('utf-8'))
        except Exception as e:
            logging.error(f"Error sending message: {e}")
            break

def receive_msg(sock, stop_event, disconnected_event):
    logging.info("Receiving message thread started")
    while not stop_event.is_set():
        try:
            message = sock.recv(1024).decode('utf-8')
            if message:
                logging.info(f"Server says: {message}")
            else:
                logging.warning("Disconnected from the server.")
                disconnected_event.set()
                stop_event.set()
                break
        except ConnectionResetError:
            logging.warning("Connection reset by server.")
            disconnected_event.set()
            stop_event.set()
            break
        except OSError as e:
            logging.error(f"OSError: {e}")
            disconnected_event.set()
            stop_event.set()
            break

def connect_to_server(client_id):
    while True:
        leader_id = discover_leader_server()
        if leader_id:
            try:
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server_ip = '192.168.100.171'
                logging.info(f"Attempting to connect to leader server at {server_ip}:{config.SERVER_PORT}")
                client_socket.connect((server_ip, config.SERVER_PORT))
                logging.info("Connection successful.")
                client_socket.sendall(f"CLIENT_ID {client_id}".encode('utf-8'))
                return client_socket
            except Exception as e:
                logging.error(f"Error connecting to the leader server: {e}")
        else:
            logging.error("Failed to discover leader server. Retrying in 5 seconds...")
        time.sleep(5)
def main():
    client_id = get_unique_client_id()
    logging.info(f"Your unique client ID is: {client_id}")

    while True:
        client_socket = connect_to_server(client_id)
        stop_event = threading.Event()
        disconnected_event = threading.Event()  

        thread_send = threading.Thread(target=send_msg, args=(client_socket, stop_event, client_id))
        thread_receive = threading.Thread(target=receive_msg, args=(client_socket, stop_event, disconnected_event))

        thread_send.start()
        thread_receive.start()

        thread_send.join()
        thread_receive.join()

        if disconnected_event.is_set():
            logging.info("Server disconnected. Attempting to reconnect to the new leader server.")
            client_socket.close()
            time.sleep(5) 
            continue
        elif stop_event.is_set():
            logging.info("Client is shutting down.")
            client_socket.close()
            break

if __name__ == '__main__':
    main()
