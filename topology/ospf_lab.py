#!/usr/bin/env python3
"""Mininet + FRR OSPF routed lab."""

from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import info, setLogLevel
from mininet.net import Mininet
from mininet.node import Node

from frr_helpers import configure_daemon, stop_daemons


class LinuxRouter(Node):
    def config(self, **params):
        super().config(**params)
        self.cmd("sysctl -w net.ipv4.ip_forward=1")
        self.cmd("sysctl -w net.ipv4.conf.all.rp_filter=0")
        self.cmd("sysctl -w net.ipv4.conf.default.rp_filter=0")

    def terminate(self):
        self.cmd("sysctl -w net.ipv4.ip_forward=0")
        super().terminate()


OSPF = {
    "r1": """hostname r1
password frr
router ospf
 ospf router-id 1.1.1.1
 network 10.10.1.0/24 area 0
 network 10.0.12.0/30 area 0
 redistribute connected
log stdout
""",
    "r2": """hostname r2
password frr
router ospf
 ospf router-id 2.2.2.2
 network 10.0.12.0/30 area 0
 network 10.0.23.0/30 area 0
 redistribute connected
log stdout
""",
    "r3": """hostname r3
password frr
router ospf
 ospf router-id 3.3.3.3
 network 10.0.23.0/30 area 0
 network 10.10.3.0/24 area 0
 redistribute connected
log stdout
""",
}


def main() -> None:
    net = Mininet(controller=None, link=TCLink)
    r1 = net.addHost("r1", cls=LinuxRouter, ip="10.10.1.1/24")
    r2 = net.addHost("r2", cls=LinuxRouter, ip="10.0.12.2/30")
    r3 = net.addHost("r3", cls=LinuxRouter, ip="10.0.23.3/30")
    h1 = net.addHost("h1", ip="10.10.1.10/24", defaultRoute="via 10.10.1.1")
    h2 = net.addHost("h2", ip="10.10.3.10/24", defaultRoute="via 10.10.3.1")

    net.addLink(h1, r1, params2={"ip": "10.10.1.1/24"})
    net.addLink(r1, r2, params1={"ip": "10.0.12.1/30"}, params2={"ip": "10.0.12.2/30"})
    net.addLink(r2, r3, params1={"ip": "10.0.23.2/30"}, params2={"ip": "10.0.23.3/30"})
    net.addLink(r3, h2, params1={"ip": "10.10.3.1/24"})

    try:
        net.start()
        info("*** Starting FRR OSPF daemons\n")
        for router in (r1, r2, r3):
            configure_daemon(router, "zebra", "hostname %s\nlog stdout" % router.name, "/tmp/odl-mininet-frr")
            configure_daemon(router, "ospfd", OSPF[router.name], "/tmp/odl-mininet-frr")
        info("*** Verify: r2 vtysh -c 'show ip ospf neighbor'\n")
        CLI(net)
    finally:
        for router in (r1, r2, r3):
            stop_daemons(router, ("ospfd", "zebra"))
        net.stop()


if __name__ == "__main__":
    setLogLevel("info")
    main()
