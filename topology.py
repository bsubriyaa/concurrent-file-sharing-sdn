from mininet.net import Mininet
from mininet.node import OVSSwitch, RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel

def create_topology():
    net = Mininet(
        controller=RemoteController,
        switch=OVSSwitch
    )

    h1 = net.addHost('h1')
    h2 = net.addHost('h2')
    h3 = net.addHost('h3')
    server = net.addHost('server')

    s1 = net.addSwitch('s1')

    c0 = net.addController(
        'c0',
        controller=RemoteController,
        ip='127.0.0.1',
        port=6653
    )

    net.addLink(h1, s1)
    net.addLink(h2, s1)
    net.addLink(h3, s1)
    net.addLink(server, s1)

    net.start()

    print("\nFile Sharing SDN Topology Started")
    print("h1, h2, h3 = clients")
    print("server = file server")
    print("s1 = Open vSwitch")
    print("c0 = SDN Controller\n")

    CLI(net)

    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    create_topology()