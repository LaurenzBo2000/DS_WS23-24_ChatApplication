'''
send_heartbeat(client_socket, interval)

Purpose: Sends regular heartbeat messages to the server.
Functionality: Runs in a loop, sending a "HEARTBEAT" message to the server at regular intervals.
Exception Handling: Handles exceptions related to lost server connection and socket issues.

HeartbeatChecker Class:

Key Methods:

update_heartbeat(client_socket): Updates the timestamp for a client's last heartbeat.
remove_client(client_socket): Removes a client from the heartbeat tracking, usually when a timeout is detected.
check_heartbeats(): Regularly checks for clients that haven't sent a heartbeat within the timeout period and removes them
'''

import threading
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def send_heartbeat(client_socket, interval=5):
    """
    Sends a heartbeat to the server every 'interval' seconds.
    """
    logging.info("Heartbeat thread started")

    while True:
        try:
            client_socket.sendall(b'HEARTBEAT')
            time.sleep(interval)
        except (ConnectionResetError, BrokenPipeError, OSError) as e:
            logging.error(f"Disconnected from the server. Stopping heartbeat. Error: {e}")
            break

class HeartbeatChecker:
    def __init__(self, timeout=10):
        self.heartbeats = {}
        self.timeout = timeout
        self.lock = threading.Lock()

    def update_heartbeat(self, client_socket):
        with self.lock:
            self.heartbeats[client_socket] = time.time()
            logging.info(f"Heartbeat updated for {client_socket.getpeername()}")

    def remove_client(self, client_socket):
        with self.lock:
            if client_socket in self.heartbeats:
                del self.heartbeats[client_socket]
                logging.info(f"Client {client_socket.getpeername()} removed from heartbeat tracking")

    def check_heartbeats(self):
        current_time = time.time()
        with self.lock:
            to_remove = [client_socket for client_socket, timestamp in self.heartbeats.items()
                         if current_time - timestamp > self.timeout]
            for client_socket in to_remove:
                logging.warning(f"Client {client_socket.getpeername()} timed out.")
                self.remove_client(client_socket)
                try:
                    client_socket.close()
                except OSError as e:
                    logging.error(f"Error closing client socket: {e}")

    def start_heartbeat_checking(self):
        while True:
            self.check_heartbeats()
            time.sleep(5)

def periodic_heartbeat_check(heartbeat_checker):
    while True:
        heartbeat_checker.check_heartbeats()
        time.sleep(5)
