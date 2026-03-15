#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/mnt/config/opstools/discovery-tool"
cd "$PROJECT_DIR"

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo ".env created from template. Fill in secrets before starting the service."
fi

echo "Install finished. Next:"
echo "  sudo cp deploy/systemd/discovery-tool.service /etc/systemd/system/"
echo "  sudo systemctl daemon-reload"
echo "  sudo systemctl enable --now discovery-tool.service"
