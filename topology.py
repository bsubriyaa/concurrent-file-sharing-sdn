"""Mininet topology.  Usage:
    sudo python3 topology.py                  # SDN mode (needs osken-manager running)
    sudo python3 topology.py --mode baseline  # plain learning switch, no controller
    options: --bw 10 (server-link Mbit/s, 0 = unlimited)  --delay 1ms
Hosts: h1=10.0.0.1  h2=10.0.0.2  h3=10.0.0.3  server=10.0.0.4
Switch ports: h1=1 h2=2 h3=3 server=4
"""
import argparse

from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.node import OVSSwitch, RemoteController


def build(mode, bw, delay):
    sdn = mode == "sdn"
    net = Mininet(controller=None, switch=OVSSwitch, link=TCLink, autoSetMacs=False)
    if sdn:
        net.addController("c0", controller=RemoteController, ip="127.0.0.1", port=6653)
        s1 = net.addSwitch("s1", protocols="OpenFlow13")
    else:
        s1 = net.addSwitch("s1", failMode="standalone")   # ordinary L2 switch

    h1 = net.addHost("h1", ip="10.0.0.1/24", mac="00:00:00:00:00:01")
    h2 = net.addHost("h2", ip="10.0.0.2/24", mac="00:00:00:00:00:02")
    h3 = net.addHost("h3", ip="10.0.0.3/24", mac="00:00:00:00:00:03")
    server = net.addHost("server", ip="10.0.0.4/24", mac="00:00:00:00:00:04")

    for h in (h1, h2, h3):
        net.addLink(h, s1)
    opts = {}
    if bw > 0:
        opts["bw"] = bw
    if delay:
        opts["delay"] = delay
    net.addLink(server, s1, **opts)
    return net


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["sdn", "baseline"], default="sdn")
    ap.add_argument("--bw", type=float, default=10, help="server link Mbit/s (0 = unlimited)")
    ap.add_argument("--delay", default="", help="server link delay, e.g. 1ms")
    a = ap.parse_args()
    setLogLevel("info")
    net = build(a.mode, a.bw, a.delay)
    net.start()
    print("\nMode: %s | server link: %s Mbit/s\n" % (a.mode, a.bw or "unlimited"))
    CLI(net)
    net.stop()
