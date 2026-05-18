#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE_NAME="printservice"

# Detect the repository owner so git operations are executed with the same user.
REPO_USER="$(stat -c '%U' "$APP_DIR" 2>/dev/null || stat -f '%Su' "$APP_DIR")"

cd "$APP_DIR"

echo "[update] Checking repository for new commits..."

sudo -u "$REPO_USER" git fetch --all --prune

LOCAL_REV="$(sudo -u "$REPO_USER" git rev-parse @)"
REMOTE_REV="$(sudo -u "$REPO_USER" git rev-parse @{u})"
BASE_REV="$(sudo -u "$REPO_USER" git merge-base @ @{u})"

if [ "$LOCAL_REV" = "$REMOTE_REV" ]; then
  echo "[update] Repository is already up-to-date."
  exit 0
fi

if [ "$LOCAL_REV" = "$BASE_REV" ]; then
  echo "[update] New remote commits found. Pulling latest changes..."
  sudo -u "$REPO_USER" git pull --ff-only

  if [ -f "$APP_DIR/requirements.txt" ]; then
    echo "[update] Installing updated Python dependencies..."
    python3 -m pip install --break-system-packages -r "$APP_DIR/requirements.txt"
  fi

  echo "[update] Restarting ${SERVICE_NAME}..."
  systemctl restart "$SERVICE_NAME"
  echo "[update] Update complete."
  exit 0
fi

echo "[update] Local branch has diverged from remote. Manual intervention is required."
exit 1
