import threading
import time
import socket

# Eine Liste zum Speichern der verbundenen Clients
connected_clients = []

# Mutex für kritische Abschnitte
mutex = threading.Lock()

# Variable zum Speichern der aktuellen Leader-Informationen
current_leader = None

# Funktion zum Überprüfen, ob dieser Server der Leader ist
def is_leader():
    global current_leader
    return current_leader == threading.current_thread()

# Funktion zum Senden einer Leader-Election-Nachricht an alle verbundenen Clients
def send_leader_election_message():
    global connected_clients
    for client_socket, _ in connected_clients:
        try:
            client_socket.send("ELECTION".encode('utf-8'))
        except socket.error:
            connected_clients.remove((client_socket, ''))

# Funktion zum Durchführen der Leader-Election
def leader_election():
    global current_leader
    global mutex

    while True:
        time.sleep(10)  # Wartezeit zwischen den Leader-Wahlen

        with mutex:
            if is_leader():
                # Wenn dieser Server der Leader ist, sende Leader-Election-Nachrichten an die Clients
                send_leader_election_message()
            else:
                # Wenn dieser Server nicht der Leader ist, überprüfe, ob der Leader noch aktiv ist
                if current_leader and current_leader not in threading.enumerate():
                    current_leader = None

        # Führe Leader-Election nur aus, wenn es keinen aktuellen Leader gibt
        with mutex:
            if current_leader is None:
                # Setze diesen Server als den Leader
                current_leader = threading.Thread(target=select_leader)
                current_leader.start()

# Funktion zum Auswählen des Leaders
def select_leader():
    global connected_clients
    global current_leader

    with mutex:
        if connected_clients:
            leader_socket, leader_name = connected_clients[0]
            broadcast(f"{leader_name} is the leader.", leader_socket)
            print(f"{leader_name} is the leader.")

# Funktion zum Senden einer Nachricht an alle verbundenen Clients
def broadcast(message, excluded_client_socket=None):
    global connected_clients
    for client_socket, _ in connected_clients:
        if client_socket != excluded_client_socket:
            try:
                client_socket.send(message.encode('utf-8'))
            except socket.error:
                connected_clients.remove((client_socket, ''))

# Funktion zum Starten des Servers und Akzeptieren von Client-Verbindungen
def start_server():
    global connected_clients
    global current_leader

    host, port = "localhost", 12345  # Beispielwerte

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

# Funktion zum Weiterleiten einer Nachricht an den Leader
def forward_message_to_leader(message, client_socket):
    global current_leader

    if current_leader:
        try:
            current_leader.send(message.encode('utf-8'))
        except socket.error:
            # Fehlerbehandlung, wenn die Verbindung zum Leader fehlschlägt
            pass

# Funktion zum Ausgeben der Liste der verbundenen Clients
def list_clients():
    global connected_clients
    print("Connected Clients:")
    for _, client_name in connected_clients:
        print(f"- {client_name}")

if __name__ == "__main__":
    # Starte den Leader-Election-Thread
    election_thread = threading.Thread(target=leader_election)
    election_thread.start()

    # Starte den Server
    start_server()
