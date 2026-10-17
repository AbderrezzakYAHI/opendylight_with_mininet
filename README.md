# OpenDayLight With Mininet

SDN and service-provider routing lab using **OpenDaylight, Mininet, Open vSwitch and FRRouting (FRR)**.

Inspired by [RYU_With_Mininet](https://github.com/AbderrezzakYAHI/RYU_With_Mininet), this project extends the original lab toward:

- OpenDaylight + OpenFlow 1.3
- Mininet virtual topologies
- OSPF with FRR
- eBGP with FRR
- Segment Routing / SR-MPLS foundation

## Architecture

```text
                         OpenDaylight
                       RESTCONF / OpenFlow
                              |
                         OpenFlow 1.3
                              |
                    +---------v----------+
                    | Open vSwitch/OVS   |
                    |      Mininet       |
                    +---------+----------+
                              |
                 +------------+------------+
                 | Linux router namespaces |
                 |          + FRR          |
                 | OSPF / BGP / SR-MPLS   |
                 +-------------------------+
```

OpenDaylight is the SDN controller for the OpenFlow portion. FRR provides the routing control plane in the Mininet router namespaces.

## Requirements

Recommended host:

- Ubuntu 22.04 or 24.04
- 4 CPU cores
- 8 GB RAM
- sudo access

Install the host packages:

```bash
sudo apt update
sudo apt install -y mininet openvswitch-switch frr git curl python3
```

Validate:

```bash
chmod +x scripts/*.sh
sudo ./scripts/check_requirements.sh
```

## OpenDaylight

Install a compatible OpenDaylight distribution separately. Start OpenDaylight and enable the OpenFlow plugin required by your release.

For current releases, consult the official OpenDaylight documentation for the exact feature/module names. RESTCONF and OpenFlow plugin APIs are release-dependent.

## 1. OpenDaylight + Mininet

Start OpenDaylight first and expose OpenFlow on TCP/6653, then run:

```bash
sudo python3 topology/basic_sdn.py
```

Inside Mininet:

```text
pingall
net
sh ovs-vsctl show
```

## 2. OSPF

Run:

```bash
sudo python3 topology/ospf_lab.py
```

The script creates three Linux router namespaces and starts FRR OSPF processes for the lab.

Verify from the Mininet CLI:

```text
r1 vtysh -c "show ip ospf neighbor"
r2 vtysh -c "show ip ospf neighbor"
r2 vtysh -c "show ip route ospf"
```

## 3. BGP

Run:

```bash
sudo python3 topology/bgp_lab.py
```

The example uses eBGP:

```text
r1 = AS 65001
r2 = AS 65002
```

Verify:

```text
r1 vtysh -c "show bgp summary"
r2 vtysh -c "show bgp summary"
r1 vtysh -c "show bgp ipv4 unicast"
```

## 4. Segment Routing / SR-MPLS

Run:

```bash
sudo python3 topology/segment_routing_lab.py
```

The lab prepares an OSPF-based topology with SR-MPLS configuration for FRR/Linux. Verify the control plane and MPLS state with:

```text
r1 vtysh -c "show ip ospf neighbor"
r1 vtysh -c "show ip ospf database segment-routing"
r1 ip -f mpls route
r2 ip -f mpls route
```

Exact SR-MPLS capabilities and configuration syntax depend on the FRR build and Linux kernel.

## Cleanup

```bash
sudo mn -c
# or
sudo ./scripts/clean.sh
```

## Project structure

```text
opendylight_with_mininet/
├── topology/
│   ├── basic_sdn.py
│   ├── ospf_lab.py
│   ├── bgp_lab.py
│   └── segment_routing_lab.py
├── frr/
│   ├── README.md
│   └── segment-routing.conf.example
├── scripts/
│   ├── check_requirements.sh
│   └── clean.sh
├── docs/
│   ├── OSPF.md
│   ├── BGP.md
│   └── SEGMENT_ROUTING.md
├── requirements.txt
├── .gitignore
└── README.md
```