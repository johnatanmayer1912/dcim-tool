# vPC Domain ID Plugin

| Metadata | Description |
| :--- | :--- |
| **Plugin ID** | `vpc_domain` |
| **Display Name** | vPC Domain ID |
| **Version** | 1.0.0 |
| **Category** | Audit |

## Purpose

Reports the **vPC domain number** when configured on Cisco NX-OS switches, along with operational telemetry useful for audits.

## Collected fields

| Field | Source |
|-------|--------|
| `domain_id` | `show vpc` / `show vpc brief` |
| `role` | primary / secondary |
| `peer_status` | peer-link status line |
| `keepalive_status` | peer-keepalive status line |

## Usage

1. Open **Plugin Tools** in the web UI.
2. Run **vPC Domain ID** against the target inventory scope.
3. Per-device reports are saved under `reports/plugins/vpc_domain/`.

Non-NX-OS devices return success with `present: false` and an explanatory message.
