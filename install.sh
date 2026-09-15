#!/usr/bin/env bash
# install.sh — one-time setup for the Chaos artifact: Python/Node dependencies,
# /etc/hosts entry for testserver.com, self-signed TLS cert for the server
# component, and a starter .env file.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

echo "== Chaos artifact setup =="

# 1. uv (Python package/venv manager)
if ! command -v uv >/dev/null 2>&1; then
  echo "-- Installing uv..."
  curl -Lsf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
else
  echo "-- uv already installed"
fi

# 2. Python dependencies (single shared venv for all components)
echo "-- Installing Python dependencies (uv sync)..."
uv sync

# 3. Node dependencies (crawler + static-analysis JS helpers)
if ! command -v npm >/dev/null 2>&1; then
  echo "!! npm not found. Install Node.js (https://nodejs.org) and re-run this script." >&2
  exit 1
fi
echo "-- Installing Node.js dependencies (npm install)..."
npm install

# 4. .env file — every component loads ~/chaos/.env specifically (a fixed
# path, not relative to this repo's actual clone location), so it must be
# created there regardless of where this repo lives on disk.
ENV_TARGET="$HOME/chaos/.env"
if [ ! -f "$ENV_TARGET" ]; then
  echo "-- Creating $ENV_TARGET from .env.example (edit DB_USER/DB_PASS before running the pipeline)"
  mkdir -p "$(dirname "$ENV_TARGET")"
  cp .env.example "$ENV_TARGET"
else
  echo "-- $ENV_TARGET already exists, leaving it untouched"
fi

# 5. /etc/hosts entry for testserver.com
if ! grep -qE "^\s*127\.0\.0\.1\s+testserver\.com\s*$" /etc/hosts 2>/dev/null; then
  echo
  echo "-- testserver.com is not in /etc/hosts. The crawler and server communicate via this hostname."
  read -r -p "   Add '127.0.0.1  testserver.com' to /etc/hosts now? (requires sudo) [y/N] " ans
  if [[ "$ans" =~ ^[Yy]$ ]]; then
    echo "127.0.0.1  testserver.com" | sudo tee -a /etc/hosts >/dev/null
  else
    echo "   Skipped. Add it manually before running the crawler/server."
  fi
else
  echo "-- testserver.com already in /etc/hosts"
fi

# 6. Self-signed TLS certificate for the server's nginx container
CERT_DIR="server/cert"
if [ ! -f "$CERT_DIR/localhost.crt" ] || [ ! -f "$CERT_DIR/localhost.key" ]; then
  echo "-- Generating self-signed TLS certificate at $CERT_DIR/"
  mkdir -p "$CERT_DIR"
  openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
    -keyout "$CERT_DIR/localhost.key" \
    -out "$CERT_DIR/localhost.crt" \
    -subj "/CN=localhost"
else
  echo "-- TLS certificate already present at $CERT_DIR/"
fi

echo
echo "== Setup complete =="
echo "Edit $ENV_TARGET with your database credentials, then follow README.md for the"
echo "per-component run instructions (static -> server -> crawler -> analyzer)."
