# Parsing Logic & Normalization

The system converts raw, unstructured CLI text into structured JSON data using a combination of **Regular Expressions (Regex)** and **Manual Iteration**.

## 1. Hardware Audit Regex
These patterns identify hardware and OS attributes in `show version` output.

| OS | Attribute | Pattern |
|----|-----------|---------|
| Cisco | OS Version | `Version ([^,]+),` |
| Cisco | Serial | `Processor board ID (.*)` |
| Cisco | Model | `cisco (.+?) processor` |
| NXOS | OS Version | `system:\s+version (.*)` |
| NXOS | Model | `Hardware\s+(.*)` |
| Juniper| OS Version | `Junos: (.*)` |
| Juniper| Model | `Model: (.*)` |

## 2. Interface Name Normalization
To ensure consistent mapping across different vendor outputs (e.g., `GigabitEthernet` in CDP vs. `Gi` in CLI), the system applies the following transformation logic:

```python
def norm_int(n):
    return (n.replace("Ethernet", "Eth")
             .replace("GigabitEthernet", "Gi")
             .replace("FastEthernet", "Fa")
             .replace("TenGigabitEthernet", "Te")
             .replace("Port-channel", "Po")
             .strip())
```

## 3. Neighbor Extraction (CDP/LLDP)
The system iterates through "Detail" outputs. It maintains state (`cur_rem`, `cur_loc`) and flushes an edge object to the results list whenever a new device header is detected.

## 4. VLAN Database Parsing
Uses a standard column-based split for `show vlan brief`:
1. Strip leading/trailing whitespace.
2. Ignore header lines (contain `--`, `Interface`, etc.).
3. Split by whitespace; Extract `[0]` as ID, `[1]` as Name.

## 5. MAC Address Formatting
Target MACs are normalized to a consistent format (removing `.`, `:`, or `-`) before being compared against CLI output columns using a case-insensitive `in` check.
