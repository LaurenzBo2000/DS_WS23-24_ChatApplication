#import necessary libraries
import socket
import threading
import time
import uuid
import random
import config

#Set the server IP address from the configuration
serverIP = config.SERVER

#Define the Server class
class Server:
    #Initialize the Server object with a given port
    def __init__(self, port):
        self.uuid = uuid.uuid4()
        self.host = serverIP
        self.port = port
        self.leader = None
        self.active_servers = {} 
        self.clients = {}
        self.is_leader = False
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.host, self.port))

    #Method to broadcast a message to all servers (excluding itself)
    def broadcast_to_servers(self, message):
        for server_address in self.active_servers:
            if server_address != (self.host, self.port):
                try:
                    self.socket.sendto(message.encode(), server_address)
                except Exception as e:
                    print(f"Error sending to {server_address}: {e}")

    #Method to broadcast a message to all clients (excluding a specific client)
    def broadcast_to_clients(self, message, exclude=None):
        for client_address in self.clients:
            if exclude is None or client_address != exclude:
                self.socket.sendto(message.encode(), client_address)

    #Method to send heartbeat messages to other servers
    def send_heartbeat(self):
        while True:
            heartbeat_message = f"heartbeat:{self.host}:{self.port}:{self.uuid}"
            print(f"Sending heartbeat: {heartbeat_message}")
            self.broadcast_to_servers(heartbeat_message)
            time.sleep(3)  

    #Method to continuously listen for incoming messages
    def listen(self):
        while True:
            try:
                message, address = self.socket.recvfrom(1024)
                message = message.decode()
                msg_type, *args = message.split(":")

                #Handle different message types
                if msg_type == "heartbeat":
                    self.handle_heartbeat(*args, address)
                elif msg_type == "new_leader":
                    self.handle_new_leader(uuid.UUID(args[0]))
                elif msg_type == "msg":
                    self.handle_client_message(address, ":".join(args))
                elif msg_type == "join":
                    self.clients[address] = args[0]
                    self.broadcast_to_clients(f"{args[0]} joined the chat.", exclude=address)
                elif msg_type == "test":
                    self.socket.sendto("ack".encode(), address)
            except Exception as e:
                print(f"Error receiving message: {e}")

    #Method to handle heartbeat messages from other servers
    def handle_heartbeat(self, host, port, server_uuid, address):
        server_uuid = uuid.UUID(server_uuid)
        self.active_servers[address] = (host, int(port), server_uuid)
        print(f"Heartbeat received from server {server_uuid} at {address}")  
        self.check_leader()

    #Method to analyze traffic (sample implementation)
    def analyze_traffic(self):
        traffic_data = random.sample(range(100), 10)
        average_traffic = sum(traffic_data) / len(traffic_data)
        print(f"Average traffic: {average_traffic} requests per second")

    #Method to handle a message indicating a new leader
    def handle_new_leader(self, server_uuid):
        if server_uuid == self.uuid:
            self.is_leader = True
            print("I am the new leader.")

    #Method to handle a message from a client and broadcast it to all clients
    def handle_client_message(self, client_address, message):
        client_id = self.clients.get(client_address, "Unknown")
        formatted_message = f"{client_id}: {message}"
        print(formatted_message)
        self.broadcast_to_clients(formatted_message, exclude=client_address)

    #Method to update the heartbeat timestamp for a given server
    def update_server_heartbeat(self, server_socket):
        with self.lock:
            self.server_heartbeats[server_socket] = time.time()

    #Method to check and remove servers with expired heartbeats
    def check_heartbeats(self):
        current_time = time.time()
        with self.lock:
            to_remove_servers = [server_socket for server_socket, timestamp in self.server_heartbeats.items()
                                 if current_time - timestamp > 5]
            for server_socket in to_remove_servers:
                self.remove_server(server_socket)

    #Method to check if the current server should become the leader
    def check_leader(self):
        if not self.active_servers or self.uuid == max(self.active_servers.values(), key=lambda x: x[2])[2]:
            self.become_leader()

    #Method to make the current server the leader
    def become_leader(self):
        if not self.is_leader:  
            self.is_leader = True   
            self.leader = self.uuid 
            print("I am the leader.")
            self.broadcast_to_servers(f"new_leader::{self.uuid}")

    #Method to check if the leader's heartbeat is missing
    def is_leader_heartbeat_missing(self):
        current_time = time.time()
        with self.lock:
            for _, timestamp in self.server_heartbeats.items():
                if current_time - timestamp <= 5:
                    return False
            return True

    #Method to start the heartbeat checking loop
    def start_heartbeat_checking(self):
        while True:
            self.check_heartbeats()
            time.sleep(5)

    #Method to run the server
    def run(self):
        print(f"Server running on {self.host}:{self.port} with UUID {self.uuid}")
        if self.port == 5000:
            self.become_leader()
        threading.Thread(target=self.listen, daemon=True).start()
        threading.Thread(target=self.send_heartbeat, daemon=True).start()

#Main function to get user input for the port and run the Server
def main():
    port = int(input("Enter port number for this server: "))
    server = Server(port)
    server.run()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Server shutting down.")

#Run the main function if the script is executed directly
if __name__ == "__main__":
    main()
