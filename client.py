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

def send_msg(sock, stop_event):
    logging.info("Sending message thread started")

    print("\nAvailable Commands:")
    print("  - 'QUIT' to exit.")
    print("  - 'ELECTION' to initiate leader election.")
    print("  - 'SIMULATE_CRASH' to simulate a server crash.")
    print("  - Any other message to send to the server.\n")

    while not stop_event.is_set():
        try:
            msg = input("Enter command or message: ")
            if msg == "QUIT":
                sock.sendall("QUIT".encode('utf-8'))
                logging.info("Client is shutting down.")
                stop_event.set()
                break
            elif msg == "ELECTION":
                lcr_initiate(client_id, sock)
            else:
                sock.sendall(msg.encode('utf-8'))
        except Exception as e:
            logging.error(f"Error sending message: {e}")
            break

    # try:
    #     sock.shutdown(socket.SHUT_RDWR)
    #     sock.close()
    # except Exception as e:
    #     logging.error(f"Error closing socket: {e}")

def receive_msg(sock, stop_event):
    logging.info("Receiving message thread started")

    while not stop_event.is_set():
        try:
            message = sock.recv(1024).decode('utf-8')
            if message == 'SERVER_CRASH':
                logging.warning("Server crash simulated. Initiating leader election.")
                lcr_initiate(client_id, sock)
            elif message.startswith('ELECTION') or message.startswith('LEADER'):
                lcr_process_message(client_id, message, sock)
            elif message:
                logging.info(f"Server says: {message}")
            else:
                logging.warning("Disconnected from the server.")
                stop_event.set()
                break
        except ConnectionResetError:
            logging.warning("Connection reset by server.")
            stop_event.set()
            break
        except OSError as e:
            logging.error(f"OSError: {e}")
            stop_event.set()
            break

    # Close the socket here only if the stop_event is set
    if stop_event.is_set():
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except OSError as e:
            logging.error(f"Error closing socket after receiving: {e}")
        finally:
            sock.close()

def main():
    global client_id
    client_id = input("Enter your client ID: ")
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client_socket.connect((SERVER_HOST, SERVER_PORT))
        client_socket.sendall(client_id.encode('utf-8'))
        time.sleep(0.5)
    except ConnectionRefusedError:
        logging.error("Cannot connect to the server. Make sure the server is running.")
        sys.exit()
    except Exception as e:
        logging.error(f"Error sending client ID: {e}")
        client_socket.close()
        sys.exit()
    stop_event = threading.Event()

    heartbeat_thread = threading.Thread(target=send_heartbeat, args=(client_socket, stop_event))

    heartbeat_thread.start()

    thread_send = threading.Thread(target=send_msg, args=(client_socket, stop_event))
    thread_receive = threading.Thread(target=receive_msg, args=(client_socket, stop_event))

    thread_send.start()
    thread_receive.start()

    heartbeat_thread.join()
    thread_send.join()
    thread_receive.join()

if __name__ == '__main__':
    main()
