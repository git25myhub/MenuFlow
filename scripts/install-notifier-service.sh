#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME=bluespace-notifier.service
SERVICE_PATH=/etc/systemd/system/${SERVICE_NAME}

if [[ $EUID -ne 0 ]]; then
  echo "This script must be run as root (use: sudo $0)" >&2
  exit 1
fi

WORKDIR="$(cd "$(dirname "$0")"/.. && pwd)"
SDL_DRIVER="${SDL_DRIVER:-x11}"
# Create a stable, space-free symlink for systemd to avoid ExecStart path issues
LINK_DIR="/opt/bluespace"
mkdir -p /opt || true
ln -sTf "${WORKDIR}" "${LINK_DIR}"

# Prefer venv python via the symlinked path
VENV_PY_LINK="${LINK_DIR}/venv/bin/python3"
if [[ -x "${VENV_PY_LINK}" ]]; then
  PYTHON_BIN="${VENV_PY_LINK}"
else
  PYTHON_BIN="/usr/bin/python3"
fi

cat >"${SERVICE_PATH}" <<'UNIT'
[Unit]
Description=BlueSpace Restaurants - Hardware Notifier (Kitchen Display)
After=network-online.target graphical.target
Wants=network-online.target graphical.target

[Service]
Type=simple
WorkingDirectory=REPLACE_WORKDIR
Environment=PYTHONUNBUFFERED=1
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/REPLACE_USER/.Xauthority
Environment=XDG_RUNTIME_DIR=/run/user/REPLACE_UID
Environment=SDL_VIDEODRIVER=REPLACE_SDL_DRIVER
Environment=PYTHONPATH=REPLACE_WORKDIR
Environment=SIMULATION_MODE=false
ExecStart=REPLACE_PY_BIN run_hardware_notifier.py
Restart=always
RestartSec=3
User=REPLACE_USER
Group=REPLACE_USER

[Install]
WantedBy=multi-user.target
UNIT

# Use the symlinked path for WorkingDirectory and PYTHONPATH
sed -i "s|REPLACE_WORKDIR|${LINK_DIR}|g" "${SERVICE_PATH}"
DEFAULT_USER=$(logname 2>/dev/null || echo pi)
sed -i "s|REPLACE_USER|${DEFAULT_USER}|g" "${SERVICE_PATH}"
DEFAULT_UID=$(id -u "${DEFAULT_USER}")
sed -i "s|REPLACE_UID|${DEFAULT_UID}|g" "${SERVICE_PATH}"
sed -i "s|REPLACE_SDL_DRIVER|${SDL_DRIVER}|g" "${SERVICE_PATH}"
sed -i "s|REPLACE_PY_BIN|${PYTHON_BIN}|g" "${SERVICE_PATH}"

# Disable any legacy services to avoid conflicts
LEGACY1="/etc/systemd/system/bluespace-hardware-notifier.service"
LEGACY2="/etc/systemd/system/bluespace-hardware-notifier-simple.service"
if systemctl list-unit-files | grep -q '^bluespace-hardware-notifier\.service'; then
  systemctl disable --now bluespace-hardware-notifier.service || true
fi
if systemctl list-unit-files | grep -q '^bluespace-hardware-notifier-simple\.service'; then
  systemctl disable --now bluespace-hardware-notifier-simple.service || true
fi
[ -f "$LEGACY1" ] && rm -f "$LEGACY1"
[ -f "$LEGACY2" ] && rm -f "$LEGACY2"

systemctl daemon-reload
systemctl enable "${SERVICE_NAME}"
systemctl restart "${SERVICE_NAME}"

echo "Installed and started ${SERVICE_NAME}. Check status with: sudo systemctl status ${SERVICE_NAME}"


