from __future__ import annotations

import time
import socket
import threading

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

PORT: int = 1119

class LANServer:
    def __init__(self, clientcount) -> None:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            self.sock.bind((get_ip(), PORT))
        except socket.error as e:
            print("Server startup failed with error:\n\t" + str(e))
            exit()
        
        self.sock.listen(1)
        
        self.connections: list[socket.socket] = []

        self.thread = threading.Thread(target=self.Start, args=[clientcount])

        self.thread.start()
    
    def Start(self, clientcount):
        for i in range(clientcount):
            self.WaitThenConnect()

        while True:
            self.Update()
    
    def WaitThenConnect(self):
        r = self.sock.accept()
        self.addconnection(r[0])
    
    def addconnection(self, csock):
        print("Connected over LAN to client #" + len(self.connections))
        self.connections.append(csock)
    
    def Update(self):
        print("\n" + str(len(self.connections)) + " Clients...")
        for i in range(len(self.connections)):
            data = self.connections[i].recv(512)
            strdata = data.decode("utf-8")
            if strdata != "": print("Client " + str(i) + ": " + strdata)

class LANClient:
    def __init__(self, serverip) -> None:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.incr: int = 0

        self.Connect(serverip)
    
    def Connect(self, serverip):
        self.sock.connect((serverip, PORT))

    def Update(self):
        self.Send(self.incr)
        self.incr+=1
    
    def Send(self, data):
        #CHANGE DATA TO STRING-FORMAT ############# FIX!!! ######### FIX!!!!!
        sendable = str(data)

        # Encode the data to a network-sendable form and send it to the server.
        self.sock.send(sendable.encode())


client: LANClient
serverIfHost: LANServer

# clientsTotal shoud INCLUDE the host device's "dirty" client.
# After calling init_server, remember to also call init_client with the local ip to create the dirty client.
def init_server(clientsTotal):
    global serverIfHost
    serverIfHost = LANServer(clientsTotal)

def init_client(serverip):
    global client
    client = LANClient(serverip)

def send(data):
    assert client, "Network error: local client not valid.\n\tMake sure to call 'init_client()' before attempting to send any messages."
    client.Send(data)



if __name__ == '__main__':
    init_server(2)
    init_client(get_ip())

    while True:
        client.Update()
        time.sleep(0.1)