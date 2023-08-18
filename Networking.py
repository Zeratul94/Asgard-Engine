from __future__ import annotations

import gc
import socket

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        # doesn't even have to be reachable
        s.connect(('10.254.254.254', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

class LANClient:
    def __init__(self, serverIP: str) -> None:
        self.sock: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(0)

        self.IP: str = get_ip()
        self.serverIP: str = serverIP

        if self.IP == self.serverIP:
            self.isServer: bool = True
            self.sock.bind((self.serverIP, 10000))
            self.sock.listen(1)
            self.clients = {}
        else:
            self.isServer: bool = False
            self.clients: dict[LANClient] = None
    
    def update(self, dTime: float):
        if self.isServer:
            connection, client_address = self.sock.accept()
            try:
                data = connection.recv(999)
                print(data)
            except:
                connection.close()
        else:
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.connect((self.serverIP, 10000))
                if False: # quit
                    self.destroy
                message="Hi, I'm Norm!"
                self.sock.sendall(message)
            except:
                self.destroy()
    
    def destroy(self):
        if self.isServer:
            for client in self.clients:
                client.destroy()
        self.sock.close()
