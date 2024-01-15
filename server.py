'''
handle_client(conn, addr)

Purpose: Manages communication with individual clients.
Functionality: Runs in a separate thread for each client. Handles incoming messages from a client and decides whether to update the heartbeat, initiate the leader election process, or broadcast the message to other clients.
Exceptions Handled:
BlockingIOError for non-blocking socket operations.
ConnectionResetError for lost client connections.
General exceptions for any other errors.

broadcast(msg, sender_conn)

Purpose: Broadcasts a message to all connected clients except the sender.
Functionality: Iterates through all connected clients and sends the message. If sending fails (due to a broken connection), the connection is closed and removed from the list of active connections.
Thread Safety: Uses a lock to ensure thread-safe modification of the global connections list.

accept_wrapper(sock)

Purpose: Accepts new client connections.
Functionality: Waits for new connections, accepts them, sets them to non-blocking, registers them with the selector, and starts a new thread for handling client communication.
Exception Handling: Catches BlockingIOError if no incoming connections are present.

'''

import socket
import threading
import selectors
from heartbeat import HeartbeatChecker
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

sel = selectors.DefaultSelector()
heartbeat_checker = HeartbeatChecker()
connections_lock = threading.Lock()
connections = {}
client_ids = {}

def handle_client(conn, addr):
    client_id = None
    logging.info(f"New connection from {addr}")
    connected = True
    while connected:
        try:
            msg = conn.recv(1024).decode('utf-8')
            if msg:
                logging.info(f"Received message from {addr}: {msg}")
                if msg == 'HEARTBEAT':
                    heartbeat_checker.update_heartbeat(conn)
                    continue
                elif msg.startswith('ELECTION') or msg.startswith('LEADER'):
                    broadcast(msg, conn)
                elif msg == 'QUIT':
                    if client_id is not None:
                        broadcast(f"Client {client_id} left the chat", conn)
                    connected = False
                elif msg == 'SIMULATE_CRASH':
                    logging.info("Simulating server crash.")
                    broadcast("SERVER_CRASH", conn)
                    time.sleep(5) 
                    logging.info("Server resumed after simulated crash.")
                else:
                    if client_id is None:
                        client_id = msg
                        client_ids[conn] = client_id
                        broadcast(f"Client {client_id} joined the chat", conn)
                    else:
                        broadcast(f"{client_ids[conn]}: {msg}", conn)
        except BlockingIOError:
            continue 
        except ConnectionResetError:
            logging.warning(f"Connection lost with {addr}")
            connected = False
        except Exception as e:
            logging.error(f"Error with {addr}: {e}")
            connected = False

    try:
        sel.unregister(conn)
    except KeyError:
        logging.warning("Connection not registered or already unregistered")
    with connections_lock:
        if conn in connections:
            del connections[conn]  
            if conn in client_ids:
                del client_ids[conn]
    heartbeat_checker.remove_client(conn)
    conn.close()

def broadcast(msg, sender_conn):
    with connections_lock:
        for conn in connections.values(): 
            if conn is not sender_conn:
                try:
                    conn.send(msg.encode('utf-8'))
                except:
                    logging.error("Error in sending message, closing connection")
                    conn.close()
                    del connections[conn]
                    if conn in client_ids:
                        del client_ids[conn]

def accept_wrapper(sock):
    try:
        conn, addr = sock.accept()
        logging.info(f"Accepted connection from {addr}")
        conn.setblocking(False)
        sel.register(conn, selectors.EVENT_READ, data=None)
        with connections_lock:
            connections[conn] = conn
        heartbeat_checker.update_heartbeat(conn)
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
    except BlockingIOError:
        pass

HOST = '127.0.0.1'
PORT = 65432

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen(100)
server_socket.setblocking(False)
sel.register(server_socket, selectors.EVENT_READ, data=None)

logging.info(f"Server is listening on {HOST}:{PORT}")

heartbeat_thread = threading.Thread(target=heartbeat_checker.start_heartbeat_checking)
heartbeat_thread.start()

try:
    while True:
        events = sel.select(timeout=None)
        for key, mask in events:
            if key.fileobj is server_socket:
                accept_wrapper(key.fileobj)
            else:
                pass
except KeyboardInterrupt:
    logging.info("Server is shutting down.")
finally:
    sel.close()
    server_socket.close()
