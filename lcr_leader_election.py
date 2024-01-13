'''
lcr_initiate(client_id, client_socket)
Purpose: Initiates the leader election process.
Functionality: Sends an "ELECTION" message with the client's ID to the server, starting the LCR algorithm for leader election.


lcr_process_message(client_id, message, client_socket)
Purpose: Processes incoming election messages for the LCR algorithm.
Functionality: Parses the election message, compares IDs, and decides whether to declare itself as the leader, forward a higher ID, or ignore the message.
Exception Handling: Catches ValueError for parsing issues in the incoming message.
'''

import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def lcr_initiate(client_id, client_socket):
    """
    Initiate the LCR leader election algorithm.
    """
    try:
        client_socket.sendall(f'ELECTION {client_id}'.encode('utf-8'))
        logging.info(f"Election initiated with ID: {client_id}")
    except Exception as e:
        logging.error(f"Error initiating LCR election: {e}")

def lcr_process_message(client_id, message, client_socket):
    """
    Process an incoming election message.
    """
    try:
        text, incoming_id_str = message.split()
        incoming_id = int(incoming_id_str)
        client_id_int = int(client_id) 
    except ValueError as e:
        logging.error(f"Invalid message format: {message}. Error: {e}")
        return False

    if text != 'ELECTION':
        logging.warning(f"Unexpected message type: {text}")
        return False

    if incoming_id == client_id_int:
        logging.info(f"I am the leader (ID: {client_id}).")
        client_socket.sendall(f'LEADER {client_id}'.encode('utf-8'))
        return True
    elif incoming_id > client_id_int:
        client_socket.sendall(f'ELECTION {incoming_id}'.encode('utf-8'))
        logging.info(f"Forwarding higher ID: {incoming_id}")

    return True
