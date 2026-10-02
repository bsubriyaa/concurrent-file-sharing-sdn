import socket
import os

HOST = "10.0.0.4"
PORT = 5000
DOWNLOAD_FOLDER = "downloads"

USERNAME = "admin"
PASSWORD = "1234"

os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

print(client.recv(1024).decode())
client.sendall(USERNAME.encode())

print(client.recv(1024).decode())
client.sendall(PASSWORD.encode())

response = client.recv(1024).decode()

if response == "AUTH_SUCCESS":
    print("Authentication successful")
else:
    print("Authentication failed")
    client.close()
    exit()

while True:
    command = input("Enter command: ")

    client.sendall(command.encode())

    if command == "QUIT":
        break

    if command.startswith("UPLOAD "):
        filename = command[7:].strip()

        if not os.path.isfile(filename):
            print("File not found")
            continue

        filesize = os.path.getsize(filename)

        client.sendall(str(filesize).encode())

        response = client.recv(5)

        if response == b"READY":
            with open(filename, "rb") as f:
                while True:
                    chunk = f.read(4096)

                    if not chunk:
                        break

                    client.sendall(chunk)

            response = client.recv(1024)
            print(response.decode())

    elif command.startswith("DOWNLOAD "):
        filename = command[9:].strip()

        response = client.recv(2)

        if response == b"OK":
            client.sendall(b"READY")

            size_data = client.recv(1024).decode().strip()
            filesize = int(size_data)

            filepath = os.path.join(DOWNLOAD_FOLDER, filename)

            received = 0

            with open(filepath, "wb") as f:
                while received < filesize:
                    data = client.recv(min(4096, filesize - received))

                    if not data:
                        break

                    f.write(data)
                    received += len(data)

            if received == filesize:
                print("File downloaded successfully")
            else:
                print("Download failed")

        else:
            print(response.decode())

    else:
        response = client.recv(4096)
        print(response.decode())

client.close()