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


class HogPolicy:
    """Detects a host that takes most of a busy link while others are active.

    update() is fed the per-client download rate (Mbit/s, switch -> host) once
    per poll and returns the keys that should be rate-limited now.
    """

    def __init__(self, link_mbps=10.0, busy_frac=0.5, share_frac=0.7,
                 other_min=0.3, consecutive=2, limit_seconds=20, limit_frac=0.5):
        self.link_mbps = link_mbps
        self.busy_frac = busy_frac        # link counts as busy above this fraction
        self.share_frac = share_frac      # hog = more than this share of total
        self.other_min = other_min        # another host must be actually active
        self.consecutive = consecutive    # polls in a row before acting
        self.limit_seconds = limit_seconds
        self.limit_frac = limit_frac      # cap = this fraction of the link
        self.strikes = defaultdict(int)
        self.limited = {}                 # key -> limit expiry time

    @property
    def limit_kbps(self):
        return int(self.limit_frac * self.link_mbps * 1000)

    def update(self, rates, now=None):
        now = time.time() if now is None else now
        total = sum(rates.values())
        out = []
        for key, r in rates.items():
            if self.limited.get(key, 0) > now:
                self.strikes[key] = 0
                continue
            others_active = any(v >= self.other_min for k, v in rates.items() if k != key)
            is_hog = (total >= self.busy_frac * self.link_mbps
                      and r >= self.share_frac * total and others_active)
            self.strikes[key] = self.strikes[key] + 1 if is_hog else 0
            if self.strikes[key] >= self.consecutive:
                self.strikes[key] = 0
                self.limited[key] = now + self.limit_seconds
                out.append(key)
        return out
