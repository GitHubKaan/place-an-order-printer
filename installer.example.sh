@ -0,0 +1,349 @@
#!/bin/bash
# =============================================================================
# Raspberry Pi Zero Printer installer script
# =============================================================================
# USAGE:
#   1. Copy this script to the Pi:
#        scp setup-rpi-printer.sh [INITIAL_USERNAME]@<IP>:/home/[INITIAL_USERNAME]/
#   2. SSH in and run:
#        chmod +x setup-rpi-printer.sh && sudo bash setup-rpi-printer.sh
#
# The script must be run as root (sudo).
# Set ROOT_PASSWORD in the config block before running.
# =============================================================================

set -e  # Exit immediately on error

# ── General Config ────────────────────────────────────────────────────────────
NEW_USER="rpi-pao-printer"
OLD_USER="pi" # When creating a partition, use "pi" as the username
ROOT_PASSWORD="" # When creating a partition, enter the root password here
SSH_PORT="22" # changing is not nessesary; but if changed be sure to reconnect to the server during installation
TIMEZONE="Europe/Berlin"
APP_DIR="/home/${NEW_USER}/place-an-order-printer"
EPSON_VENDOR="04b8"
EPSON_PRODUCT="0e28"
GITHUB_REPO="https://github.com/GitHubKaan/place-an-order-printer"
# ─────────────────────────────────────────────────────────────────────────────

# ── Environment Config (.env.prod) ────────────────────────────────────────────
ENV_NAME="PROD"
ENV_VERSION="1"

ENV_API_VERSION="1"
ENV_API_HTTPS="false"
ENV_API_WWW="false"
ENV_API_HOST="localhost"
ENV_API_PORT="4000"
ENV_API_PATH="api"

ENV_WEBSOCKET_PATH="ws"
ENV_WEBSOCKET_RECONNECT_TIME="5"

ENV_DEVICE_TOKEN=""
# ─────────────────────────────────────────────────────────────────────────────

# Colour helpers
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()    { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
section() { echo -e "\n${GREEN}━━━ $* ━━━${NC}"; }

if [ "$(id -u)" -ne 0 ]; then
  echo -e "${RED}[ERROR]${NC} Run this script with sudo: sudo bash $0"
  exit 1
fi

# =============================================================================
section "1 - Update & Upgrade"
# =============================================================================
info "apt-get update..."
apt-get update -y

info "apt-get upgrade..."
apt-get upgrade -y

info "Installing unattended-upgrades..."
apt-get install -y unattended-upgrades

# Enable automatic security upgrades non-interactively
echo "unattended-upgrades unattended-upgrades/enable_auto_updates boolean true" \
  | debconf-set-selections
dpkg-reconfigure --priority=low --frontend=noninteractive unattended-upgrades

# =============================================================================
section "2 - Change root password"
# =============================================================================
if [ -z "${ROOT_PASSWORD}" ] || [ "${ROOT_PASSWORD}" = "change-me-now" ]; then
  echo -e "${RED}[ERROR]${NC} ROOT_PASSWORD is not set or still default. Edit the config block first."
  exit 1
fi
echo "root:${ROOT_PASSWORD}" | chpasswd
info "Root password updated."

# =============================================================================
section "3 - Create new user: ${NEW_USER}"
# =============================================================================
if id "${NEW_USER}" &>/dev/null; then
  warn "User ${NEW_USER} already exists — skipping creation."
else
  adduser "${NEW_USER}"
  usermod -aG sudo "${NEW_USER}"
  info "User ${NEW_USER} created and added to sudo group."
fi

# =============================================================================
section "4 - Harden SSH"
# =============================================================================
SSHD="/etc/ssh/sshd_config"

# Backup original config
cp "${SSHD}" "${SSHD}.bak.$(date +%Y%m%d%H%M%S)"

# Disable root login
sed -i "s/^#\?PermitRootLogin .*/PermitRootLogin no/" "${SSHD}"
grep -q "^PermitRootLogin" "${SSHD}" || echo "PermitRootLogin no" >> "${SSHD}"

# Password authentication (keep enabled until key-based auth is confirmed)
sed -i "s/^#\?PasswordAuthentication .*/PasswordAuthentication yes/" "${SSHD}"
grep -q "^PasswordAuthentication" "${SSHD}" || echo "PasswordAuthentication yes" >> "${SSHD}"

# SSH keep-alive: send a keep-alive every 60 s, allow 3 missed → auto-disconnect after 3 min idle
sed -i '/^ClientAliveInterval/d' "${SSHD}"
sed -i '/^ClientAliveCountMax/d' "${SSHD}"
echo "ClientAliveInterval 60"  >> "${SSHD}"
echo "ClientAliveCountMax 3"   >> "${SSHD}"

# Per-user block for new user
if ! grep -q "Match User ${NEW_USER}" "${SSHD}"; then
cat >> "${SSHD}" <<EOF

Match User ${NEW_USER}
    AllowTcpForwarding yes
    X11Forwarding no
    PermitTTY yes
EOF
fi

info "SSH config updated. Restarting sshd..."
systemctl restart ssh || systemctl restart sshd

# =============================================================================
section "5 - Firewall (UFW)"
# =============================================================================
apt-get install -y ufw

ufw allow "${SSH_PORT}/tcp" comment "SSH"
ufw default deny incoming
ufw default allow outgoing
ufw --force enable

info "UFW status:"
ufw status

# =============================================================================
section "6 - Fail2Ban (with SSH port)"
# =============================================================================
apt-get install -y fail2ban

cat > /etc/fail2ban/jail.local <<EOF
[DEFAULT]
bantime  = 1h
findtime = 10m
maxretry = 5

[sshd]
enabled  = true
port     = ${SSH_PORT}
logpath  = %(sshd_log)s
backend  = %(sshd_backend)s
EOF

systemctl enable --now fail2ban
info "Fail2Ban status: $(systemctl is-active fail2ban)"

# =============================================================================
section "7 - Timezone"
# =============================================================================
timedatectl set-timezone "${TIMEZONE}"
info "Timezone set to $(timedatectl | grep 'Time zone')"

# =============================================================================
section "8 - Python, Git & Printer Dependencies"
# =============================================================================
apt-get install -y git screen python3-pip libusb-1.0-0 \
  build-essential python3-dev libjpeg-dev zlib1g-dev libopenjp2-7-dev libtiff5-dev libfreetype6-dev liblcms2-dev libwebp-dev libusb-1.0-0-dev

pip3 install escpos --break-system-packages

# Add new user to printer group
usermod -aG lp "${NEW_USER}"

# Epson USB udev rule
echo "SUBSYSTEM==\"usb\", ATTRS{idVendor}==\"${EPSON_VENDOR}\", ATTRS{idProduct}==\"${EPSON_PRODUCT}\", MODE=\"0666\"" \
  | tee /etc/udev/rules.d/99-epson.rules

udevadm control --reload-rules
udevadm trigger

info "Python packages, Git and USB rules configured."

# =============================================================================
section "9 - Clone repository from GitHub"
# =============================================================================
# Ensure parent directory exists with correct ownership
mkdir -p "$(dirname "${APP_DIR}")"
chown "${NEW_USER}:${NEW_USER}" "$(dirname "${APP_DIR}")"

if [ -d "${APP_DIR}/.git" ]; then
  info "Repository already exists — pulling latest changes..."
  sudo -u "${NEW_USER}" git -C "${APP_DIR}" pull
else
  info "Cloning ${GITHUB_REPO} into ${APP_DIR}..."
  sudo -u "${NEW_USER}" git clone "${GITHUB_REPO}" "${APP_DIR}"
fi

chown -R "${NEW_USER}:${NEW_USER}" "${APP_DIR}"
info "Repository ready at ${APP_DIR}"

# Install the auto-update helper script and Git post-merge hook
HOOK_FILE="${APP_DIR}/.git/hooks/post-merge"
cat > "${HOOK_FILE}" <<EOF
#!/usr/bin/env bash
/usr/bin/bash "${APP_DIR}/scripts/update-repo.sh"
EOF
chmod +x "${HOOK_FILE}"
chmod +x "${APP_DIR}/scripts/update-repo.sh"
info "Git post-merge hook installed."

# =============================================================================
section "10 - Create .env.prod"
# =============================================================================
ENV_FILE="${APP_DIR}/.env.prod"

cat > "${ENV_FILE}" <<EOF
# GENERAL
# Choose between DEV or PROD (.env.dev = DEV; .env.prod = PROD)
ENV=${ENV_NAME}
VERSION=${ENV_VERSION}
# API
API_VERSION=${ENV_API_VERSION}
API_HTTPS=${ENV_API_HTTPS}
# Enable www. subdomain
API_WWW=${ENV_API_WWW}
# Only the domain name (do not add protocol!)
API_HOST=${ENV_API_HOST}
# Optional
API_PORT=${ENV_API_PORT}
# Optional (do not add slashes to the front or back)
API_PATH=${ENV_API_PATH}
# WEBSOCKET
# Optional (do not add slashes to the front or back)
WEBSOCKET_PATH=${ENV_WEBSOCKET_PATH}
# WebSocket timeout until reconnect attempt (in seconds)
WEBSOCKET_RECONNECT_TIME=${ENV_WEBSOCKET_RECONNECT_TIME}
# AUTHORIZATION
DEVICE_TOKEN=${ENV_DEVICE_TOKEN}
EOF

chown "${NEW_USER}:${NEW_USER}" "${ENV_FILE}"
chmod 600 "${ENV_FILE}"   # Readable only by owner (token is sensitive)
info ".env.prod created at ${ENV_FILE}"

# =============================================================================
section "11 - Install Python requirements"
# =============================================================================
if [ -f "${APP_DIR}/requirements.txt" ]; then
  info "requirements.txt found — installing dependencies..."
  sudo -u "${NEW_USER}" pip3 install --break-system-packages -r "${APP_DIR}/requirements.txt"
  info "Dependencies installed."
else
  warn "requirements.txt not found in ${APP_DIR} — please install manually."
fi

# =============================================================================
section "12 - Systemd print service"
# =============================================================================
cat > /etc/systemd/system/printservice.service <<EOF
[Unit]
Description=Print Service in Screen
After=network.target

[Service]
Type=forking
User=${NEW_USER}
WorkingDirectory=${APP_DIR}
ExecStart=/usr/bin/screen -dmS printservice bash -c 'make prod'
ExecStop=/usr/bin/screen -S printservice -X quit
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable printservice
info "Systemd service registered."

# =============================================================================
section "14 - Create automatic update timer"
# =============================================================================
cat > /etc/systemd/system/printservice-update.service <<EOF
[Unit]
Description=Update Place An Order printer repository and restart printservice
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/bin/bash "${APP_DIR}/scripts/update-repo.sh"

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/printservice-update.timer <<EOF
[Unit]
Description=Run printservice repository update every 15 minutes

[Timer]
OnBootSec=5min
OnUnitActiveSec=15min
Persistent=true
Unit=printservice-update.service

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable printservice-update.timer
systemctl start printservice-update.timer
info "Automatic update timer registered."

# =============================================================================
section "13 - Remove old default user (${OLD_USER})"
# =============================================================================
warn "──────────────────────────────────────────────────────────────"
warn "The old user '${OLD_USER}' has NOT been deleted automatically."
warn "Before deleting:"
warn "  1. Log OUT of this session"
warn "  2. Log IN as ${NEW_USER} on port ${SSH_PORT}"
warn "  3. Verify sudo works: sudo whoami"
warn "  4. Then run: sudo userdel -r -f ${OLD_USER}"
warn "──────────────────────────────────────────────────────────────"

# =============================================================================
section "Setup complete!"
# =============================================================================
echo ""
echo -e "${GREEN}All steps finished. Next steps:${NC}"
echo "  1. Verify printer detected:  lsusb"
echo "  2. Start service:            sudo systemctl start printservice"
echo "  3. Check service status:     sudo systemctl status printservice"
echo "  4. Follow screen session:    sudo -u ${NEW_USER} screen -r printservice"
echo "  5. Delete old user (see warning above)"
echo ""
echo -e "${YELLOW}Remember to reboot for all changes to take effect:${NC}"
echo "     sudo shutdown -r now"
echo ""