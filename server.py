import socket
import threading
import selectors
import logging
import config
import os
import time
from heartbeat import HeartbeatChecker
from lcr_leader_election import lcr_initiate, lcr_process_message, elect_new_leader

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

sel = selectors.DefaultSelector()
heartbeat_checker = HeartbeatChecker()
server_lock = threading.Lock()
servers = {}
leader_server = None
is_leader = False
clients = {}

def get_own_id():
    return f"{socket.gethostname()}-{os.getpid()}"

def broadcast_to_clients(message, sender_id=None):
    with server_lock:
        logging.info(f"Broadcasting message to clients: {message}")
        for client_id, conn in clients.items():
            if client_id != sender_id:
                try:
                    conn.send(message.encode('utf-8'))
                except Exception as e:
                    logging.error(f"Error broadcasting to client {client_id}: {e}")
                    remove_client(conn, client_id)


def handle_client(conn, client_id):
    global clients
    logging.info(f"New client connection: {client_id}")
    clients[client_id] = conn

    while True:
        try:
            msg = conn.recv(1024).decode('utf-8')
            if msg:
                logging.info(f"Received message from client {client_id}: {msg}")
                broadcast_to_clients(msg, client_id)
            else:
                break
        except Exception as e:
            logging.error(f"Error with client {client_id}: {e}")
            break

    remove_client(conn, client_id)

def remove_client(conn, client_id):
    with server_lock:
        if client_id in clients:
            del clients[client_id]
            conn.close()
            logging.info(f"Client {client_id} disconnected")

def handle_discovery_request():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('', config.DISCOVERY_PORT))
        while True:
            try:
                data, addr = s.recvfrom(1024)
                if data == b'DISCOVER':
                    s.sendto(f"LEADER:{get_own_id()}".encode(), addr)
            except Exception as e:
                logging.error(f"Error in discovery request handling: {e}")

def handle_server(conn, addr):
    global leader_server, is_leader, servers
    server_id = None
    client_id = None
    logging.info(f"New server connection from {addr}")
    connected = True

    while connected:
        try:
            msg = conn.recv(1024).decode('utf-8')
            if msg:
                logging.info(f"Received message from server {addr}: {msg}")
                if msg == 'HEARTBEAT':
                    heartbeat_checker.update_server_heartbeat(conn)
                elif msg.startswith('ELECTION'):
                    _, server_id = msg.split(maxsplit=1)
                    lcr_initiate(conn, server_id)
                elif msg.startswith('LEADER'):
                    leader_server = lcr_process_message(msg, conn, server_id, servers)
                    is_leader = leader_server == get_own_id()
                elif msg.startswith('CLIENT_ID'):
                    client_id = msg.split(' ', 1)[1]
                    logging.info(f"Received client ID from {addr}: {client_id}")
                    handle_client(conn, client_id)
                elif msg == 'QUIT':
                    connected = False
        except BlockingIOError:
            continue
        except ConnectionResetError:
            logging.warning(f"Connection lost with server {addr}")
            connected = False
        except Exception as e:
            logging.error(f"Error with server {addr}: {e}")
            connected = False

    remove_server(conn, addr, server_id)


def remove_server(conn, addr=None, server_id=None):
    global leader_server
    with server_lock:
        if conn in servers:
            del servers[conn]
            conn.close()

        if server_id and server_id == leader_server:
            new_leader_id = elect_new_leader(servers)
            if new_leader_id:
                leader_server = new_leader_id
                broadcast_to_servers(f"NEW_LEADER {new_leader_id}")

    if addr:
        logging.info(f"Server connection closed with {addr}")
    if server_id:
        logging.info(f"Server {server_id} disconnected")

def start_leader_role():
    global is_leader, leader_server
    is_leader = True
    leader_server = get_own_id()
    logging.info("Server is now acting as the leader")
    broadcast_to_servers(f"NEW_LEADER {get_own_id()}")

def start_follower_role(leader_addr):
    global is_leader
    is_leader = False
    try:
        leader_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        leader_socket.connect((leader_addr, config.SERVER_PORT))
        logging.info(f"Connected to leader server at {leader_addr}")
        thread = threading.Thread(target=handle_server, args=(leader_socket, (leader_addr, config.SERVER_PORT)))
        thread.start()
    except Exception as e:
        logging.error(f"Error connecting to leader server: {e}")

def monitor_leader_heartbeat():
    global leader_server, is_leader, servers
    while not is_leader:
        time.sleep(config.LEADER_HEARTBEAT_TIMEOUT)
        if heartbeat_checker.is_leader_heartbeat_missing():
            logging.warning("Leader heartbeat missing. Initiating leader election.")
            if len(servers) > 1:
                new_leader = elect_new_leader(servers)
                if new_leader == get_own_id():
                    start_leader_role()
                else:
                    start_follower_role(str(new_leader))
            else:
                start_leader_role()
                broadcast_to_servers(f"NEW_LEADER {get_own_id()}", None)


def get_next_available_port(start_port):
    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("", start_port))
                return start_port
        except OSError:
            start_port += 1

def initialize_server():
    global SERVER_PORT  
    SERVER_PORT = get_next_available_port(config.SERVER_PORT)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('0.0.0.0', SERVER_PORT))
    server_socket.listen(100)
    server_socket.setblocking(False)
    sel.register(server_socket, selectors.EVENT_READ, data=None)

    logging.info(f"Server is listening on {config.SERVERS[0]}:{SERVER_PORT}")

    heartbeat_thread = threading.Thread(target=heartbeat_checker.start_heartbeat_checking)
    leader_heartbeat_thread = threading.Thread(target=monitor_leader_heartbeat)

    heartbeat_thread.start()
    leader_heartbeat_thread.start()

    try:
        while True:
            events = sel.select(timeout=None)
            for key, mask in events:
                if key.fileobj is server_socket:
                    accept_server_connection(key.fileobj)
    except KeyboardInterrupt:
        logging.info("Server is shutting down.")
    finally:
        sel.close()
        server_socket.close()

def broadcast_to_servers(msg, sender_conn=None):
    with server_lock:
        for conn in servers.values():
            if conn != sender_conn:
                try:
                    conn.send(msg.encode('utf-8'))
                except Exception as e:
                    logging.error(f"Error in sending message to server: {e}")
                    remove_server(conn)

def accept_server_connection(sock):
    conn, addr = sock.accept()
    logging.info(f"Accepted server connection from {addr}")
    conn.setblocking(False)
    sel.register(conn, selectors.EVENT_READ, data=None)
    with server_lock:
        servers[conn] = conn
    heartbeat_checker.update_server_heartbeat(conn)
    thread = threading.Thread(target=handle_server, args=(conn, addr))
    thread.start()

if __name__ == '__main__':
    discovery_thread = threading.Thread(target=handle_discovery_request)
    discovery_thread.start()
    initialize_server()
