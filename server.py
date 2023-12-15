import socket
import threading

class ChatServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.clients = []
        self.leader_election = None  # Referenz zur LeaderElection-Klasse
        self.lock = threading.Lock()

    def start(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.host, self.port))
        server_socket.listen()

        print(f"Server listening on {self.host}:{self.port}")

        while True:
            client_socket, addr = server_socket.accept()
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket, addr))
            client_thread.start()

    def handle_client(self, client_socket, addr):
        with self.lock:
            self.clients.append(client_socket)

        while True:
            try:
                message = client_socket.recv(1024).decode('utf-8')
                if not message:
                    break
                if message == "ELECTION":
                    self.leader_election.start_election(client_socket)  # Initiieren der Leader Election
                else:
                    self.broadcast(message, client_socket)
            except:
                with self.lock:
                    self.clients.remove(client_socket)
                break

    def broadcast(self, message, sender_socket):
        with self.lock:
            for client_socket in self.clients:
                if client_socket != sender_socket:
                    try:
                        client_socket.send(message.encode('utf-8'))
                    except:
                        pass

if __name__ == "__main__":
    server = ChatServer('localhost', 12345)
    server.start()
