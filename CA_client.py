'''
send_msg(sock)

Purpose: Handles sending messages from the client to the server.
Functionality: Runs in a loop, waiting for user input to send as a message. Special commands like "QUIT" and "ELECTION" trigger respective actions.
Exception Handling: Catches general exceptions for issues during message sending.

receive_msg(sock)

Purpose: Manages receiving messages from the server.
Functionality: Continuously listens for incoming messages from the server. Processes special messages related to the leader election and prints other messages to the console.
Exception Handling: Handles ConnectionResetError and OSError for issues like server disconnection or socket errors.
'''

import socket
import threading
import sys
import logging
import time

from heartbeat import send_heartbeat 
from lcr_leader_election import lcr_initiate, lcr_process_message 

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 65432 


def send_msg(sock):
    logging.info("Sending message thread started")

    while True:
        time.sleep(0.5)  
        print("\nAvailable Commands:")
        print("  - 'QUIT' to exit.")
        print("  - 'ELECTION' to initiate leader election.")
        print("  - Any other message to send to the server.\n")

        try:
            msg = input("Enter command or message: ")
            if msg == "QUIT":
                logging.info("Client is shutting down.")
                sock.close()
                sys.exit()
            elif msg == "ELECTION":
                lcr_initiate(client_id, sock)
            else:
                sock.sendall(msg.encode('utf-8'))
        except Exception as e:
            logging.error(f"Error sending message: {e}")
            break


def receive_msg(sock):
    logging.info("Receiving message thread started")

    while True:
        try:
            message = sock.recv(1024).decode('utf-8')
            if message.startswith('ELECTION') or message.startswith('LEADER'):
                lcr_process_message(client_id, message, sock)
            elif message:
                logging.info(f"Server says: {message}")
            else:
                logging.warning("Disconnected from the server.")
                sock.close()
                break
        except ConnectionResetError:
            logging.warning("Connection reset by server.")
            sock.close()
            break
        except OSError as e:
            logging.error(f"OSError: {e}")
            break

def main():
    global client_id
    client_id = input("Enter your client ID: ")
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((SERVER_HOST, SERVER_PORT))
    except ConnectionRefusedError:
        logging.error("Cannot connect to the server. Make sure the server is running.")
        sys.exit()

    heartbeat_thread = threading.Thread(target=send_heartbeat, args=(client_socket,))
    heartbeat_thread.start()

    thread_send = threading.Thread(target=send_msg, args=(client_socket,))
    thread_send.start()

    thread_receive = threading.Thread(target=receive_msg, args=(client_socket,))
    thread_receive.start()

if __name__ == '__main__':
    main()
