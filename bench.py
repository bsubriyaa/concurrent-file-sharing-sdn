"""Benchmark client.  Appends rows to results.csv (long format).

  python3 bench.py single --mode sdn --scenario single --client h2 --runs 10
  python3 bench.py attack --mode sdn --client h3 --seconds 20
"""
import argparse
import csv
import hashlib
import os
import socket
import time

from fsclient import FSClient, FSError

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(BASE_DIR, "results.csv")


def write_rows(rows):
    new = not os.path.exists(RESULTS)
    with open(RESULTS, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["mode", "scenario", "client", "run", "metric", "value"])
        w.writerows(rows)


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def single(a):
    expected = None
    src = os.path.join(BASE_DIR, "shared_files", a.file)
    if os.path.exists(src):
        expected = sha256_of(src)
    dest_dir = "/tmp/bench_" + a.client
    for run in range(1, a.runs + 1):
        c = FSClient(a.host, a.port, timeout=60)
        c.login(a.user, a.password)
        t0 = time.time()
        _, size, digest = c.download(a.file, dest_dir)
        dt = time.time() - t0
        c.quit()
        rows = [
            (a.mode, a.scenario, a.client, run, "seconds", round(dt, 4)),
            (a.mode, a.scenario, a.client, run, "mbps", round(size * 8 / dt / 1e6, 3)),
            (a.mode, a.scenario, a.client, run, "hash_ok", int(expected is None or digest == expected)),
        ]
        write_rows(rows)
        print(f"{a.client} run {run}: {dt:.2f}s  {size*8/dt/1e6:.2f} Mbit/s  hash_ok={rows[2][-1]}")


def attack(a):
    """Brute-force login attempts at ~20/s; count how many reach the server."""
    end = time.time() + a.seconds
    total = answered = 0
    while time.time() < end:
        total += 1
        try:
            s = socket.create_connection((a.host, a.port), timeout=1)
            s.settimeout(1)
            s.sendall(b"AUTH admin wrong\n")
            if s.recv(100):
                answered += 1
            s.close()
        except OSError:
            pass
        time.sleep(0.05)
    write_rows([
        (a.mode, "attack", a.client, 1, "attempts", total),
        (a.mode, "attack", a.client, 1, "answered_by_server", answered),
    ])
    print(f"{a.client}: {total} attempts, {answered} reached the server")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("kind", choices=["single", "attack"])
    ap.add_argument("--mode", required=True,
                    help="label for this run: baseline, sdn, sdn_nolimit, sdn_limit ...")
    ap.add_argument("--scenario", default="single")
    ap.add_argument("--client", default="h2")
    ap.add_argument("--host", default="10.0.0.4")
    ap.add_argument("--port", type=int, default=5000)
    ap.add_argument("--user", default="admin")
    ap.add_argument("--password", default="1234")
    ap.add_argument("--file", default="big5.bin")
    ap.add_argument("--runs", type=int, default=10)
    ap.add_argument("--seconds", type=int, default=20)
    a = ap.parse_args()
    {"single": single, "attack": attack}[a.kind](a)
