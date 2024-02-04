#import necessary libraries
import threading
import time
import logging
import socket
import config

logging.basicConfig(level=logging.getLevelName(config.LOG_LEVEL), format=config.LOG_FORMAT)

#Define the HeartbeatChecker class
class HeartbeatChecker:

    #Initialize the HeartbeatChecker object
    def __init__(self):
        self.server_heartbeats = {}
        self.lock = threading.Lock()

    #Method to update the heartbeat timestamp for a given server
    def update_server_heartbeat(self, server_socket):
        with self.lock:
            self.server_heartbeats[server_socket] = time.time()
            logging.info(f"Server heartbeat updated for {server_socket.getpeername()}")

    #Method to check and remove servers with expired heartbeats
    def check_heartbeats(self):
        current_time = time.time()
        with self.lock:
            to_remove_servers = [server_socket for server_socket, timestamp in self.server_heartbeats.items()
                                 if current_time - timestamp > config.LEADER_HEARTBEAT_TIMEOUT]
            for server_socket in to_remove_servers:
                logging.warning(f"Server {server_socket.getpeername()} timed out.")
                self.remove_server(server_socket)

    #Method to remove a server from the list of tracked heartbeats
    def remove_server(self, server_socket):
        with self.lock:
            if server_socket in self.server_heartbeats:
                del self.server_heartbeats[server_socket]
                logging.info(f"Server {server_socket.getpeername()} removed from heartbeat tracking")

    #Method to check if a leader's heartbeat is missing
    def is_leader_heartbeat_missing(self):
        current_time = time.time()
        with self.lock:
            for _, timestamp in self.server_heartbeats.items():
                if current_time - timestamp <= config.LEADER_HEARTBEAT_TIMEOUT:
                    return False
            return True

    #Method to start the heartbeat checking loop
    def start_heartbeat_checking(self):
        while True:
            self.check_heartbeats()
            time.sleep(config.HEARTBEAT_INTERVAL)

#Method to send heartbeat messages to the server
def send_heartbeat(server_socket):
    logging.info("Server heartbeat thread started")
    while True:
        try:
            server_socket.sendall(b'HEARTBEAT')
            time.sleep(config.HEARTBEAT_INTERVAL)
        except (ConnectionResetError, BrokenPipeError, OSError) as e:
            logging.error(f"Disconnected from the server. Stopping heartbeat. Error: {e}")
            break
