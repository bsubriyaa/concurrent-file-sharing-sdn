# Concurrent File Sharing System with SDN

A multi-user file-sharing service built on raw **TCP sockets** (Python `socket` + `threading`),
run inside **Mininet** with an **Open vSwitch** switch controlled by an **OS-Ken** (OpenFlow 1.3)
controller. The application reports security events to the controller, which reacts by installing
and removing flow rules.

## Architecture

```text
                  +------------------------+
                  |  OS-Ken controller c0  |   reads events.jsonl, installs flows,
                  |  (127.0.0.1:6653)      |   logs bandwidth to stats.csv
                  +-----------+------------+
                              | OpenFlow 1.3
                        +-----+-----+
                        |    s1     |   Open vSwitch
                        +-+--+--+-+-+
        port 1 |  port 2 | port 3|  | port 4 (capped, default 10 Mbit/s)
              h1        h2      h3  server 10.0.0.4 : TCP 5000
          10.0.0.1  10.0.0.2  10.0.0.3
```

All four hosts connect only to `s1` (star topology).

**Socket -> SDN integration.** The file server appends one JSON line per application event
(`AUTH_OK`, `AUTH_FAIL`, `UPLOAD`, `DOWNLOAD`, ...) to `events.jsonl`. Mininet hosts share the
filesystem with the controller process, so the controller simply tails that file.
After **3 failed logins from one IP** it installs a priority-200 DROP flow for
`IP -> 10.0.0.4:5000` with a 30 s hard timeout; access is restored automatically when the flow
expires. The controller also polls port statistics every 2 s into `stats.csv` (per-port Mbit/s).

## Files

| File | Purpose |
|---|---|
| `server.py` | Threaded TCP file server: authentication, LIST, UPLOAD, DOWNLOAD, metadata, event log |
| `fsclient.py` | Client library implementing the protocol |
| `client.py` | Interactive command-line client |
| `controller.py` | OS-Ken controller: learning switch + dynamic blocking + bandwidth monitor |
| `policy.py` | Pure-Python blocking policy (3 failures / 60 s -> block) |
| `topology.py` | Mininet topology; `--mode sdn` or `--mode baseline`, link cap options |
| `bench.py`, `analyze.py` | Benchmark client and results summariser |
| `exp_sdn.mn`, `exp_baseline.mn` | Experiment scripts run from the Mininet CLI |
| `selftest.py` | Local loopback tests of the server (no Mininet needed) |
| `results.csv`, `results_summary.md` | Raw and summarised experiment results |

## Protocol

Every control message is one UTF-8 line ending in `\n`; file bytes follow an exact size.

```text
C: AUTH <user> <password>     S: OK | ERR <reason>       (3 failures close the connection)
C: LIST                       S: OK <nbytes>\n<nbytes of text>
C: UPLOAD <name> <size>       S: READY | ERR ...   then <size> raw bytes   S: OK | ERR ...
C: DOWNLOAD <name>            S: OK <size>\n<size raw bytes> | ERR file not found
C: QUIT                       S: BYE
```

Safety properties: file names are restricted to `[A-Za-z0-9._-]` (no paths, no `..`); uploads go
to a temporary `.part` file that is removed if the transfer is interrupted; `metadata.json`
writes are locked and atomic.

Demo accounts (hard-coded, passwords stored as salted PBKDF2 hashes in memory):
`admin/1234`, `alice/alice123`, `bob/bob123`. Traffic is not encrypted (no TLS).

## Requirements

Ubuntu 24.04 (WSL2 works), Python 3.12, Mininet 2.3.0, Open vSwitch, OS-Ken
(`sudo apt install mininet python3-os-ken`). If Mininet cannot start Open vSwitch after a
WSL restart: `sudo service openvswitch-switch start`.

## Quick check without Mininet

```bash
python3 selftest.py        # 13 checks: 5 MB hash, path traversal, interrupted upload, 8 parallel clients ...
```

## Running the SDN demo

Terminal A (controller):

```bash
cd file-sharing-sdn
osken-manager controller.py
# optional static ACL baseline: STATIC_H1_BLOCK=1 osken-manager controller.py
```

Terminal B (network):

```bash
cd file-sharing-sdn
sudo mn -c
sudo python3 topology.py            # sdn mode, server link 10 Mbit/s
```

At the `mininet>` prompt:

```text
pingall
server python3 server.py > server.log 2>&1 &
h2 python3 client.py --host 10.0.0.4 --user admin --password 1234
```

Dynamic block demo (h3 fails three logins, is blocked, then recovers after 30 s):

```text
h3 sh -c 'for i in 1 2 3; do python3 client.py --host 10.0.0.4 --user admin --password wrong; done'
h3 sh -c 'printf "LIST\nQUIT\n" | timeout 5 python3 client.py --host 10.0.0.4 --user admin --password 1234'   # no output: blocked
h2 sh -c 'printf "LIST\nQUIT\n" | python3 client.py --host 10.0.0.4 --user admin --password 1234'             # still works
sh ovs-ofctl -O OpenFlow13 dump-flows s1                                                                      # shows the priority-200 drop flow
sh cat controller_events.log                                                                                  # BLOCK ... response_ms=..., UNBLOCK ...
```

Note: the Mininet prompt replaces host names such as `h2` with their IPs inside commands.

## Reproducing the experiments

SDN run (controller running, `topology.py` in sdn mode, server started as above):

```text
source exp_sdn.mn
```

Baseline run: stop the controller, `sudo mn -c`, `sudo python3 topology.py --mode baseline`,
start the server, then `source exp_baseline.mn`. Finally `python3 analyze.py`.
Delete `results.csv` first to start fresh.

## Results (server link capped at 10 Mbit/s, 5 MB file)

| Scenario | Metric | Baseline (no SDN) | SDN |
|---|---|---|---|
| single client, 10 runs | throughput (Mbit/s) | 9.16 ± 1.19 | 9.64 ± 0.03 |
| 3 clients at once, 3 runs each | per-client throughput (Mbit/s) | 3.45 ± 1.04 | 3.68 ± 1.98 |
| 3 clients at once | Jain fairness index | 0.999 | 0.943 |
| brute-force login, 20 s | attempts that reached the server | 99 of 99 | 3 of 20 |
| h2 download during the attack | throughput (Mbit/s) | 9.58 ± 0.10 | 9.61 ± 0.06 |

* The controller blocked the attacker **89 ms** after the third failed login was logged, and
  restored access after about 32 s (30 s timeout plus switch expiry check).
* The SDN adds no measurable overhead to normal transfers. Throughput differences in the
  single-client and concurrent tests are within run-to-run noise; the SDN does not make
  transfers faster. Its benefit here is access control with fast automatic reaction.
* The brute-force attack uses little bandwidth, so it does not reduce h2's throughput in either
  mode; the block protects the server and its logs rather than the link.
* All downloads were verified with SHA-256.

## Known limitations

* The controller and server communicate through a shared file, which works because Mininet hosts
  share the host filesystem; a real deployment would use a network channel.
* The policy blocks per source IP and only for the file-sharing port.
* No TLS; demo accounts are hard-coded.
* Fairness is not enforced by the controller (no meters/queues yet).
