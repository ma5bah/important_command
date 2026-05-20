#!/bin/bash

# ==============================================================================
# VULNHUB INTENT-LOCKED QEMU RUNNER
# ==============================================================================
# PURPOSE: This script automates an isolated layer-2 host bridge environment to
# force DHCP-based VulnHub VMs into a deterministic static IP (default 10.0.3.7).
#
# WHY THIS SPECIFIC DESIGN EXISTS (CRITICAL FOR FUTURE AGENTS):
# 1. AWS ROUTING BYPASS: The host is an AWS EC2 instance. Cloud providers drop
#    layer-3 traffic targeting unallocated subnets. We deploy a local bridge (br0)
#    to anchor a private virtual Layer-2 broadcast domain inside the host.
# 2. DNSMASQ PORT-53 COLLISION AVOIDANCE: Kali systems use systemd-resolved on 
#    port 53. dnsmasq fails to start if it tries to bind DNS. `--port=0` disables
#    the DNS daemon entirely, forcing dnsmasq to act strictly as a DHCP engine.
# 3. VIRTIO DRIVER SUBSTITUTION: Legacy VulnHub VMs fail to probe standard QEMU 
#    e1000 NICs due to old kernels. `virtio-net-pci` guarantees universal Linux 
#    kernel driver compatibility across modern host hypervisors.
# 4. DETERMINISTIC STATIC BOUNDARY: VulnHub targets request IPs via DHCP. By
#    hardcoding an arbitrary MAC address into the VM hardware flag and mapping it
#    statically within dnsmasq configurations, we intercept the request and force
#    the target onto the user's specific requested IP.
# ==============================================================================

# Ensure the execution environment has root authority to manage networking stack
if [ "$EUID" -ne 0 ]; then
  echo "[-] Privilege Error: Please run this script with sudo."
  exit 1
fi

# ==============================================================================
# GLOBAL RUNTIME CONFIGURATION
# ==============================================================================
VM_IMAGE="dc9.qcow2"             # Target virtual disk file (QCOW2 format)
TARGET_IP="10.0.3.7"             # User intent: Precise IP assigned to target
VM_MAC="52:54:00:12:34:56"       # Controlled MAC address injected into QEMU NIC
GATEWAY_IP="10.0.3.1"            # Host-side interface IP acting as gateway
SUBNET_CIDR="10.0.3.0/24"        # Network boundaries
DHCP_RANGE="10.0.3.10,10.0.3.50" # Pool range required by dnsmasq to switch on DHCP
VNC_PORT=":2"                    # VNC Display port (Maps to localhost TCP 5902)
# ==============================================================================

echo "[+] Step 1: Flashing local networking interfaces and stale daemons..."
# Kill any competing virtualization tasks or blocked sockets from prior failures
pkill -9 -f qemu 2>/dev/null
pkill -9 dnsmasq 2>/dev/null
systemctl stop dnsmasq 2>/dev/null
ip link delete br0 2>/dev/null
ip link delete tap9 2>/dev/null
sleep 1

echo "[+] Step 2: Instantiating the virtual layer-2 software bridge (br0)..."
# Build the switch topology and assign the host IP to serve as the default route
ip link add br0 type bridge
ip address add ${GATEWAY_IP}/24 dev br0
ip link set br0 up
# Force promiscuous mode so the host catches all interface frames regardless of destination MAC
ip link set br0 promisc on

echo "[+] Step 3: Spinning up and linking the host TAP interface (tap9)..."
# Create a virtual file descriptor/tunnel for packet injection into QEMU
ip tuntap add dev tap9 mode tap
ip link set tap9 master br0
ip link set tap9 up

echo "[+] Step 4: Activating localized DHCP engine with intent-locked lease mapping..."
# EXPLANATION OF FLAGS FOR SUBSEQUENT REVIEWS:
# --interface=br0   : Restricts DHCP scoping strictly to our software bridge.
# --dhcp-range      : Mandatory flag. Initializes dnsmasq's internal DHCP subsystem matrix.
# --dhcp-host       : Intercepts matching MAC hardware packets and forces the Target IP override.
# --port=0          : Disables local DNS socket bindings completely to dodge systemd-resolved lockouts.
dnsmasq --interface=br0 \
        --dhcp-range=${DHCP_RANGE},255.255.255.0,24h \
        --dhcp-host=${VM_MAC},${TARGET_IP} \
        --port=0 --no-daemon &
sleep 2

echo "[+] Step 5: Executing QEMU emulator daemon with VirtIO network emulation..."
if [ ! -f "$VM_IMAGE" ]; then
    echo "[-] File I/O Error: $VM_IMAGE not found in active directory path!"
    pkill -9 dnsmasq
    exit 1
fi

# EXPLANATION OF MACHINE PARAMETERS:
# -netdev tap       : Links QEMU backplane to the host kernel TAP driver interface we created.
# -device virtio... : Swaps hardware layer to VirtIO standard, injecting our specific tracking MAC.
# -vnc              : Sets headless display binding.
# -daemonize        : detaches execution loop back to the host shell environment safely.
qemu-system-x86_64 \
  -m 4G \
  -smp 2 \
  -drive file=${VM_IMAGE},format=qcow2 \
  -netdev tap,id=net0,ifname=tap9,script=no,downscript=no \
  -device virtio-net-pci,netdev=net0,mac=${VM_MAC} \
  -vnc ${VNC_PORT} \
  -daemonize

echo "[+] Step 6: Querying bridge ARP tables until target claims ${TARGET_IP}..."
echo "[*] (Awaiting kernel initialization handshake. Monitoring..."
echo "------------------------------------------------------------"

SUCCESS_IP=""
# Polling matrix loop running a 60-second limit check (20 loops x 3 seconds)
for i in {1..20}; do
  sleep 3
  # Use arp-scan localized to the bridge descriptor to isolate virtual targets from AWS networks
  if arp-scan --interface=br0 ${SUBNET_CIDR} 2>/dev/null | grep -q "${TARGET_IP}"; then
    SUCCESS_IP="${TARGET_IP}"
    echo -e "\n[+++] RUNTIME SUCCESS: Target VM actively attached and verified at: $SUCCESS_IP"
    break
  fi
  echo -n "."
done

if [ -z "$SUCCESS_IP" ]; then
  echo -e "\n[-] Connection Timeout: The target failed to claim the IP assignment."
  echo "[*] Diagnostic Advice: Inspect the display via VNC at 127.0.0.1:5902 to trace internal boot panics."
else
  echo "[+] Step 7: Launching tailored Nmap exploitation scan against verified IP..."
  echo "------------------------------------------------------------"
  # -e br0 is critical: forces the scanner to bind directly onto the raw interface, preventing AWS route confusion
  nmap -e br0 -Pn -sC -sV -p- ${SUCCESS_IP}
fi
