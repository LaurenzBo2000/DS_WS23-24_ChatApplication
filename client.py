#import necessary libraries
import socket
import threading
import time
import config

#Set the server IP address from the configuration
serverIP = config.SERVER

#Define the Client class
class Client:

    #Initialize the Client object with a client ID
    def __init__(self, client_id):
        self.client_id = client_id
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.connected_server_port = self.find_active_server()

    #Method to find an active server by sending a test message to different ports
    def find_active_server(self):
        while config.base_port <= config.max_port:
            try:

                #Send a test message to the server
                self.socket.sendto('test'.encode(), (serverIP, config.base_port))
                self.socket.settimeout(2)
                response, _ = self.socket.recvfrom(1024)

                #Check for a positive acknowledgment from the server
                if response.decode() == "ack":
                    print(f"Connected to server on port {config.base_port}")
                    return config.base_port
            except socket.error:
                print(f"No server on port {config.base_port}")

             #Move on to the next port
            config.base_port += 1
        print("No active servers found. Exiting.")
        exit()
        
    #Method to update the heartbeat timestamp for a given server
    def update_server_heartbeat(self, server_socket):
        with self.lock:
            self.server_heartbeats[server_socket] = time.time()

    #Method to check and remove servers with expired heartbeats
    def check_heartbeats(self):
        current_time = time.time()
        with self.lock:
            to_remove_servers = [server_socket for server_socket, timestamp in self.server_heartbeats.items()
                                 if current_time - timestamp > 2]
            for server_socket in to_remove_servers:
                self.remove_server(server_socket)

    #Method to remove a server from the list of active servers
    def remove_server(self, server_socket):
        with self.lock:
            if server_socket in self.server_heartbeats:
                del self.server_heartbeats[server_socket]

    #Method to send a message to the connected server
    def send_message(self, message):
        full_message = f"msg:{message}"
        self.socket.sendto(full_message.encode(), (serverIP, self.connected_server_port))

    #Method to continuously listen for incoming messages
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

    #Method to join the chat by sending a join message to the server
    def join_chat(self):
        join_message = f"join:{self.client_id}"
        self.socket.sendto(join_message.encode(), (serverIP, self.connected_server_port))

    #Method to run the client, including joining the chat and starting the message listening thread
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

#Main function to get user input for the client ID and run the Client
def main():
    client_id = input("Enter your client ID: ")
    client = Client(client_id)
    client.run()

#Run the main function if the script is executed directly
if __name__ == "__main__":
    main()
