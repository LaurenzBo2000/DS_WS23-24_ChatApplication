import threading
import time
import socket
import os
from server_manager import get_active_server

# Eine Liste zum Speichern der verbundenen Clients
connected_clients = []

# Dateiname für die Chat-Speicherung
CHAT_LOG_FILE = "chat_log.txt"

# Mutex für kritische Abschnitte
mutex = threading.Lock()

# Variable zum Speichern der aktuellen Leader-Informationen
current_leader = None

# Funktion zum Speichern einer Nachricht im Chat-Log
def save_to_chat_log(message):
    with open(CHAT_LOG_FILE, "a") as chat_log:
        chat_log.write(message + "\n")

# Funktion zum Laden des Chat-Logs beim Starten des Servers
def load_chat_log():
    if os.path.exists(CHAT_LOG_FILE):
        with open(CHAT_LOG_FILE, "r") as chat_log:
            return chat_log.readlines()
    return []

# Funktion zum Ausgeben der Liste der verbundenen Clients
def list_clients():
    global connected_clients
    print("Connected Clients:")
    for _, client_name in connected_clients:
        print(f"- {client_name}")

# Funktion zum Weiterleiten einer Nachricht an den Leader
def forward_message_to_leader(message, client_socket):
    global current_leader

    if current_leader:
        try:
            broadcast(message, client_socket)
            current_leader.send(message.encode('utf-8'))
        except socket.error:
            # Fehlerbehandlung, wenn die Verbindung zum Leader fehlschlägt
            pass

# Funktion zum Behandeln der Kommunikation mit einem Client
def handle_client(client_socket, client_name):
    global connected_clients
    global current_leader

    while True:
        try:
            received_data = client_socket.recv(1024).decode('utf-8')
            print(f"{client_name}: {received_data}")

            if received_data.lower() == 'exit':
                break
            elif received_data.lower() == 'list':
                list_clients()
            else:
                broadcast(f"{client_name}: {received_data}", client_socket)
                forward_message_to_leader(f"{client_name}: {received_data}", client_socket)
        except socket.error:
            break

    print(f"{client_name} left the chat")
    broadcast(f"{client_name} left the chat", client_socket)

    client_socket.close()
    connected_clients.remove((client_socket, client_name))

# Funktion zum Starten des Servers und Akzeptieren von Client-Verbindungen
def start_server():
    global connected_clients
    global current_leader

    # Laden des vorhandenen Chat-Logs beim Starten des Servers
    chat_log = load_chat_log()
    for log_entry in chat_log:
        print(log_entry.strip())

    # Starte den Leader-Election-Thread
    election_thread = threading.Thread(target=leader_election)
    election_thread.start()

    host, port = get_active_server()  # Verwende die Adresse des aktiven Servers

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)

    print(f"Server listening on {host}:{port}")

    while True:
        client_socket, client_address = server_socket.accept()
        print(f"Connection established with {client_address}")

        # Erfrage den Namen des Clients
        client_name = client_socket.recv(1024).decode('utf-8')
        print(f"{client_name} joined the chat")
        broadcast(f"{client_name} joined the chat", client_socket)

        # Füge den verbundenen Client zur Liste hinzu
        connected_clients.append((client_socket, client_name))

        # Starte einen separaten Thread für die Client-Behandlung
        client_handler = threading.Thread(target=handle_client, args=(client_socket, client_name))
        client_handler.start()

if __name__ == "__main__":
    start_server()