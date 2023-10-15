# Copyright © Gedalya Gordon 2023, all rights reserved. #

from __future__ import annotations

import time
import socket
import threading
from collections.abc import Callable

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

        self.connected = False

        print("Connecting to server " + serverip + "from local client...")

        self.thread = threading.Thread(target=self.Connect, args=[serverip])
        self.thread.start()
    
    def Connect(self, serverip):
        try:
            self.sock.connect((serverip, PORT))
            self.connected = True
            print("Connected local client to server " + serverip + ".")
        except socket.error as e:
            print("Connection error:", e)
        
        while True:
            self.Receive(self.sock.recv(512))
    
    def Send(self, data):
        #CHANGE DATA TO STRING-FORMAT ############# FIX!!! ######### FIX!!!!!
        sendable = str(data)

        # Encode the data to a network-sendable form and send it to the server.
        self.sock.send(sendable.encode())
    
    def Receive(self, data):
        d = data.decode('utf-8')
        if __name__ == '__main__':
            print("Server says:", data.decode('utf-8'))
        else:
            for event in _receive_events:
                event(d)
        if d == "Quit successful":
            exit()

# client and server variable declarations (This comment is functionally a flag for searching the file)
client: LANClient
serverIfHost: LANServer

# The events to fire when a message is received
_receive_events: list[Callable[[str], None]] = []

# clientsTotal shoud INCLUDE the host device's "dirty" client.
# After calling init_server, remember to also call init_client with the local ip to create the dirty client.
def init_server(clientsTotal) -> str:
    global serverIfHost
    serverIfHost = LANServer(clientsTotal)
    return get_ip()

def init_client(serverip):
    global client
    client = LANClient(serverip)

def send(data):
    assert client, "Network error: local client not valid.\n\tMake sure to call 'init_client()' before attempting to send any messages."
    client.Send(data)

def add_receive_target(event: (Callable[[str], None])):
    global _receive_events
    _receive_events.append(event)

def quit():
    assert client, "Network error: local client not valid.\n\tMake sure to call 'init_client()' before attempting to send any messages."
    send("mquit")
    time.sleep(0.05)
    client.sock.close()
    exit()


if __name__ == '__main__':
    shouldserve = input("Are you (1) hosting the server or (2) connecting to it?\n")
    match int(shouldserve.strip('()')):
        case 1:
            desiredclients = int(input("How many clients would you like to host? (Include your own computer in your total.)\n"))
            init_server(desiredclients)
            init_client(get_ip())
        case 2:
            targetip = input("Please enter the IPv4 address of the host you would like to connect to:\n")
            init_client(targetip)

    time.sleep(0.1)
    while True:
        d = input("Input data to send:\n")
        send(d)
        time.sleep(0.1)
    