sudo bash -s <<'BASH'
# Add your public key to root's authorized_keys
mkdir -p /root/.ssh
echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAINB27DT/QgikoPbxuZ4Pu7548dCHtWpRwW24G8gEV3nq masbahuddin60@gmail.com" >> /root/.ssh/authorized_keys
chmod 700 /root/.ssh
chmod 600 /root/.ssh/authorized_keys

# Enable root SSH login in sshd_config
if [ -f /etc/ssh/sshd_config ]; then
  # Backup original
  cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak
  # Enable root login with public key
  sed -i -E 's/^#?PermitRootLogin.*/PermitRootLogin prohibit-password/' /etc/ssh/sshd_config
  # Ensure PubkeyAuthentication is enabled
  sed -i -E 's/^#?PubkeyAuthentication.*/PubkeyAuthentication yes/' /etc/ssh/sshd_config
  # Restart SSH service
  systemctl restart sshd 2>/dev/null || systemctl restart ssh 2>/dev/null || service sshd restart 2>/dev/null || service ssh restart 2>/dev/null
fi

# Get connection details with better defaults
PUB=$(curl -fsS --max-time 5 https://ifconfig.co || curl -fsS --max-time 5 https://icanhazip.com || echo "N/A")
LIP=$(ip -4 addr show scope global 2>/dev/null | awk '/inet/ {print $2; exit}' | cut -d/ -f1)
[ -z "$LIP" ] && LIP=$(hostname -I 2>/dev/null | awk '{print $1}')
[ -z "$LIP" ] && LIP="N/A"

# Better port detection with fallback to 22
PORT=$(ss -tlnp 2>/dev/null | grep -E "sshd|:22" | awk '{print $4}' | grep -oE '[0-9]+$' | head -1)
[ -z "$PORT" ] && PORT=$(grep -E "^[^#]*Port " /etc/ssh/sshd_config 2>/dev/null | awk '{print $2}' | head -1)
[ -z "$PORT" ] && PORT="22"

# Output connection details
printf '\n\033[32m✓ Root SSH access configured!\033[0m\n\n'
printf 'ssh://root@%s:%s\n' "$PUB" "$PORT"
printf 'Public IP: %s\n' "$PUB"
printf 'Local IP: %s\n' "$LIP"
printf 'SSH port: %s\n' "$PORT"
printf 'Username: root\n'
printf 'Auth: SSH key (no password needed)\n\n'
printf '\033[33mConnect with:\033[0m\n'
printf '\033[36mssh root@%s -p %s -i ~/.ssh/htb_temp_user\033[0m\n' "$PUB" "$PORT"
printf '\033[33mor if your key is the default:\033[0m\n'
printf '\033[36mssh root@%s -p %s\033[0m\n\n' "$PUB" "$PORT"
BASH
