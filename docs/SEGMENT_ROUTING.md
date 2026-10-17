# Segment Routing / SR-MPLS

`topology/segment_routing_lab.py` provides a small OSPF + Segment Routing lab foundation.

Conceptual flow:

```text
OSPF
  -> loopback reachability
  -> Prefix-SID / Node-SID
  -> MPLS labels
  -> SR-MPLS forwarding
```

Run:

```bash
sudo python3 topology/segment_routing_lab.py
```

Verify:

```text
r1 vtysh -c "show ip ospf database segment-routing"
r1 ip -f mpls route
r2 ip -f mpls route
```

SR-MPLS support is dependent on the exact FRR and Linux kernel versions. The configuration therefore serves as a lab starting point rather than a universal production configuration.
