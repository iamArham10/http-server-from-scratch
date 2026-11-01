import socket

HOST = "127.0.0.1"
PORT = 6666

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    print(f"listening on {HOST}:{PORT}")
    conn, addr = s.accept()
    with conn:
        print(f"Connected to {addr}")
        while True:
            data = conn.recv(1024)
            print(f"Received {data}")
            if not data:
                break
            conn.sendall(str.encode(f"Received: {data}"))
