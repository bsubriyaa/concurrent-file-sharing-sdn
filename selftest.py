import hashlib, os, socket, subprocess, sys, tempfile, threading, time
from fsclient import FSClient, FSError

PORT = 5055
os.chdir(os.path.dirname(os.path.abspath(__file__)))
srv = subprocess.Popen([sys.executable, "server.py", "--host", "127.0.0.1", "--port", str(PORT)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
time.sleep(1)
tmp = tempfile.mkdtemp()
ok = True

def check(name, cond):
    global ok
    ok &= bool(cond)
    print(("PASS " if cond else "FAIL ") + name)

def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()

def login(user="admin", pw="1234"):
    c = FSClient("127.0.0.1", PORT); c.login(user, pw); return c

try:
    big = os.path.join(tmp, "big.bin")
    open(big, "wb").write(os.urandom(5 * 1024 * 1024))
    c = login()
    c.upload(big)
    d, size, h = c.download("big.bin", os.path.join(tmp, "dl"))
    check("5MB upload+download hash matches", h == sha(big) and size == 5 * 1024 * 1024)

    # file containing the old END marker
    tricky = os.path.join(tmp, "tricky.bin")
    open(tricky, "wb").write(b"abc\nEND\nxyz" * 1000)
    c.upload(tricky)
    check("binary containing 'END' survives", c.download("tricky.bin", os.path.join(tmp, "dl"))[2] == sha(tricky))

    # missing file then LIST must not be corrupted
    try: c.download("nope.txt", os.path.join(tmp, "dl")); r = False
    except FSError: r = True
    lst = c.list()
    check("missing file error, then LIST still clean", r and "big.bin" in lst and "ERR" not in lst)

    # path traversal
    for bad in ["../server.py", "/etc/passwd", "..", ".hidden", "a/b"]:
        try: c.download(bad, os.path.join(tmp, "dl")); r = False
        except FSError: r = True
        check(f"download rejects {bad!r}", r)
    s = socket.create_connection(("127.0.0.1", PORT)); s.sendall(b"AUTH admin 1234\nUPLOAD ../evil.txt 3\n")
    time.sleep(.3); data = s.recv(4096); s.close()
    check("upload rejects ../evil.txt", b"invalid file name" in data and not os.path.exists("../evil.txt"))

    # interrupted upload leaves nothing
    s = socket.create_connection(("127.0.0.1", PORT))
    s.sendall(b"AUTH admin 1234\nUPLOAD half.bin 1000000\n"); time.sleep(.3)
    s.sendall(b"x" * 1000); s.close(); time.sleep(.5)
    left = [f for f in os.listdir("shared_files") if f.startswith("half")]
    check("interrupted upload leaves no partial file", not left and "half.bin" not in c.list())

    # wrong login x3 closes connection
    s = socket.create_connection(("127.0.0.1", PORT))
    for _ in range(3): s.sendall(b"AUTH admin wrong\n"); time.sleep(.1)
    time.sleep(.3); s.recv(4096)
    check("3 bad logins -> server closes", s.recv(10) == b"")

    # parallel clients
    results = []
    def work(i):
        cc = login(); p = os.path.join(tmp, f"dl{i}")
        results.append(cc.download("big.bin", p)[2] == sha(big)); cc.quit()
    t0 = time.time(); ts = [threading.Thread(target=work, args=(i,)) for i in range(8)]
    [t.start() for t in ts]; [t.join() for t in ts]
    check(f"8 parallel downloads all correct ({time.time()-t0:.2f}s)", len(results) == 8 and all(results))

    # parallel uploads, metadata integrity
    def up(i):
        cc = login("alice", "alice123"); p = os.path.join(tmp, f"u{i}.bin")
        open(p, "wb").write(os.urandom(200000)); cc.upload(p); cc.quit()
    ts = [threading.Thread(target=up, args=(i,)) for i in range(10)]
    [t.start() for t in ts]; [t.join() for t in ts]
    import json; meta = json.load(open("metadata.json"))
    check("10 parallel uploads all in metadata.json", all(f"u{i}.bin" in meta for i in range(10)))
    c.quit()
finally:
    srv.terminate()
    print("\nALL PASSED" if ok else "\nSOME FAILED")
