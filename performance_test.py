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

    client.sendall(b"DOWNLOAD performance_test.bin")

    response = client.recv(2)

    if response == b"OK":
        client.sendall(b"READY")

        size_data = client.recv(1024).decode().strip()
        filesize = int(size_data)

        received = 0

        start_time = time.time()

        while received < filesize:
            data = client.recv(min(4096, filesize - received))

            if not data:
                break

            received += len(data)

        end_time = time.time()

        if received == filesize:
            elapsed = end_time - start_time
            throughput = (filesize * 8) / elapsed / 1000

            print("File size:", filesize, "bytes")
            print("Transfer time:", round(elapsed, 6), "seconds")
            print("Throughput:", round(throughput, 2), "Kbps")
        else:
            print("Download failed")

else:
    print("Authentication failed")

client.close()