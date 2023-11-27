# !/usr/bin/env python3
# -*- coding: UTF-8 -*-

import socket
import sys
import os


def handleRequest(tcpSocket):
    # 1. Receive request message from the client on connection socket
    request = tcpSocket.recv(1024).decode('utf-8')
    print("Received request:")
    print(request)

    # 2. Extract the path of the requested object from the message (second part of the HTTP header)
    lines = request.split('\n')
    filename = lines[0].split()[1]

    # Handling root file
    if filename == '/':
        filename = '/index.html'

    # 3 & 4. Read the corresponding file from disk and store in temporary buffer
    try:
        fin = open('htdocs' + filename)
        content = fin.read()
        fin.close()

        # 5. Send the correct HTTP response error or success
        response = 'HTTP/1.1 200 OK\n\n' + content

    except FileNotFoundError:
        response = 'HTTP/1.1 404 Not Found\n\nFile not found'

    # 6. Send the content of the file to the socket
    tcpSocket.sendall(response.encode())

    # 7. Close the connection socket
    tcpSocket.close()


def startServer(serverPort):
    # Create a TCP socket
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Bind the socket to server address and server port
    serverSocket.bind(('', serverPort))

    # Listen to at most 1 connection at a time
    serverSocket.listen(1)

    print("Web server running on port:", serverPort)

    # Server should be up and running and listening to the incoming connections
    while True:
        conn, addr = serverSocket.accept()
        print("Got a connection from:", addr)

        # Handle the request
        handleRequest(conn)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 WebServer.py [port_number]")
        sys.exit()

    startServer(1314)
