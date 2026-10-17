# OSPF

`topology/ospf_lab.py` builds a three-router routed topology and starts FRR OSPF in the Mininet namespaces.

Run:

```bash
sudo python3 topology/ospf_lab.py
```

Verify:

```text
r1 vtysh -c "show ip ospf neighbor"
r2 vtysh -c "show ip ospf neighbor"
r2 vtysh -c "show ip route ospf"
```

Expected: OSPF adjacencies between adjacent routers and learned routes for the remote LANs.
