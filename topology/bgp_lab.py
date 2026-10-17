#!/usr/bin/env python3
"""Simple eBGP lab using two isolated FRR Linux router namespaces."""

from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.node import Node

from frr_helpers import configure_daemon, stop_daemons


FRR_ROOT = "/tmp/odl-mininet-frr"


class LinuxRouter(Node):
    """Linux router namespace with IPv4 forwarding enabled."""

    def config(self, **params):
        super().config(**params)

        self.cmd("sysctl -w net.ipv4.ip_forward=1")
        self.cmd("sysctl -w net.ipv4.conf.all.rp_filter=0")
        self.cmd("sysctl -w net.ipv4.conf.default.rp_filter=0")

    def terminate(self):
        self.cmd("sysctl -w net.ipv4.ip_forward=0")
        super().terminate()


BGP_R1 = """\
hostname r1
password frr
router bgp 65001
 bgp router-id 1.1.1.1
 no bgp ebgp-requires-policy
 neighbor 10.255.0.2 remote-as 65002
 address-family ipv4 unicast
  network 172.16.1.0/24
  neighbor 10.255.0.2 activate
 exit-address-family
log stdout
"""


BGP_R2 = """\
hostname r2
password frr
router bgp 65002
 bgp router-id 2.2.2.2
 no bgp ebgp-requires-policy
 neighbor 10.255.0.1 remote-as 65001
 address-family ipv4 unicast
  network 172.16.2.0/24
  neighbor 10.255.0.1 activate
 exit-address-family
log stdout
"""


def main() -> None:
    net = Mininet(controller=None, link=TCLink)

    # Explicitly disable Mininet's automatic host IP assignment.
    r1 = net.addHost("r1", cls=LinuxRouter, ip=None)
    r2 = net.addHost("r2", cls=LinuxRouter, ip=None)

    h1 = net.addHost(
        "h1",
        ip="172.16.1.10/24",
        defaultRoute="via 172.16.1.1",
    )

    h2 = net.addHost(
        "h2",
        ip="172.16.2.10/24",
        defaultRoute="via 172.16.2.1",
    )

    # LAN: h1 <-> r1
    net.addLink(
        h1,
        r1,
        params1={"ip": "172.16.1.10/24"},
        params2={"ip": "172.16.1.1/24"},
    )

    # eBGP transit link: r1 <-> r2
    net.addLink(
        r1,
        r2,
        params1={"ip": "10.255.0.1/30"},
        params2={"ip": "10.255.0.2/30"},
    )

    # LAN: r2 <-> h2
    net.addLink(
        r2,
        h2,
        params1={"ip": "172.16.2.1/24"},
        params2={"ip": "172.16.2.10/24"},
    )

    try:
        net.start()

        # Explicitly remove any accidental addresses from router interfaces.
        r1.cmd("ip addr flush dev r1-eth0")
        r1.cmd("ip addr flush dev r1-eth1")
        r2.cmd("ip addr flush dev r2-eth0")
        r2.cmd("ip addr flush dev r2-eth1")

        # Apply the intended router addressing explicitly.
        r1.cmd("ip addr add 172.16.1.1/24 dev r1-eth0")
        r1.cmd("ip addr add 10.255.0.1/30 dev r1-eth1")

        r2.cmd("ip addr add 10.255.0.2/30 dev r2-eth0")
        r2.cmd("ip addr add 172.16.2.1/24 dev r2-eth1")

        # Start isolated FRR instances.
        configure_daemon(
            r1,
            "zebra",
            "hostname r1\nlog stdout",
            FRR_ROOT,
        )

        configure_daemon(
            r2,
            "zebra",
            "hostname r2\nlog stdout",
            FRR_ROOT,
        )

        configure_daemon(
            r1,
            "bgpd",
            BGP_R1,
            FRR_ROOT,
        )

        configure_daemon(
            r2,
            "bgpd",
            BGP_R2,
            FRR_ROOT,
        )

        CLI(net)

    finally:
        stop_daemons(r1, ("bgpd", "zebra"))
        stop_daemons(r2, ("bgpd", "zebra"))
        net.stop()


if __name__ == "__main__":
    setLogLevel("info")
    main()