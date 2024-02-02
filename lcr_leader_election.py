import logging
import socket
import config
import random

logging.basicConfig(level=logging.getLevelName(config.LOG_LEVEL), format=config.LOG_FORMAT)

def lcr_initiate(sock, server_id):
    try:
        sock.sendall(f'ELECTION {server_id}'.encode('utf-8'))
        logging.info(f"Election initiated with server ID: {server_id}")
    except Exception as e:
        logging.error(f"Error initiating LCR election: {e}")

def lcr_process_message(message, sock, server_id):
    logging.info(f"Received message for processing: {message}")

    parts = message.split()
    if parts[0] == 'ELECTION':
        _, incoming_id_str = parts
        incoming_id = int(incoming_id_str)
        server_id_int = int(server_id)

        if incoming_id == server_id_int:
            logging.info(f"I am the leader (ID: {server_id_int}).")
            sock.sendall(f'LEADER {server_id_int}'.encode('utf-8'))
        elif incoming_id > server_id_int:
            sock.sendall(f'ELECTION {incoming_id}'.encode('utf-8'))
            logging.info(f"Forwarding higher ID: {incoming_id}")

    elif parts[0] == 'LEADER':
        _, leader_id_str = parts
        leader_id = int(leader_id_str)
        logging.info(f"Leader has been elected with ID: {leader_id}")

def elect_new_leader():
    global servers
    if servers:
        sorted_servers = sorted(servers.items(), key=lambda x: x[1]) 
        lowest_id = sorted_servers[0][1]
        logging.info(f"New leader elected: Server ID {lowest_id}")
        return lowest_id
    else:
        logging.error("No available servers to elect as a new leader.")
        return None
