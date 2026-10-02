import socket
import threading
import os

HOST = "0.0.0.0"
PORT = 5000
SHARED_FOLDER = "shared_files"

os.makedirs(SHARED_FOLDER, exist_ok=True)


def handle_client(conn, addr):
    print("Client connected:", addr)

    try:
        conn.sendall(b"Welcome to the File Sharing Server\n")

        while True:
            data = conn.recv(1024).decode().strip()

            if not data:
                break

            if data == "LIST":
                files = os.listdir(SHARED_FOLDER)

                if files:
                    response = "\n".join(files)
                else:
                    response = "No files available"

                conn.sendall(response.encode())

            elif data.startswith("UPLOAD "):
                filename = data[7:].strip()

                size_data = conn.recv(1024).decode().strip()
                filesize = int(size_data)

                filepath = os.path.join(SHARED_FOLDER, filename)

                conn.sendall(b"READY")

                received = 0

                with open(filepath, "wb") as f:
                    while received < filesize:
                        chunk = conn.recv(min(4096, filesize - received))

                        if not chunk:
                            break

                        f.write(chunk)
                        received += len(chunk)

                if received == filesize:
                    conn.sendall(b"UPLOAD SUCCESS")
                else:
                    conn.sendall(b"UPLOAD FAILED")

            elif data.startswith("DOWNLOAD "):
                filename = data[9:].strip()
                filepath = os.path.join(SHARED_FOLDER, filename)

                if os.path.isfile(filepath):
                    filesize = os.path.getsize(filepath)

                    conn.sendall(b"OK")
                    conn.recv(1024)

                    conn.sendall(str(filesize).encode())

                    with open(filepath, "rb") as f:
                        while True:
                            chunk = f.read(4096)

                            if not chunk:
                                break

                            conn.sendall(chunk)

                else:
                    conn.sendall(b"ERROR: File not found")

            elif data == "QUIT":
                break

            else:
                conn.sendall(b"Invalid command")

    except Exception as e:
        print("Error:", e)

    finally:
        conn.close()
        print("Client disconnected:", addr)


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server.bind((HOST, PORT))
server.listen(5)

print("File Sharing Server started")
print("Listening on port", PORT)

while True:
    conn, addr = server.accept()

    thread = threading.Thread(
        target=handle_client,
        args=(conn, addr)
    )

    thread.start()