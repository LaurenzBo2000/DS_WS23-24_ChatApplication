import socket
import threading

class LeaderElection:
    def __init__(self, host, port, server_host, server_port):
        self.host = host
        self.port = port
        self.server_host = server_host
        self.server_port = server_port
        self.current_node = 0
        self.leader = None
        self.in_election = False
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self):
        self.server_socket.connect((self.server_host, self.server_port))
        server_listener_thread = threading.Thread(target=self.listen_to_server)
        server_listener_thread.start()

    def listen_to_server(self):
        while True:
            try:
                message = self.server_socket.recv(1024).decode('utf-8')
                if message.startswith("LEADER"):
                    leader_id = int(message.split()[1])
                    self.leader = leader_id
                    self.in_election = False
                    print(f"Node {self.current_node} elected Node {self.leader} as leader.")
                elif message == "OK":
                    self.in_election = False
                    print(f"Node {self.current_node} received OK. Leader is Node {self.leader}.")
            except:
                break

    def start_election(self, initiator_socket):
        if not self.in_election:
            self.in_election = True
            initiator_socket.send("ELECTION".encode('utf-8'))

if __name__ == "__main__":
    total_nodes = 5
    node_id = int(input("Enter the ID of this node (0 to {}): ".format(total_nodes - 1)))
    server_host = 'localhost'
    server_port = 12345

    if 0 <= node_id < total_nodes:
        host = 'localhost'
        port = 5000 + node_id

        leader_election = LeaderElection(host, port, server_host, server_port)
        leader_election.start()

        while True:
            pass
    else:
        print("Invalid node ID.")