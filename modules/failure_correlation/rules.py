"""Rule catalog for failure correlation — symptoms, noise, and hypotheses.

Each RULE matches a log (or CLI) line and contributes structured evidence.
Hypotheses are composed later by correlator.py from evidence clusters.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Pattern, Tuple
import re

# Categories used in UI filters / KPI chips
CAT_INTERFACE = 'interface'
CAT_VPC = 'vpc'
CAT_PROTOCOL = 'protocol'
CAT_SECURITY = 'security'
CAT_HARDWARE = 'hardware'
CAT_CONFIG = 'config'
CAT_SYSTEM = 'system'
CAT_NOISE = 'noise'

SEVERITY_ORDER = {'critical': 0, 'error': 1, 'warning': 2, 'info': 3, 'noise': 4}


def _rx(pattern: str, flags: int = re.IGNORECASE) -> Pattern[str]:
    return re.compile(pattern, flags)


# (rule_id, category, severity, regex, symptom_code, title, engineer_hint)
RULES: List[Tuple[str, str, str, Pattern[str], str, str, str]] = [
    # ── Interface / link ──────────────────────────────────────────────
    (
        'IF_DOWN_LINK_FAILURE', CAT_INTERFACE, 'error',
        _rx(r'IF_DOWN_LINK_FAILURE|LINK[_ ]?FAILURE|lost\s+carrier|no\s+carrier|Ethernet.*down.*link'),
        'INTERFACE_DOWN', 'Link failure (PHY / carrier lost)',
        'Check cable, SFP/optic, remote peer power, and show interface counters errors.',
    ),
    (
        'IF_DOWN_ADMIN', CAT_INTERFACE, 'warning',
        _rx(r'IF_DOWN_ADMIN_DOWN|administratively down|interface.*shutdown'),
        'INTERFACE_ADMIN_DOWN', 'Administratively shut',
        'Interface was shut by config/operator — verify intent before no shutdown.',
    ),
    (
        'IF_ERRDISABLE', CAT_INTERFACE, 'critical',
        _rx(r'ERR[_-]?DISABLE|error[_ ]?disabled|errdisable'),
        'ERRDISABLE', 'Err-disabled',
        'Clear cause (BPDU guard, UDLD, security violation, etc.) then errdisable recovery or bounce.',
    ),
    (
        'IF_BPDU_GUARD', CAT_SECURITY, 'critical',
        _rx(r'BPDU[_ ]?GUARD|spanning.?tree.*bpdu.?guard|received\s+BPDU.*guard'),
        'BPDU_GUARD', 'BPDU Guard trip',
        'Unexpected BPDU on access edge — find rogue switch/bridge or mis-cabled trunk.',
    ),
    (
        'IF_UDLD', CAT_INTERFACE, 'error',
        _rx(r'\bUDLD\b|uni.?directional\s+link'),
        'UDLD', 'UDLD unidirectional link',
        'Fiber/SFP one-way fault common — replace optic/cable; verify both ends UDLD mode.',
    ),
    (
        'IF_STORM', CAT_INTERFACE, 'warning',
        _rx(r'storm.?control|BROADCAST.*threshold|multicast.*suppress'),
        'STORM_CONTROL', 'Storm-control suppress',
        'Broadcast/multicast storm or misconfig — check loops and storm-control thresholds.',
    ),
    (
        'IF_UPDOWN', CAT_INTERFACE, 'info',
        _rx(r'LINEPROTO.*UPDOWN|LINK-3-UPDOWN|interface .* changed state to (up|down)'),
        'LINK_STATE_CHANGE', 'Link state change',
        'Correlate with preceding IF_DOWN_* / errdisable / peer reload lines in the same window.',
    ),
    (
        'IF_CRC', CAT_INTERFACE, 'warning',
        _rx(r'\bCRC\b|input errors|giants|runts|symbol errors'),
        'LAYER1_ERRORS', 'Layer-1 errors (CRC/input)',
        'Dirty fiber, bad SFP, duplex mismatch, or EMI — clean/replace physical path.',
    ),
    # ── vPC / MLAG ────────────────────────────────────────────────────
    (
        'VPC_KEEPALIVE', CAT_VPC, 'critical',
        _rx(r'v?PC.*keep-?alive.*(fail|down|timeout|lost|not\s+operational)|peer-keep-?alive.*(fail|down|timeout)'),
        'VPC_KEEPALIVE_FAIL', 'vPC peer-keepalive failed',
        'Check mgmt/keepalive VRF reachability, ACL, routing to peer keepalive IP; peer reload?',
    ),
    (
        'VPC_PEERLINK', CAT_VPC, 'critical',
        _rx(r'peer-link.*(down|fail)|v?PC.*peer-?link.*(down|fail)|CIF-3-PEER_LINK_DOWN'),
        'VPC_PEERLINK_DOWN', 'vPC peer-link down',
        'Peer-link members/optics first; dual-active risk — stabilize peer-link before dual-homed hosts.',
    ),
    (
        'VPC_CONSISTENCY', CAT_VPC, 'error',
        _rx(r'consistency\s+check.*(fail|type.?1|suspend)|type-1\s+inconsistency|vpc.*suspend'),
        'VPC_CONSISTENCY', 'vPC consistency failure',
        'Align VLAN/STP/MTU/LACP params between peers (show vpc consistency-parameters).',
    ),
    (
        'VPC_DUAL_ACTIVE', CAT_VPC, 'critical',
        _rx(r'dual.?active|split.?brain'),
        'VPC_DUAL_ACTIVE', 'vPC dual-active / split-brain',
        'Emergency: isolate one peer secondary; restore keepalive + peer-link before rejoin.',
    ),
    (
        'VPC_ROLE', CAT_VPC, 'warning',
        _rx(r'vPC.*role.*(change|primary|secondary)|elected\s+primary'),
        'VPC_ROLE_CHANGE', 'vPC role change',
        'Often follows peer reload — confirm orphan ports and dual-homed host impact.',
    ),
    # ── Routing / first-hop ───────────────────────────────────────────
    (
        'OSPF_ADJ', CAT_PROTOCOL, 'error',
        _rx(r'OSPF.*NBR.*DOWN|OSPF-5-ADJCHG|OSPF.*neighbor\s+\S+\s+.*\bDown\b'),
        'OSPF_DOWN', 'OSPF adjacency down',
        'Check link, MTU, area, authentication, and bidirectional reachability to neighbor.',
    ),
    (
        'BGP_DOWN', CAT_PROTOCOL, 'error',
        _rx(r'BGP.*\bDOWN\b|BGP-5-ADJCHANGE.*\bDown\b|BGP.*neighbor\s+\S+.*remote\s+AS.*\bdown\b'),
        'BGP_DOWN', 'BGP session down',
        'Check TCP/179 path, TTL security, auth, and max-prefix / hold timer expiry.',
    ),
    (
        'HSRP_CHANGE', CAT_PROTOCOL, 'warning',
        _rx(r'(HSRP|VRRP|GLBP).*state.*(Active|Standby|Speak|Init)'),
        'FHRP_CHANGE', 'First-hop redundancy state change',
        'May indicate uplink loss or peer failure — verify VIP owners and tracked interfaces.',
    ),
    # ── Security / AAA ────────────────────────────────────────────────
    (
        'AUTH_FAIL', CAT_SECURITY, 'warning',
        _rx(r'LOGIN_FAILED|authentication\s+failed|AAA.*FAIL|Invalid\s+user'),
        'AUTH_FAIL', 'Authentication failure',
        'Credential/RADIUS issue or attack — check AAA servers and source IP.',
    ),
    (
        'PORT_SECURITY', CAT_SECURITY, 'error',
        _rx(r'PORT_SECURITY|psecure.?violation|security violation'),
        'PORT_SECURITY', 'Port-security violation',
        'MAC flood or moved host — clear secure MAC / raise max / find sticky conflict.',
    ),
    # ── Hardware / environment ────────────────────────────────────────
    (
        'FAN_POWER_TEMP', CAT_HARDWARE, 'critical',
        _rx(r'FAN.*FAIL|POWER.*FAIL|TEMPERATURE.*ALARM|environmental\s+monitor'),
        'HARDWARE_ALARM', 'Environmental / power / fan alarm',
        'Hardware priority — check PSU, fans, airflow; plan RMA if persistent.',
    ),
    (
        'MODULE_DOWN', CAT_HARDWARE, 'error',
        _rx(r'Module .* down|CARD_DOWN|XBAR.*fail|LC.*offline'),
        'MODULE_DOWN', 'Linecard / module down',
        'Check module status and logs around insertion/removal or fabric errors.',
    ),
    # ── Config / ops ──────────────────────────────────────────────────
    (
        'CONFIG_CHANGE', CAT_CONFIG, 'info',
        _rx(r'CONFIG_I|Configured from|\%SYS-5-CONFIG_I|commit complete'),
        'CONFIG_CHANGE', 'Configuration change',
        'Not a failure by itself — correlate if outage starts immediately after change.',
    ),
    (
        'RELOAD', CAT_SYSTEM, 'warning',
        _rx(r'System restarted|reload|cold.?boot|\%SYS-5-RESTART'),
        'DEVICE_RELOAD', 'Device reload / restart',
        'Peer-facing features (vPC/HSRP/OSPF) will flap — check why reload occurred.',
    ),
    # ── Noise (explicitly discarded from “why” unless only evidence) ───
    (
        'NOISE_CDP_LLDP', CAT_NOISE, 'noise',
        _rx(r'CDP-4-|LLDP.*timer|Native VLAN mismatch.*informational'),
        'NOISE', 'Informational neighbor noise',
        'Usually not root cause — keep if nothing else matches in the window.',
    ),
    (
        'NOISE_DEBUG', CAT_NOISE, 'noise',
        _rx(r'^debug |\%DEBUG|TRACE:'),
        'NOISE', 'Debug trace noise',
        'Disable debug after collection; do not treat as primary root cause.',
    ),
]


def match_line(line: str) -> Optional[Dict[str, Any]]:
    """Return first matching rule dict for a log/CLI line, or None."""
    text = (line or '').strip()
    if not text:
        return None
    for rule_id, cat, sev, rx, symptom, title, hint in RULES:
        m = rx.search(text)
        if not m:
            continue
        return {
            'rule_id': rule_id,
            'category': cat,
            'severity': sev,
            'symptom_code': symptom,
            'title': title,
            'hint': hint,
            'evidence': text[:500],
            'match': m.group(0)[:120],
        }
    return None


def extract_interface(text: str) -> Optional[str]:
    """Best-effort interface token from Cisco-like log text."""
    patterns = [
        r'\b((?:Ethernet|Eth|GigabitEthernet|Gi|TenGigabitEthernet|Te|FastEthernet|Fa|port-channel|Po|mgmt)\d+(?:/\d+)*(?:\.\d+)?)\b',
        r'\b((?:Ethernet|Eth)\d+/\d+)\b',
    ]
    for p in patterns:
        m = re.search(p, text or '', re.I)
        if m:
            return m.group(1)
    return None


def all_rule_ids() -> List[str]:
    return [r[0] for r in RULES]
