#!/usr/bin/env bash
# =============================================================================
#  gerar_certs.sh — gera uma CA e um certificado de servidor de TESTE para
#  habilitar o listener TLS 8883 do Mosquitto no docker-compose.
#
#  Projeto: Monitoramento de Qualidade do Ar - Atividade 3
#
#  Uso:
#    ./gerar_certs.sh                 # CN = localhost
#    ./gerar_certs.sh meu.host.local  # CN customizado
#
#  Depois, descomente o bloco do listener 8883 em mosquitto/config/mosquitto.conf
#  (cafile/certfile/keyfile apontam para mosquitto/config/certs/) e recrie o
#  container: docker compose up -d --force-recreate mosquitto
#
#  ATENCAO: esta e uma CA de TESTE, para desenvolvimento. Em producao use uma
#  autoridade real e, idealmente, certificado por dispositivo (mTLS), como no
#  plano de AWS IoT Core (infra/aws/planejamento_servicos.md).
# =============================================================================

set -euo pipefail

CN="${1:-localhost}"
DIR="$(cd "$(dirname "$0")" && pwd)/mosquitto/config/certs"
DIAS=825

mkdir -p "$DIR"

if [[ -f "$DIR/server.crt" ]]; then
  echo "[i] Certificados ja existem em $DIR (remova-os para regenerar). Nada a fazer."
  exit 0
fi

echo "[+] Gerando CA de teste..."
openssl req -new -x509 -days "$DIAS" -nodes \
  -subj "/CN=QAR-Broker-CA" \
  -keyout "$DIR/ca.key" -out "$DIR/ca.crt"

echo "[+] Gerando chave e CSR do servidor (CN=$CN)..."
openssl req -new -nodes \
  -subj "/CN=$CN" \
  -keyout "$DIR/server.key" -out "$DIR/server.csr"

echo "[+] Assinando o certificado do servidor com a CA..."
openssl x509 -req -in "$DIR/server.csr" -days "$DIAS" \
  -CA "$DIR/ca.crt" -CAkey "$DIR/ca.key" -CAcreateserial \
  -out "$DIR/server.crt"

rm -f "$DIR/server.csr"

echo
echo "[ok] Certificados gerados em: $DIR"
echo "     ca.crt / server.crt / server.key"
echo
echo "Proximos passos:"
echo "  1. Descomente o listener 8883 em mosquitto/config/mosquitto.conf."
echo "  2. docker compose up -d --force-recreate mosquitto"
echo "  3. Teste: mosquitto_sub -h localhost -p 8883 --cafile \"$DIR/ca.crt\" -t 'qualidade-ar/#'"
echo "  4. No gerador: python ../../poc/ingestao_teste.py --host localhost --porta 8883 --tls --tls-inseguro"
