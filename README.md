# A simple HTTP Proxy

This simple proxy program is written in python with 2 modules: socket and threading.

The code runs on a proxy server. It first establishes a TCP socket and waits for clients. When a client is connected, a new thread will be created to handle the client.  The socket will receive message from the client, analyze the data to get the host information, and then transfer it to the destination server through a new TCP connection. Then it will wait for the response of the remote server, then transfer the response back to the client.
