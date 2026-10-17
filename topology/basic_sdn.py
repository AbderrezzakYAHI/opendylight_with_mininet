#!/usr/bin/env python3
"""Basic Mininet topology controlled by a remote OpenDaylight instance."""

from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import info, setLogLevel
from mininet.net import Mininet
from mininet.node import OVSSwitch, RemoteController


def main() -> None:
    net = Mininet(controller=None, switch=OVSSwitch, link=TCLink)
    net.addController(
        "odl",
        controller=RemoteController,
        ip="127.0.0.1",
        port=6653,
    )

    h1 = net.addHost("h1", ip="10.0.0.1/24")
    h2 = net.addHost("h2", ip="10.0.0.2/24")
    s1 = net.addSwitch("s1", protocols="OpenFlow13")
    s2 = net.addSwitch("s2", protocols="OpenFlow13")

    net.addLink(h1, s1)
    net.addLink(s1, s2)
    net.addLink(s2, h2)

    info("*** Starting OpenDaylight-controlled topology\n")
    net.start()
    CLI(net)
    net.stop()


if __name__ == "__main__":
    setLogLevel("info")
    main()
