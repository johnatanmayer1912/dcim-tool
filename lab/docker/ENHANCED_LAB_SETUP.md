# Enhanced Lab Setup for Comprehensive Testing

## Lab Architecture

### Docker SSH Simulator (Current - Fast for CI/CD)
- **Purpose**: Mock SSH devices for automated testing
- **Devices**: 1× IOS C9300, 2× NX-OS N9K-C93180YC-EX
- **Start**: `cd lab/docker && docker-compose up -d`
- **Pros**: Fast, no virtualization overhead, always available
- **Cons**: Not real device behavior, limited CLI simulation

### ContainerLab Setup (Recommended for Expert Validation)
- **Purpose**: Real Cisco NX-OSv images for authentic testing
- **Devices**: 1× IOS C9300v, 2× NX-OSv (different models)
- **Start**: `cd lab/containerlab && ./deploy.sh`
- **Pros**: Real device behavior, authentic CLI, full feature testing
- **Cons**: Requires N9KV image, higher resource usage

---

## Option 1: Enhanced Docker SSH Simulator (Quick Start)

### Modified docker-compose.yml

```yaml
name: nst-ssh-lab-enhanced

services:
  ssh-sim:
    build:
      context: ../..
      dockerfile: lab/docker/Dockerfile.ssh-sim
    image: nst-ssh-sim:local
    container_name: nst-ssh-sim
    restart: unless-stopped
    ports:
      - "127.0.0.1:2201:2201"   # LAB-IOS-ACCESS1   C9300-24P
      - "127.0.0.1:2202:2202"   # LAB-NXOS-LEAF1    N9K-C93180YC-EX
      - "127.0.0.1:2203:2203"   # LAB-NXOS-LEAF2    N9K-C9348GC-XP (NEW)
    environment:
      - LAB_IOS_MODEL=C9300-24P
      - LAB_NXOS_MODEL1=N9K-C93180YC-EX
      - LAB_NXOS_MODEL2=N9K-C9348GC-XP
```

### Inventory for NST UI

```text
# Enhanced Lab Inventory
127.0.0.1,cisco_ios
127.0.0.1,cisco_nxos
127.0.0.1,cisco_nxos
```

### Start Commands

```bash
# Start lab
cd lab/docker
docker-compose up -d

# Verify connectivity
telnet 127.0.0.1 2201  # IOS
telnet 127.0.0.1 2202  # NX-OS Leaf1
telnet 127.0.0.1 2203  # NX-OS Leaf2

# Stop lab
docker-compose down
```

---

## Option 2: ContainerLab with Real NX-OSv (Expert Validation)

### Prerequisites

1. Install containerlab: https://containerlab.dev/install/
2. Pull NX-OSv image:
   ```bash
   docker pull vrnetlab/cisco_n9kv:lite.10.5.2.F
   export N9KV_IMAGE=vrnetlab/cisco_n9kv:lite.10.5.2.F
   ```

### Enhanced nst-clos.clab.yml

```yaml
name: nst-enhanced-lab

topology:
  nodes:
    # IOS Device (C9300v - simulated)
    ios-access1:
      kind: ceos
      image: ceos:latest
      mgmt-ipv4: 172.28.28.11
      startup-config: |
        interface Ethernet1
          ip address 192.168.100.11/24
        ip route 0.0.0.0/0 192.168.100.1
    
    # NX-OS Device 1 (N9K-C93180YC-EX)
    nxos-leaf1:
      kind: cisco_n9kv
      image: ${N9KV_IMAGE:-vrnetlab/cisco_n9kv:latest}
      mgmt-ipv4: 172.28.28.12
      startup-config: |
        interface Ethernet1/1
          ip address 192.168.100.12/24
        interface mgmt0
          ip address 172.28.28.12/24
    
    # NX-OS Device 2 (N9K-C9348GC-XP - different model)
    nxos-leaf2:
      kind: cisco_n9kv
      image: ${N9KV_IMAGE:-vrnetlab/cisco_n9kv:latest}
      mgmt-ipv4: 172.28.28.13
      startup-config: |
        interface Ethernet1/1
          ip address 192.168.100.13/24
        interface mgmt0
          ip address 172.28.28.13/24
    
    # Management switch (virtual)
    mgmt-sw:
      kind: ceos
      image: ceos:latest
      mgmt-ipv4: 172.28.28.10
      startup-config: |
        interface Ethernet1
          ip address 192.168.100.1/24

  links:
    - endpoints: ["ios-access1:Ethernet1", "mgmt-sw:Ethernet2"]
    - endpoints: ["nxos-leaf1:Ethernet1/1", "mgmt-sw:Ethernet3"]
    - endpoints: ["nxos-leaf2:Ethernet1/1", "mgmt-sw:Ethernet4"]
```

### Inventory for NST UI

```text
# ContainerLab Inventory
172.28.28.11,cisco_ios
172.28.28.12,cisco_nxos
172.28.28.13,cisco_nxos
```

### Start Commands

```bash
# Set image
export N9KV_IMAGE=vrnetlab/cisco_n9kv:lite.10.5.2.F

# Deploy lab
cd lab/containerlab
./deploy.sh

# Verify connectivity
ssh admin@172.28.28.11  # IOS
ssh admin@172.28.28.12  # NX-OS Leaf1
ssh admin@172.28.28.13  # NX-OS Leaf2

# Destroy lab
containerlab destroy -t nst-enhanced-lab.clab.yml
```

---

## Test Execution Workflow

### 1. Lab Startup
```bash
# Option 1: Docker SSH Simulator (Fast)
cd lab/docker
docker-compose up -d

# Option 2: ContainerLab (Real Devices)
cd lab/containerlab
export N9KV_IMAGE=vrnetlab/cisco_n9kv:lite.10.5.2.F
./deploy.sh
```

### 2. Application Startup
```bash
cd C:\Users\bbb12\OneDrive\Desktop\Antigravity Projects Folder\OCT2026\NMT
python vlan_checker_web.py
```

### 3. Test Execution
- Open browser: http://127.0.0.1:5051
- Add credentials for lab devices
- Follow COMPREHENSIVE_LAB_TEST_PLAN.md
- Execute tests in order (TEST-001 to TEST-500)

### 4. Evidence Collection
- Evidence artifacts stored in: `C:\Users\bbb12\Documents\NetworkSwissToolPro\outputs\`
- Generate test report from results
- Expert team review and sign-off

### 5. Lab Cleanup
```bash
# Option 1: Docker SSH Simulator
cd lab/docker
docker-compose down

# Option 2: ContainerLab
cd lab/containerlab
containerlab destroy -t nst-enhanced-lab.clab.yml
```

---

## Recommended Approach

### For Expert Team Validation
**Use ContainerLab (Option 2)** because:
- Real NX-OSv CLI behavior
- Authentic parsing output
- Full feature testing (vPC, OTV, etc.)
- Closer to production environment

### For Automated CI/CD
**Use Docker SSH Simulator (Option 1)** because:
- Fast startup/teardown
- Consistent mock behavior
- No virtualization overhead
- Suitable for regression testing

---

## Next Steps

1. **Choose lab option** based on testing needs
2. **Build and deploy lab** using instructions above
3. **Execute 500-test plan** from COMPREHENSIVE_LAB_TEST_PLAN.md
4. **Expert team review** with sign-off
5. **Update MANDATORY_MANIFEST.yaml** with any new test requirements
