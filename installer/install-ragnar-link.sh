#!/usr/bin/env bash
set -euo pipefail

APP_USER="${APP_USER:-ragnar-link}"
APP_DIR="${APP_DIR:-/opt/ragnar-link}"
CONFIG_DIR="${CONFIG_DIR:-/etc/ragnar-link}"
STATE_DIR="${STATE_DIR:-/run/ragnar-link}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Please run as root: sudo installer/install-ragnar-link.sh" >&2
  exit 1
fi

install -d -m 0755 "${APP_DIR}" "${CONFIG_DIR}"
find "${APP_DIR}" -mindepth 1 \
  ! -path "${APP_DIR}/host/.venv" \
  ! -path "${APP_DIR}/host/.venv/*" \
  -exec rm -rf {} +
cp -a "${REPO_ROOT}/." "${APP_DIR}/"
rm -rf "${APP_DIR}/.git" "${APP_DIR}/host/.venv" "${APP_DIR}/firmware/ragnar_espnow_gateway/.pio"

if ! id "${APP_USER}" >/dev/null 2>&1; then
  USERADD_GROUPS=()
  if getent group dialout >/dev/null 2>&1; then
    USERADD_GROUPS=(--groups dialout)
  fi
  useradd --system --home-dir "${APP_DIR}" --shell /usr/sbin/nologin "${USERADD_GROUPS[@]}" "${APP_USER}"
elif getent group dialout >/dev/null 2>&1; then
  usermod -a -G dialout "${APP_USER}"
fi

python3 -m venv "${APP_DIR}/host/.venv"
"${APP_DIR}/host/.venv/bin/pip" install "${APP_DIR}/host"

if [[ ! -f "${CONFIG_DIR}/config.yaml" ]]; then
  install -m 0644 "${APP_DIR}/installer/ragnar-link.config.yaml" "${CONFIG_DIR}/config.yaml"
fi

install -m 0644 "${APP_DIR}/systemd/ragnar-link.service" /etc/systemd/system/ragnar-link.service
install -d -m 0755 -o "${APP_USER}" -g "${APP_USER}" "${STATE_DIR}"

systemctl daemon-reload
systemctl enable ragnar-link.service
systemctl restart ragnar-link.service

echo "Ragnar Link installed."
echo "Edit ${CONFIG_DIR}/config.yaml if the USB serial path or ESP-NOW channel needs changing."
echo "Check logs with: journalctl -u ragnar-link -f"
