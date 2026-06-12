from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import random
import time


DOMAINS = ("network", "linux", "windows", "vmware")
SEVERITIES = ("info", "warning", "error", "critical")
ABNORMAL_SEVERITIES = ("warning", "error", "critical")


@dataclass(frozen=True)
class GeneratedLogLine:
    domain: str
    severity: str
    path: Path
    text: str


def generate_log_lines(
    log_root_path: Path,
    count: int,
    interval_seconds: float,
    domain: str = "all",
    severity: str = "abnormal",
) -> list[GeneratedLogLine]:
    generated = []
    for index in range(count):
        generated.append(generate_one_log_line(log_root_path, domain=domain, severity=severity))
        if index < count - 1 and interval_seconds > 0:
            time.sleep(interval_seconds)
    return generated


def generate_one_log_line(log_root_path: Path, domain: str = "all", severity: str = "abnormal") -> GeneratedLogLine:
    selected_domain = _pick_domain(domain)
    selected_severity = _pick_severity(severity)
    template = random.choice(TEMPLATES[selected_domain][selected_severity])
    now = datetime.now().astimezone()
    text = template(now)

    output_dir = log_root_path / selected_domain
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"dynamic-{selected_domain}.log"
    with output_path.open("a", encoding="utf-8") as handle:
        handle.write(text + "\n")

    return GeneratedLogLine(
        domain=selected_domain,
        severity=selected_severity,
        path=output_path,
        text=text,
    )


def _pick_domain(domain: str) -> str:
    normalized = domain.lower()
    if normalized == "all":
        return random.choice(DOMAINS)
    if normalized not in DOMAINS:
        raise ValueError(f"Unsupported domain '{domain}'. Expected one of: all, {', '.join(DOMAINS)}")
    return normalized


def _pick_severity(severity: str) -> str:
    normalized = severity.lower()
    if normalized == "all":
        return random.choice(SEVERITIES)
    if normalized == "abnormal":
        return random.choice(ABNORMAL_SEVERITIES)
    if normalized not in SEVERITIES:
        raise ValueError(f"Unsupported severity '{severity}'. Expected one of: all, abnormal, {', '.join(SEVERITIES)}")
    return normalized


def _iso(now: datetime) -> str:
    return now.isoformat(timespec="seconds")


def _syslog(now: datetime) -> str:
    return now.strftime("%b %d %H:%M:%S")


def _rand_ip(prefix: str = "10.255.0") -> str:
    return f"{prefix}.{random.randint(2, 254)}"


def _rand_public_ip() -> str:
    return f"203.0.113.{random.randint(10, 250)}"


def _rand_interface() -> str:
    return random.choice(["TenGigabitEthernet1/0/48", "Gi1/0/12", "Port-channel10", "Gi2/0/21"])


TEMPLATES = {
    "network": {
        "info": [
            lambda now: f"{_iso(now)} core-sw01.example.local %SYS-5-CONFIG_I: Configured from console by netadmin on vty0 (10.10.10.5)",
        ],
        "warning": [
            lambda now: f"{_iso(now)} edge-fw01.example.local %ASA-4-106023: Deny tcp src outside:{_rand_public_ip()}/443 dst inside:10.20.30.15/50432 by access-group \"OUTSIDE-IN\"",
            lambda now: f"{_iso(now)} access-sw07.example.local %PM-4-ERR_DISABLE: loopback error detected on Gi1/0/12, putting Gi1/0/12 in err-disable state",
            lambda now: f"{_iso(now)} dist-sw02.example.local %C4K_EBM-4-HOSTFLAPPING: Host 00:50:56:aa:bb:cc in vlan 120 is flapping between port Gi2/0/17 and Gi2/0/21",
        ],
        "error": [
            lambda now: f"{_iso(now)} dist-sw02.example.local %LINK-3-UPDOWN: Interface {_rand_interface()}, changed state to down",
            lambda now: f"{_iso(now)} edge-fw01.example.local %ASA-3-210007: LU allocate connection failed, memory pressure high, current memory usage {random.randint(90, 98)} percent",
        ],
        "critical": [
            lambda now: f"{_iso(now)} core-rtr01.example.local %BGP-5-ADJCHANGE: neighbor {_rand_ip()} Down BGP Notification sent",
            lambda now: f"{_iso(now)} core-rtr01.example.local %OSPF-5-ADJCHG: Process 100, Nbr {_rand_ip()} on Port-channel10 from FULL to DOWN, Neighbor Down: Dead timer expired",
            lambda now: f"{_iso(now)} core-sw01.example.local %PLATFORM-2-PS_FAIL: Power supply 2 failed or removed",
        ],
    },
    "linux": {
        "info": [
            lambda now: f"{_syslog(now)} linux-web01.example.local systemd[1]: Started nginx.service - A high performance web server.",
        ],
        "warning": [
            lambda now: f"{_syslog(now)} linux-web01.example.local sshd[1842]: Failed password for invalid user admin from {_rand_public_ip()} port 51520 ssh2",
            lambda now: f"{_syslog(now)} linux-api02.example.local kernel: EXT4-fs warning (device sda1): ext4_dx_add_entry: Directory index full",
            lambda now: f"{_syslog(now)} linux-web01.example.local kernel: TCP: request_sock_TCP: Possible SYN flooding on port 443. Sending cookies.",
        ],
        "error": [
            lambda now: f"{_syslog(now)} linux-api02.example.local systemd[1]: app-worker.service: Main process exited, code=exited, status=1/FAILURE",
            lambda now: f"{_syslog(now)} linux-web01.example.local nginx[1902]: upstream timed out (110: Connection timed out) while reading response header from upstream, client: 10.50.10.8, server: app.example.local",
        ],
        "critical": [
            lambda now: f"{_syslog(now)} linux-db01.example.local kernel: blk_update_request: critical medium error, dev sdb, sector {random.randint(8000000, 9999999)}",
            lambda now: f"{_syslog(now)} linux-api02.example.local systemd[1]: payment-worker.service: Main process exited, code=exited, status=1/FAILURE",
        ],
    },
    "windows": {
        "info": [
            lambda now: f"{_iso(now)} WIN-AD01.example.local Security EventID=4624 Level=Information User=svc_monitor LogonType=3 Message=\"An account was successfully logged on\"",
        ],
        "warning": [
            lambda now: f"{_iso(now)} WIN-AD01.example.local Security EventID=4625 Level=Warning User=svc_backup SourceIP=10.40.10.{random.randint(10, 99)} Message=\"An account failed to log on\"",
            lambda now: f"{_iso(now)} WIN-FILE01.example.local System EventID=2013 Level=Warning Source=Srv Message=\"The C: disk is at or near capacity. Free space is {random.randint(4, 9)} percent\"",
        ],
        "error": [
            lambda now: f"{_iso(now)} WIN-APP02.example.local Application EventID=1000 Level=Error Source=Application Error Message=\"Faulting application name: app-worker.exe, exception code: 0xc0000005\"",
            lambda now: f"{_iso(now)} WIN-APP02.example.local System EventID=6008 Level=Error Source=EventLog Message=\"The previous system shutdown was unexpected\"",
        ],
        "critical": [
            lambda now: f"{_iso(now)} WIN-DB01.example.local System EventID=7031 Level=Critical Source=Service Control Manager Message=\"The SQLAgent service terminated unexpectedly. It has done this {random.randint(2, 5)} time(s)\"",
        ],
    },
    "vmware": {
        "info": [
            lambda now: f"{_iso(now)} vcenter01.example.local vpxd[12001]: Event=VmPoweredOnEvent VM=app-web-{random.randint(1, 9):02d} Host=esxi-01.example.local User=ops.user Message=\"Virtual machine powered on\"",
        ],
        "warning": [
            lambda now: f"{_iso(now)} vcenter01.example.local vpxd[12001]: Event=DatastoreUsageOnDiskWarning Datastore=ds-prod-01 Usage={random.randint(84, 93)}% Message=\"Datastore usage on disk has exceeded warning threshold\"",
            lambda now: f"{_iso(now)} esxi-01.example.local hostd[10122]: warning hostd[10122] [Originator@6876 sub=Vimsvc.ha-eventmgr] Event 12345: Host memory usage is high: {random.randint(88, 96)} percent",
        ],
        "error": [
            lambda now: f"{_iso(now)} vcenter01.example.local vpxd[12001]: Event=VmFailedMigrateEvent VM=app-db-02 SourceHost=esxi-01.example.local DestHost=esxi-02.example.local Message=\"vMotion migration failed due to network timeout\"",
            lambda now: f"{_iso(now)} vcenter01.example.local vpxd[12001]: Event=VmPoweredOffEvent VM=legacy-app-01 User=unknown Message=\"Virtual machine powered off unexpectedly\"",
        ],
        "critical": [
            lambda now: f"{_iso(now)} esxi-03.example.local vmkernel: cpu4:2103311)ALERT: APD: All paths down for device naa.6000c29b2",
            lambda now: f"{_iso(now)} vcenter01.example.local vpxd[12001]: Event=DasHostFailedEvent Host=esxi-03.example.local Cluster=prod-cluster Message=\"vSphere HA detected a host failure\"",
        ],
    },
}
