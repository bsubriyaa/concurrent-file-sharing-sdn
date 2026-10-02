import socket
import time

HOST = "10.0.0.4"
PORT = 5000

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

client.recv(1024)
client.sendall(b"admin")

client.recv(1024)
client.sendall(b"1234")

response = client.recv(1024).decode()

if response == "AUTH_SUCCESS":
    print("Authentication successful")

    client.sendall(b"DOWNLOAD test.txt")

    response = client.recv(2)

    if response == b"OK":
        client.sendall(b"READY")

        size_data = client.recv(1024).decode().strip()
        filesize = int(size_data)

        received = 0

        while received < filesize:
            data = client.recv(min(4096, filesize - received))

            if not data:
                break

            received += len(data)

        if received == filesize:
            print("Download successful:", filesize, "bytes")
        else:
            print("Download failed")

        print("Connection kept open for 5 seconds...")
        time.sleep(5)

else:
    print("Authentication failed")

client.close()
print("Client finished")