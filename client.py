import socket

HOST = "127.0.0.1"
PORT = 6666
MESSAGE = b"hello, world"

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.sendall(MESSAGE)
    received_message = s.recv(len(MESSAGE) + 100)

    print(received_message.decode())
