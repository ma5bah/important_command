#!/bin/bash
set -euo pipefail

# =======================
# Complete Screen Sharing Setup Script
# Auto-detects session type and installs/configures everything
# =======================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

log() { echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_info() { echo -e "${CYAN}ℹ️  $1${NC}"; }

error_exit() {
    log_error "$1"
    exit 1
}

echo ""
echo -e "${CYAN}╔════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║    Complete Screen Sharing Setup       ║${NC}"
echo -e "${CYAN}║    Auto-detects and configures VNC     ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════╝${NC}"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    error_exit "Don't run as root. Run as your regular user."
fi

# Detect session type
SESSION_TYPE="${XDG_SESSION_TYPE:-unknown}"
DESKTOP="${XDG_CURRENT_DESKTOP:-unknown}"

log "Step 1/9: Detecting system..."
echo "  Session Type: $SESSION_TYPE"
echo "  Desktop: $DESKTOP"
echo "  Display: ${DISPLAY:-not set}"
echo ""

# Check if we're in SSH or local terminal
if [ -n "${SSH_CLIENT:-}" ] || [ -n "${SSH_TTY:-}" ]; then
    log_warning "Running via SSH - setting DISPLAY=:0"
    export DISPLAY=:0
fi

# Get IP address
IP=$(hostname -I 2>/dev/null | awk '{print $1}')
if [ -z "$IP" ]; then
    IP=$(hostname -i 2>/dev/null | awk '{print $1}')
fi

# Decide which method to use
USE_VINO=false
USE_X11VNC=false

if [[ "$DESKTOP" == *"GNOME"* ]] || [[ "$SESSION_TYPE" == "wayland" ]]; then
    log_info "GNOME/Wayland detected - using vino (GNOME Screen Sharing)"
    USE_VINO=true
elif [[ "$SESSION_TYPE" == "x11" ]] || ps aux | grep -E "[X]org" >/dev/null 2>&1; then
    log_info "X11 detected - using x11vnc"
    USE_X11VNC=true
else
    log_warning "Cannot determine session type clearly"
    echo ""
    echo "Choose method:"
    echo "1) vino (GNOME built-in, works with Wayland)"
    echo "2) x11vnc (Traditional, X11 only)"
    echo ""
    read -p "Choice [1-2]: " method_choice
    
    if [ "$method_choice" = "1" ]; then
        USE_VINO=true
    else
        USE_X11VNC=true
    fi
fi

# ======================
# VINO SETUP (GNOME)
# ======================
if [ "$USE_VINO" = true ]; then
    log "Step 2/9: Installing vino..."
    
    if ! command -v vino-server >/dev/null 2>&1; then
        sudo apt update -y
        sudo apt install -y vino dconf-cli
        log_success "vino installed"
    else
        log_success "vino already installed"
    fi
    
    log "Step 3/9: Stopping existing screen sharing..."
    pkill -9 vino-server 2>/dev/null || true
    sleep 1
    
    log "Step 4/9: Configuring vino..."

    # Ensure dconf schema is updated
    if [ -d "/usr/share/glib-2.0/schemas" ]; then
        log_info "Updating dconf schemas..."
        sudo glib-compile-schemas /usr/share/glib-2.0/schemas/
    fi
    
    # Enable screen sharing
    dconf write /org/gnome/desktop/remote-access/enabled true
    dconf write /org/gnome/desktop/remote-access/prompt-enabled false
    dconf write /org/gnome/desktop/remote-access/require-encryption false
    dconf write /org/gnome/desktop/remote-access/view-only false
    
    log_success "Basic configuration done"
    
    log "Step 5/9: Setting password..."
    echo ""
    read -sp "Enter VNC password: " VNC_PASSWORD
    echo ""
    read -sp "Verify password: " VNC_PASSWORD_VERIFY
    echo ""
    
    if [ "$VNC_PASSWORD" != "$VNC_PASSWORD_VERIFY" ]; then
        error_exit "Passwords don't match"
    fi
    
    # Encode password
    SECRET=$(echo -n "$VNC_PASSWORD" | base64)
    dconf write /org/gnome/desktop/remote-access/authentication-methods "['vnc']"
    dconf write /org/gnome/desktop/remote-access/vnc-password "'$SECRET'"
    
    log_success "Password configured"
    
    log "Step 6/9: Starting vino server..."
    
    # Force vino to use a specific resolution by modifying display settings
    log "Step 6.1: Forcing Vino to use 3024x1964 resolution..."
    dconf write /org/gnome/desktop/remote-access/screen-size '(uint32 3024, uint32 1964)'
    
    # Start vino
    /usr/lib/vino/vino-server >/dev/null 2>&1 &
    sleep 3
    
    log "Step 7/9: Verifying vino is running..."
    if pgrep -u "$USER" vino-server >/dev/null 2>&1; then
        log_success "vino-server is running!"
    else
        log_error "vino-server failed to start"
        log_info "Trying alternative start method..."
        
        # Try with dbus
        dbus-launch /usr/lib/vino/vino-server >/dev/null 2>&1 &
        sleep 3
        
        if pgrep -u "$USER" vino-server >/dev/null 2>&1; then
            log_success "vino-server started with dbus!"
        else
            error_exit "Cannot start vino-server. Check: journalctl -xe"
        fi
    fi

    log "Step 8/9: Configuring UFW firewall..."
    VNC_PORT=5900
    if command -v ufw >/dev/null 2>&1; then
        if sudo ufw status | grep -q 'Status: active'; then
            if ! sudo ufw status | grep -q "ALLOW IN.*$VNC_PORT"; then
                sudo ufw allow $VNC_PORT/tcp
                log_success "UFW rule added for port $VNC_PORT"
            else
                log_success "UFW rule for port $VNC_PORT already exists"
            fi
        else
            log_info "UFW is not active, skipping firewall configuration."
        fi
    else
        log_warning "UFW is not installed, skipping firewall configuration."
    fi
    
    log "Step 9/9: Creating autostart entry..."
    mkdir -p ~/.config/autostart
    cat > ~/.config/autostart/vino-server.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=Vino VNC Server
Exec=/usr/lib/vino/vino-server
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
EOF
    log_success "Autostart configured"
    
    VNC_PORT=5900
    VNC_METHOD="vino (GNOME Screen Sharing)"

# ======================
# X11VNC SETUP
# ======================
elif [ "$USE_X11VNC" = true ]; then
    log "Step 2/9: Installing x11vnc..."
    
    if ! command -v x11vnc >/dev/null 2>&1; then
        sudo apt update -y
        sudo apt install -y x11vnc
        log_success "x11vnc installed"
    else
        log_success "x11vnc already installed"
    fi
    
    log "Step 3/9: Stopping existing x11vnc sessions..."
    pkill -9 x11vnc 2>/dev/null || true
    sleep 1
    
    log "Step 4/9: Setting up password..."
    VNC_DIR="$HOME/.vnc"
    mkdir -p "$VNC_DIR"
    
    if [ ! -f "$VNC_DIR/x11vnc_passwd" ]; then
        echo ""
        x11vnc -storepasswd "$VNC_DIR/x11vnc_passwd"
        log_success "Password saved"
    else
        log_success "Password already exists"
        read -p "Create new password? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            x11vnc -storepasswd "$VNC_DIR/x11vnc_passwd"
        fi
    fi
    
    log "Step 5/9: Finding X authority file..."
    
    # Try multiple methods to find auth file
    XAUTH=""
    
    # Method 1: Parse from Xorg process
    XAUTH=$(ps aux | grep -oP "Xorg.*-auth \K\S+" | head -1)
    
    # Method 2: Check common locations
    if [ -z "$XAUTH" ] || [ ! -f "$XAUTH" ]; then
        for auth_file in "$HOME/.Xauthority" "/var/run/lightdm/$USER/xauthority" "/run/user/$(id -u)/gdm/Xauthority"; do
            if [ -f "$auth_file" ]; then
                XAUTH="$auth_file"
                break
            fi
        done
    fi
    
    # Method 3: Find in /run
    if [ -z "$XAUTH" ] || [ ! -f "$XAUTH" ]; then
        XAUTH=$(find /run/user/$(id -u) -name "Xauthority" 2>/dev/null | head -1)
    fi
    
    if [ -n "$XAUTH" ] && [ -f "$XAUTH" ]; then
        log_success "Found X authority: $XAUTH"
        export XAUTHORITY="$XAUTH"
    else
        log_warning "X authority not found, will try without it"
        XAUTH="guess"
    fi
    
    log "Step 6/9: Starting x11vnc..."
    
    # Ensure DISPLAY is set
    if [ -z "${DISPLAY:-}" ]; then
        export DISPLAY=:0
    fi
    
    # Get the resolution of the physical display
    
    GEOMETRY="3024x1964"  # Example for MacBook Pro 16-inch Retina
    VNC_PORT=5900
    
    # Start x11vnc with proper options
    if [ "$XAUTH" = "guess" ]; then
        x11vnc \
            -display "$DISPLAY" \
            -auth guess \
            -forever \
            -rfbauth "$VNC_DIR/x11vnc_passwd" \
            -rfbport $VNC_PORT \
            -shared \
            -clip $GEOMETRY \
            -encodings "tight" \
            -noxdamage \
            -repeat \
            -nowf \
            -nopw \
            -o "$VNC_DIR/x11vnc.log" &
    else
        x11vnc \
            -display "$DISPLAY" \
            -auth "$XAUTH" \
            -forever \
            -rfbauth "$VNC_DIR/x11vnc_passwd" \
            -rfbport $VNC_PORT \
            -shared \
            -clip $GEOMETRY \
            -encodings "tight" \
            -noxdamage \
            -repeat \
            -nowf \
            -nopw \
            -o "$VNC_DIR/x11vnc.log" &
    fi
    
    X11VNC_PID=$!
    sleep 3
    
    log "Step 7/9: Verifying x11vnc is running..."
    if pgrep -u "$USER" x11vnc >/dev/null 2>&1; then
        log_success "x11vnc is running!"
    else
        log_error "x11vnc failed to start"
        log_info "Checking log file..."
        if [ -f "$VNC_DIR/x11vnc.log" ]; then
            echo ""
            tail -20 "$VNC_DIR/x11vnc.log"
            echo ""
        fi
        error_exit "x11vnc startup failed"
    fi
    
    log "Step 8/9: Configuring UFW firewall..."
    if command -v ufw >/dev/null 2>&1; then
        if sudo ufw status | grep -q 'Status: active'; then
            if ! sudo ufw status | grep -q "ALLOW IN.*$VNC_PORT"; then
                sudo ufw allow $VNC_PORT/tcp
                log_success "UFW rule added for port $VNC_PORT"
            else
                log_success "UFW rule for port $VNC_PORT already exists"
            fi
        else
            log_info "UFW is not active, skipping firewall configuration."
        fi
    else
        log_warning "UFW is not installed, skipping firewall configuration."
    fi

    log "Step 9/9: Creating systemd user service..."
    
    mkdir -p ~/.config/systemd/user
    cat > ~/.config/systemd/user/x11vnc.service << EOF
[Unit]
Description=x11vnc Screen Sharing
After=graphical.target

[Service]
Type=simple
Environment=DISPLAY=:0
Environment=XAUTHORITY=$XAUTH
ExecStart=/usr/bin/x11vnc -display :0 -auth $XAUTH -forever -rfbauth $VNC_DIR/x11vnc_passwd -rfbport $VNC_PORT -shared -encodings "tight" -noxdamage -repeat -nowf -nopw -clip $GEOMETRY
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOF
    
    systemctl --user daemon-reload
    systemctl --user enable x11vnc.service
    log_success "Autostart configured"
    
    VNC_PORT=5900
    VNC_METHOD="x11vnc"
fi

# ======================
# FINAL STATUS
# ======================
echo ""
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ SCREEN SHARING IS ACTIVE!          ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}📺 Configuration:${NC}"
echo "    Method:       $VNC_METHOD"
echo "    Display:      ${DISPLAY:-:0}"
echo "    Port:         $VNC_PORT"
echo ""
echo -e "${CYAN}🔌 Connection Details:${NC}"
echo "    IP Address:   $IP"
echo "    Port:         $VNC_PORT"
echo ""
echo -e "${CYAN}📱 Connect from VNC Client:${NC}"
echo "    ${IP}:${VNC_PORT}"
echo "    or simply: ${IP}"
echo ""
echo -e "${CYAN}🔍 Current Status:${NC}"
if [ "$USE_VINO" = true ]; then
    pgrep -a vino-server || echo "    Warning: vino-server not detected"
else
    pgrep -a x11vnc || echo "    Warning: x11vnc not detected"
fi
echo ""
echo -e "${CYAN}🛠️  Management Commands:${NC}"
if [ "$USE_VINO" = true ]; then
    echo "    Stop:         pkill vino-server"
    echo "    Start:        /usr/lib/vino/vino-server &"
    echo "    Status:       pgrep -a vino-server"
    echo "    Logs:         journalctl --user -u vino-server"
    echo "    NOTE: Vino's resolution is fixed at 3024x1964."
else
    echo "    Stop:         pkill x11vnc"
    echo "    Start:        systemctl --user start x11vnc"
    echo "    Status:       systemctl --user status x11vnc"
    echo "    Logs:         tail -f ~/.vnc/x11vnc.log"
    echo "    NOTE: x11vnc's resolution is fixed at 3024x1964."
fi
echo ""
echo -e "${CYAN}💡 Important Notes:${NC}"
echo "    • You'll see your ACTUAL laptop screen"
echo "    • Changes are reflected on both screens"
echo "    • Server auto-starts on boot"
echo "    • Multiple clients can connect"
echo ""
echo -e "${CYAN}🔒 Security:${NC}"
echo "    • Password protected"
echo "    • Accessible from LAN: $IP"
echo "    • For SSH tunnel: ssh -L 5900:localhost:5900 user@$IP"
echo ""
log_success "Setup complete! Connect now from your VNC client."
echo ""