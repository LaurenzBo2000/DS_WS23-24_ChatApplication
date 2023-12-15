import socket
import threading

class ChatClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        self.client_socket.connect((self.host, self.port))
        receive_thread = threading.Thread(target=self.receive)
        receive_thread.start()

    def receive(self):
        while True:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                print(message)
            except:
                break

    def send(self, message):
        self.client_socket.send(message.encode('utf-8'))

if __name__ == "__main__":
    client = ChatClient('localhost', 12345)
    client.connect()

    while True:
        message = input()
        client.send(message)