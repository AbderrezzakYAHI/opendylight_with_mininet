# BGP

`topology/bgp_lab.py` creates two FRR routers in different ASes and starts eBGP.

- r1: AS 65001
- r2: AS 65002

Run:

```bash
sudo python3 topology/bgp_lab.py
```

Verify:

```text
r1 vtysh -c "show bgp summary"
r2 vtysh -c "show bgp summary"
r1 vtysh -c "show bgp ipv4 unicast"
```

Expected: the eBGP session becomes `Established` and the two LAN prefixes are exchanged.
