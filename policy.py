"""Pure-Python blocking policy (no OpenFlow here, so it can be unit-tested)."""
import json
import time
from collections import defaultdict, deque


class BlockPolicy:
    def __init__(self, threshold=3, window=60, block_seconds=30):
        self.threshold = threshold
        self.window = window
        self.block_seconds = block_seconds
        self.fails = defaultdict(deque)   # ip -> timestamps of AUTH_FAIL
        self.blocked = {}                 # ip -> unblock time

    def handle(self, line, now=None):
        """Feed one events.jsonl line. Returns an ip to block, or None."""
        now = time.time() if now is None else now
        try:
            ev = json.loads(line)
        except ValueError:
            return None
        if ev.get("event") != "AUTH_FAIL":
            return None
        ip = ev.get("ip")
        if not ip or ip.startswith("127."):
            return None
        if self.blocked.get(ip, 0) > now:
            return None
        q = self.fails[ip]
        q.append(ev.get("ts", now))
        while q and q[0] < ev.get("ts", now) - self.window:
            q.popleft()
        if len(q) >= self.threshold:
            q.clear()
            self.blocked[ip] = now + self.block_seconds
            return ip
        return None
