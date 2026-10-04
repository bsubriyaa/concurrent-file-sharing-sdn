"""Interactive client.  Usage: python3 client.py --host 10.0.0.4 --user admin"""
import argparse
import getpass

from fsclient import FSClient, FSError


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="10.0.0.4")
    ap.add_argument("--port", type=int, default=5000)
    ap.add_argument("--user", default="admin")
    ap.add_argument("--password", default=None)
    args = ap.parse_args()

    password = args.password if args.password is not None else getpass.getpass("Password: ")
    try:
        c = FSClient(args.host, args.port)
        c.login(args.user, password)
    except (OSError, FSError) as e:
        print("Could not connect/login:", e)
        return
    print("Authentication successful. Commands: LIST, UPLOAD <path>, DOWNLOAD <name>, QUIT")

    while True:
        try:
            line = input("Enter command: ").strip()
        except EOFError:
            line = "QUIT"
        cmd, _, arg = line.partition(" ")
        cmd = cmd.upper()
        try:
            if cmd == "LIST":
                print(c.list())
            elif cmd == "UPLOAD" and arg:
                print("Uploaded", c.upload(arg), "bytes")
            elif cmd == "DOWNLOAD" and arg:
                dest, size, digest = c.download(arg)
                print(f"Downloaded {size} bytes to {dest}\nsha256 {digest}")
            elif cmd == "QUIT":
                c.quit()
                break
            else:
                print("Unknown command")
        except (FSError, OSError) as e:
            print("Error:", e)
            if isinstance(e, OSError) or "closed" in str(e) or "lost" in str(e):
                break


if __name__ == "__main__":
    main()
