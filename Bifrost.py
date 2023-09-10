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
        print("Connected over LAN to client #" + str(len(self.connections) + 1))
        self.connections.append(csock)
    
    def Update(self):
        for i in range(len(self.connections)):
            c = self.connections[i]
            data = c.recv(512)
            strdata = data.decode("utf-8")
            if strdata != "": # Process the message
                match strdata[0]: # Prefixes
                    case 'r': # A request to perform an action--usually sending input/data to all clients (incl. the sender)
                        cmd = strdata.lstrip('r').split(' ')[0]
                        args = strdata.lstrip('r' + cmd + ' ')
                        match cmd:
                            case 'cast':
                                for conn in self.connections:
                                    conn.send(args.encode())

                            case _: c.send("Invalid request".encode())
                    case 'm': # A command to run locally
                        match strdata.lstrip('m'):
                            case 'quit':
                                self.connections.pop(i)
                                time.sleep(0.05)
                                c.send("Quit successful".encode())
                                c.close()
                            
                            case _: c.send("Invalid command".encode())
                    
                    case _: c.send("Unrecognized data".encode())

class LANClient:
    def __init__(self, serverip: str) -> None:
        print("Starting local client...")
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.incr: int = 0

        print("Connecting to server " + serverip + "from local client...")
        self.Connect(serverip)
        print("Connected local client to server " + serverip + ".")
    
    def Connect(self, serverip):
        self.sock.connect((serverip, PORT))

    def Update(self):
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
    receive(client.sock.recv(512))

def receive(data):
    print("Server says:", data.decode('utf-8'))

def quit():
    assert client, "Network error: local client not valid.\n\tMake sure to call 'init_client()' before attempting to send any messages."
    send("mquit")
    time.sleep(0.05)
    client.sock.close()


if __name__ == '__main__':
    init_server(1)
    init_client(get_ip())

    time.sleep(0.1)
    while True:
        d = input("Input data to send:\n")
        send(d)
        time.sleep(0.1)
    