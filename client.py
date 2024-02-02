import socket
import threading
import time
import config

serverIP = config.SERVER

class Client:
    def __init__(self, client_id):
        self.client_id = client_id
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.connected_server_port = self.find_active_server()

    def find_active_server(self):
        while config.base_port <= config.max_port:
            try:
                self.socket.sendto('test'.encode(), (serverIP, config.base_port))
                self.socket.settimeout(2)
                response, _ = self.socket.recvfrom(1024)
                if response.decode() == "ack":
                    print(f"Connected to server on port {config.base_port}")
                    return config.base_port
            except socket.error:
                print(f"No server on port {config.base_port}")
            config.base_port += 1
        print("No active servers found. Exiting.")
        exit()

    def update_server_heartbeat(self, server_socket):
        with self.lock:
            self.server_heartbeats[server_socket] = time.time()

    def check_heartbeats(self):
        current_time = time.time()
        with self.lock:
            to_remove_servers = [server_socket for server_socket, timestamp in self.server_heartbeats.items()
                                 if current_time - timestamp > 2]
            for server_socket in to_remove_servers:
                self.remove_server(server_socket)

    def remove_server(self, server_socket):
        with self.lock:
            if server_socket in self.server_heartbeats:
                del self.server_heartbeats[server_socket]

    def send_message(self, message):
        full_message = f"msg:{message}"
        self.socket.sendto(full_message.encode(), (serverIP, self.connected_server_port))

    def listen_for_messages(self):
        while True:
            try:
                message, _ = self.socket.recvfrom(1024)
                print(f"\nReceived message: {message.decode()}\nEnter message: ", end="")
            except socket.timeout:
                continue
            except socket.error:
                print("\nLost connection to the server. Attempting to reconnect...")
                self.connected_server_port = self.find_active_server()
                self.join_chat()

    def join_chat(self):
        join_message = f"join:{self.client_id}"
        self.socket.sendto(join_message.encode(), (serverIP, self.connected_server_port))

    def run(self):
        self.join_chat()
        threading.Thread(target=self.listen_for_messages, daemon=True).start()

        try:
            while True:
                message = input("Enter message: ")
                if message:
                    self.send_message(message)
        except KeyboardInterrupt:
            print("\nClient exiting...")

def main():
    client_id = input("Enter your client ID: ")
    client = Client(client_id)
    client.run()

if __name__ == "__main__":
    main()
