# Network Swiss Tool Pro — Labs

## Tier A — Docker SSH fabric (default, running)

**Topology:** 1× IOS C9300-24P + 2× NX-OS **N9K-C93180YC-EX** (CLI simulators with CDP).

| Port | Hostname | Platform |
|------|----------|----------|
| 2201 | LAB-IOS-ACCESS1 | C9300-24P |
| 2202 | LAB-NXOS-LEAF1 | N9K-C93180YC-EX |
| 2203 | LAB-NXOS-LEAF2 | N9K-C93180YC-EX |

```bash
./lab/scripts/start-ssh-lab.sh
# Commit lab/docker/inventory.nst.txt in NST Inventory
# Add vault credential (any password) → select as Primary sidebar
# Validate: python scripts/lab_exhaustive_validate.py --credential-id <id>
```

**Credential rule (Zero Trust):** Settings password boxes are **draft only**. Execute uses vault `credential_id` only.

**Failure correlation:** Swiss Tools → Inventory utilities → **Failure correlation** (lab fixtures include link-down, vPC keepalive fail, BPDU err-disable, OSPF down).

## Tier B — Real NX-OS Clos (Containerlab)

See `lab/containerlab/` — requires your Cisco N9Kv qcow2 (~24 GB RAM).
