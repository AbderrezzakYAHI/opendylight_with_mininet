#!/usr/bin/env python3

from pathlib import Path
from typing import Iterable

DEFAULT_RUN_ROOT = Path("/tmp/odl-mininet-frr")
FRR_BIN = Path("/usr/lib/frr")
VTYSH = Path("/usr/bin/vtysh")


def router_paths(node, run_root=None):
    """
    Create isolated runtime paths for one Mininet router.
    """
    base = Path(run_root) if run_root else DEFAULT_RUN_ROOT

    root = base / node.name
    vty = root / "vty"
    zapi = root / "zserv.api"

    root.mkdir(parents=True, exist_ok=True)
    vty.mkdir(parents=True, exist_ok=True)
    # FRR daemons drop privileges to the "frr" user.
    # The runtime directory must therefore be writable by that user.
    node.cmd(f"chown -R frr:frr {root}")
    node.cmd(f"chmod 755 {root}")
    node.cmd(f"chmod 755 {vty}")

    return root, vty, zapi


def configure_daemon(node, daemon: str, config: str, run_root=None) -> None:
    """
    Start one FRR daemon inside a Mininet namespace.

    Compatible with the current ospf_lab.py / bgp_lab.py callers.
    """
    root, vty, zapi = router_paths(node, run_root)

    daemon_bin = FRR_BIN / daemon
    conf = root / f"{daemon}.conf"
    pid = root / f"{daemon}.pid"
    log = root / f"{daemon}.log"

    if not daemon_bin.exists():
        raise RuntimeError(f"FRR daemon not found: {daemon_bin}")

    # Write configuration.
    conf.write_text(config, encoding="utf-8")

    # FRR daemons run as user 'frr' on Ubuntu.
    node.cmd(f"chmod 755 {root}")
    node.cmd(f"chmod 755 {vty}")
    node.cmd(f"chmod 644 {conf}")

    # Start the daemon using the Ubuntu FRR binary path.
    command = (
        f"{daemon_bin} "
        f"-d "
        f"-f {conf} "
        f"-i {pid} "
        f"-z {zapi} "
        f"--vty_socket {vty} "
        f"--log file:{log}"
    )

    output = node.cmd(command)

    # Give the daemon time to initialize.
    node.cmd("sleep 1")

    if not pid.exists():
        log_output = node.cmd(
            f"cat {log} 2>/dev/null || true"
        )

        raise RuntimeError(
            f"Failed to start {daemon} on {node.name}\n"
            f"Command output: {output}\n"
            f"Log:\n{log_output}"
        )


def vtysh(node, command: str, run_root=None) -> str:
    """
    Execute vtysh against the isolated FRR instance.
    """
    _, vty, _ = router_paths(node, run_root)

    return node.cmd(
        f"{VTYSH} "
        f"--vty_socket {vty} "
        f"-c '{command}'"
    )


def stop_daemons(
    node,
    daemons: Iterable[str],
    run_root=None
) -> None:
    """
    Stop only the daemons belonging to this Mininet router.
    """
    root, _, _ = router_paths(node, run_root)

    for daemon in daemons:
        pid_file = root / f"{daemon}.pid"

        if pid_file.exists():
            pid = node.cmd(
                f"cat {pid_file} 2>/dev/null"
            ).strip()

            if pid.isdigit():
                node.cmd(
                    f"kill -TERM {pid} 2>/dev/null || true"
                )

        node.cmd(f"rm -f {pid_file}")
