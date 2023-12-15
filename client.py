import socket
import threading
from server_manager import get_active_server

def receive_messages(client_socket):
    # Funktion zum Empfangen von Nachrichten vom Server und Anzeigen auf der Konsole
    # Beendet die Verbindung, wenn 'exit' empfangen wird
    while True:
        try:
            received_data = client_socket.recv(1024).decode('utf-8')
            print(received_data)
            if received_data.lower() == 'exit':
                break
        except socket.error:
            break

    client_socket.close()

def start_client():
    host, port = get_active_server()  # Verwende die Adresse des aktiven Servers

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))

    # Erfrage den Namen des Clients
    client_name = input("Enter your name: ")
    client_socket.send(client_name.encode('utf-8'))

    print(f"Connected to {host}:{port}")

    # Starte einen separaten Thread für den Nachrichtenempfang
    receive_handler = threading.Thread(target=receive_messages, args=(client_socket,))
    receive_handler.start()

    while True:
        message = input()
        client_socket.send(message.encode('utf-8'))
        if message.lower() == 'exit':
            break

        # Zusätzlicher Code zum Weiterleiten der Nachricht an den Leader
        forward_message_to_leader(f"{client_name}: {message}", client_socket)

    # Sende eine Abschiedsnachricht und beende den Client
    client_socket.send('exit'.encode('utf-8'))
    client_socket.close()

if __name__ == "__main__":
    start_client()
