#!/usr/bin/env sh
set -eu

PROJECT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$PROJECT_ROOT"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker não encontrado. Instale e inicie Docker Engine/Desktop." >&2
  exit 1
fi

if docker compose version >/dev/null 2>&1; then
  compose() { docker compose "$@"; }
  compose_label="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
  compose() { docker-compose "$@"; }
  compose_label="docker-compose"
else
  echo "Docker Compose v2 não encontrado." >&2
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "O daemon do Docker não está acessível." >&2
  exit 1
fi

if [ ! -f .env ]; then
  cp .env.example .env
  echo "[config] .env criado com acesso restrito ao computador local."
fi

compose config --quiet
compose up -d --build

ready=0
i=1
while [ "$i" -le 60 ]; do
  code="fetch('http://127.0.0.1:3001/api/health').then(r=>r.json()).then(j=>{if(!j.ok||!j.mqtt_connected||j.devices<1)process.exit(2)}).catch(()=>process.exit(3))"
  if compose exec -T backend node -e "$code" >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 2
  i=$((i + 1))
done

if [ "$ready" -ne 1 ]; then
  echo "O stack não ficou pronto no prazo." >&2
  compose ps || true
  compose logs --tail 80 backend demo || true
  exit 1
fi

port=$(awk -F= '/^DASHBOARD_PORT=/{print $2; exit}' .env)
port=${port:-3001}
printf '\nInstalação concluída.\nDashboard: http://localhost:%s\n' "$port"
echo "Parar:     $compose_label down"
echo "Logs:      $compose_label logs -f backend demo"
