"""Client library for the file-sharing protocol (see server.py)."""
import hashlib
import os
import socket


class FSError(Exception):
    pass


class FSClient:
    def __init__(self, host, port=5000, timeout=30):
        self.sock = socket.create_connection((host, port), timeout=timeout)
        self.buf = b""

    # -- low level
    def _readline(self):
        while b"\n" not in self.buf:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise FSError("server closed the connection")
            self.buf += chunk
        line, self.buf = self.buf.split(b"\n", 1)
        return line.decode("utf-8", "replace").strip()

    def _read_exact(self, n):
        while n > 0:
            if self.buf:
                chunk, self.buf = self.buf[:n], self.buf[n:]
            else:
                chunk = self.sock.recv(min(65536, n))
                if not chunk:
                    raise FSError("connection lost mid-transfer")
            n -= len(chunk)
            yield chunk

    def _send(self, text):
        self.sock.sendall(text.encode() + b"\n")

    # -- operations
    def login(self, user, password):
        self._send(f"AUTH {user} {password}")
        reply = self._readline()
        if reply != "OK":
            raise FSError(reply)

    def list(self):
        self._send("LIST")
        reply = self._readline()
        if not reply.startswith("OK "):
            raise FSError(reply)
        return b"".join(self._read_exact(int(reply[3:]))).decode()

    def upload(self, path):
        name = os.path.basename(path)
        if not os.path.isfile(path):
            raise FSError(f"local file not found: {path}")
        size = os.path.getsize(path)
        self._send(f"UPLOAD {name} {size}")
        reply = self._readline()
        if reply != "READY":
            raise FSError(reply)
        with open(path, "rb") as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                self.sock.sendall(chunk)
        reply = self._readline()
        if reply != "OK":
            raise FSError(reply)
        return size

    def download(self, name, dest_dir="downloads"):
        os.makedirs(dest_dir, exist_ok=True)
        self._send(f"DOWNLOAD {name}")
        reply = self._readline()
        if not reply.startswith("OK "):
            raise FSError(reply)
        size = int(reply[3:])
        dest = os.path.join(dest_dir, os.path.basename(name))
        h = hashlib.sha256()
        try:
            with open(dest, "wb") as f:
                for chunk in self._read_exact(size):
                    f.write(chunk)
                    h.update(chunk)
        except Exception:
            if os.path.exists(dest):
                os.remove(dest)
            raise
        return dest, size, h.hexdigest()

    def quit(self):
        try:
            self._send("QUIT")
            self._readline()
        except (OSError, FSError):
            pass
        self.sock.close()
