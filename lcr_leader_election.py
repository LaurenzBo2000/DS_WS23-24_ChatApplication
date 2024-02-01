import logging
import socket
import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def lcr_initiate(sock, server_id):
    """
    Initiates the LCR leader election process.
    """
    try:
        sock.sendall(f'ELECTION {server_id}'.encode('utf-8'))
        logging.info(f"Election initiated with server ID: {server_id}")
    except Exception as e:
        logging.error(f"Error initiating LCR election: {e}")

def lcr_process_message(message, sock, server_id, servers):
    """
    Process an incoming election or leader announcement message.
    """
    logging.info(f"Received message for processing: {message}")

    parts = message.split()
    if parts[0] == 'ELECTION':
        _, incoming_id_str = parts
        incoming_id = int(incoming_id_str)
        server_id_int = int(server_id)

        if incoming_id == server_id_int:
            logging.info(f"I am the leader (ID: {server_id_int}).")
            sock.sendall(f'LEADER {server_id_int}'.encode('utf-8'))
            broadcast_new_leader(servers, server_id_int)
        elif incoming_id > server_id_int:
            sock.sendall(f'ELECTION {incoming_id}'.encode('utf-8'))
            logging.info(f"Forwarding higher ID: {incoming_id}")

    elif parts[0] == 'LEADER':
        _, leader_id_str = parts
        leader_id = int(leader_id_str)
        logging.info(f"Leader has been elected with ID: {leader_id}")
        broadcast_new_leader(servers, leader_id)

def broadcast_new_leader(servers, new_leader_id):
    """
    Broadcast the new leader to all servers.
    """
    for server in servers.values():
        try:
            server.sendall(f'NEW_LEADER {new_leader_id}'.encode('utf-8'))
        except Exception as e:
            logging.error(f"Error broadcasting new leader: {e}")

def elect_new_leader(servers):
    """
    Elect a new leader based on the lowest server ID.
    """
    if servers:
        sorted_servers = sorted(servers.items(), key=lambda x: x[1])
        lowest_id = sorted_servers[0][1]
        logging.info(f"New leader elected: Server ID {lowest_id}")
        return lowest_id
    else:
        logging.error("No available servers to elect as a new leader.")
        return None
