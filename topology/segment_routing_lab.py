#!/usr/bin/env python3
"""SR-MPLS lab using FRR OSPF and the Linux MPLS dataplane."""

from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import info, setLogLevel
from mininet.net import Mininet
from mininet.node import Node

from frr_helpers import configure_daemon, stop_daemons


FRR_ROOT = "/tmp/odl-mininet-frr"
MPLS_LABELS = 100000


class LinuxRouter(Node):
    """Linux router namespace with IPv4 forwarding and MPLS enabled."""

    def config(self, **params):
        super().config(**params)

        self.cmd("sysctl -w net.ipv4.ip_forward=1")
        self.cmd("sysctl -w net.ipv4.conf.all.rp_filter=0")
        self.cmd("sysctl -w net.ipv4.conf.default.rp_filter=0")

        # Enable the MPLS platform label table.
        self.cmd(
            f"sysctl -w net.mpls.platform_labels={MPLS_LABELS}"
        )

    def enable_mpls_input(self):
        """Enable MPLS packet input on all router interfaces."""
        for intf in self.intfNames():
            if intf == "lo" or intf.startswith(self.name + "-eth"):
                self.cmd(
                    f"sysctl -w net.mpls.conf.{intf}.input=1"
                )

    def terminate(self):
        self.cmd("sysctl -w net.ipv4.ip_forward=0")
        super().terminate()


OSPF_SR = {
    "r1": """\
hostname r1
password frr

router ospf
 ospf router-id 1.1.1.1
 segment-routing on
 segment-routing global-block 16000 23999
 segment-routing node-msd 16
 segment-routing prefix 10.255.1.1/32 index 1
 network 10.20.1.0/24 area 0
 network 10.20.12.0/30 area 0
 network 10.255.1.1/32 area 0

log stdout
""",

    "r2": """\
hostname r2
password frr

router ospf
 ospf router-id 2.2.2.2
 segment-routing on
 segment-routing global-block 16000 23999
 segment-routing node-msd 16
 segment-routing prefix 10.255.2.2/32 index 2
 network 10.20.12.0/30 area 0
 network 10.20.23.0/30 area 0
 network 10.255.2.2/32 area 0

log stdout
""",

    "r3": """\
hostname r3
password frr

router ospf
 ospf router-id 3.3.3.3
 segment-routing on
 segment-routing global-block 16000 23999
 segment-routing node-msd 16
 segment-routing prefix 10.255.3.3/32 index 3
 network 10.20.3.0/24 area 0
 network 10.20.23.0/30 area 0
 network 10.255.3.3/32 area 0

log stdout
""",
}


def main() -> None:
    net = Mininet(controller=None, link=TCLink)

    # Do not let Mininet assign default 10.0.0.0/8 router addresses.
    r1 = net.addHost("r1", cls=LinuxRouter, ip=None)
    r2 = net.addHost("r2", cls=LinuxRouter, ip=None)
    r3 = net.addHost("r3", cls=LinuxRouter, ip=None)

    h1 = net.addHost(
        "h1",
        ip="10.20.1.10/24",
        defaultRoute="via 10.20.1.1",
    )

    h2 = net.addHost(
        "h2",
        ip="10.20.3.10/24",
        defaultRoute="via 10.20.3.1",
    )

    # h1 <-> r1
    net.addLink(
        h1,
        r1,
        params1={"ip": "10.20.1.10/24"},
        params2={"ip": "10.20.1.1/24"},
    )

    # r1 <-> r2
    net.addLink(
        r1,
        r2,
        params1={"ip": "10.20.12.1/30"},
        params2={"ip": "10.20.12.2/30"},
    )

    # r2 <-> r3
    net.addLink(
        r2,
        r3,
        params1={"ip": "10.20.23.1/30"},
        params2={"ip": "10.20.23.2/30"},
    )

    # r3 <-> h2
    net.addLink(
        r3,
        h2,
        params1={"ip": "10.20.3.1/24"},
        params2={"ip": "10.20.3.10/24"},
    )

    try:
        net.start()

        # Explicit router addressing.
        r1.cmd("ip addr flush dev r1-eth0")
        r1.cmd("ip addr flush dev r1-eth1")

        r2.cmd("ip addr flush dev r2-eth0")
        r2.cmd("ip addr flush dev r2-eth1")

        r3.cmd("ip addr flush dev r3-eth0")
        r3.cmd("ip addr flush dev r3-eth1")

        r1.cmd("ip addr add 10.20.1.1/24 dev r1-eth0")
        r1.cmd("ip addr add 10.20.12.1/30 dev r1-eth1")

        r2.cmd("ip addr add 10.20.12.2/30 dev r2-eth0")
        r2.cmd("ip addr add 10.20.23.1/30 dev r2-eth1")

        r3.cmd("ip addr add 10.20.23.2/30 dev r3-eth0")
        r3.cmd("ip addr add 10.20.3.1/24 dev r3-eth1")

        # SR loopbacks.
        loopbacks = (
            (r1, "10.255.1.1/32"),
            (r2, "10.255.2.2/32"),
            (r3, "10.255.3.3/32"),
        )

        for router, address in loopbacks:
            router.cmd(
                f"ip addr add {address} dev lo 2>/dev/null || true"
            )

        # Enable MPLS input on all relevant interfaces.
        for router in (r1, r2, r3):
            router.enable_mpls_input()

        info("*** Starting FRR OSPF Segment Routing\n")

        for router in (r1, r2, r3):
            configure_daemon(
                router,
                "zebra",
                f"hostname {router.name}\nlog stdout",
                FRR_ROOT,
            )

            configure_daemon(
                router,
                "ospfd",
                OSPF_SR[router.name],
                FRR_ROOT,
            )

        CLI(net)

    finally:
        for router in (r1, r2, r3):
            stop_daemons(router, ("ospfd", "zebra"))

        net.stop()


if __name__ == "__main__":
    setLogLevel("info")
    main()