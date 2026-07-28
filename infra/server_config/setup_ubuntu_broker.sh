#!/usr/bin/env bash
# =============================================================================
#  setup_ubuntu_broker.sh
#  Provisiona um broker Mosquitto endurecido e ajustado para milhares de
#  conexoes, em uma VM Ubuntu (20.04/22.04/24.04).
#
#  Projeto: Monitoramento de Qualidade do Ar - Atividade 3 (UFG - IoT)
#
#  O que o script faz (de forma idempotente - pode rodar novamente sem quebrar):
#    1. Instala o Mosquitto e as ferramentas de cliente.
#    2. Aplica ajuste de kernel/limites para suportar muitas conexoes TCP.
#    3. Instala uma configuracao tunada do broker em /etc/mosquitto/conf.d.
#    4. (Opcional) Cria autenticacao por senha + ACL de menor privilegio.
#    5. (Opcional) Gera uma CA de teste e habilita o listener TLS 8883.
#    6. Habilita e reinicia o servico.
#
#  Uso:
#    sudo ./setup_ubuntu_broker.sh                 # PoC: listener 1883 anonimo
#    sudo ./setup_ubuntu_broker.sh --auth          # exige usuario/senha + ACL
#    sudo ./setup_ubuntu_broker.sh --auth --tls    # tambem habilita TLS 8883
#
#  Variaveis de ambiente uteis:
#    MQTT_USER      usuario a criar quando --auth (padrao: ingestor)
#    MQTT_PASSWORD  senha do usuario (se ausente com --auth, o script pergunta)
#    MAX_FDS        limite de descritores de arquivo (padrao: 200000)
# =============================================================================

set -euo pipefail

# ----------------------------------------------------------------------------
# Constantes e utilidades de log
# ----------------------------------------------------------------------------
readonly CONF_DIR="/etc/mosquitto"
readonly CONF_FILE="${CONF_DIR}/conf.d/qar-broker.conf"
readonly PASSWD_FILE="${CONF_DIR}/passwd"
readonly ACL_FILE="${CONF_DIR}/aclfile"
readonly CERTS_DIR="${CONF_DIR}/certs"
readonly SYSCTL_FILE="/etc/sysctl.d/99-mosquitto-qar.conf"
readonly SYSTEMD_OVERRIDE_DIR="/etc/systemd/system/mosquitto.service.d"
readonly MAX_FDS="${MAX_FDS:-200000}"

log()  { printf '\033[1;34m[+]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[!]\033[0m %s\n' "$*" >&2; }
erro() { printf '\033[1;31m[x]\033[0m %s\n' "$*" >&2; exit 1; }

# ----------------------------------------------------------------------------
# Flags
# ----------------------------------------------------------------------------
USAR_AUTH=false
USAR_TLS=false
for arg in "$@"; do
  case "$arg" in
    --auth) USAR_AUTH=true ;;
    --tls)  USAR_TLS=true ;;
    -h|--help)
      grep -E '^#( |$)' "$0" | sed -E 's/^# ?//'
      exit 0 ;;
    *) erro "argumento desconhecido: ${arg} (use --help)" ;;
  esac
done

[[ $EUID -eq 0 ]] || erro "execute como root (sudo $0 $*)."
command -v apt-get >/dev/null 2>&1 || erro "este script e para sistemas baseados em Debian/Ubuntu."

# ----------------------------------------------------------------------------
# 1. Instalacao dos pacotes
# ----------------------------------------------------------------------------
instalar_pacotes() {
  log "Atualizando indices de pacotes e instalando o Mosquitto..."
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -y
  apt-get install -y mosquitto mosquitto-clients openssl
  systemctl enable mosquitto >/dev/null 2>&1 || true
}

# ----------------------------------------------------------------------------
# 2. Ajuste de kernel e limites (concorrencia)
# ----------------------------------------------------------------------------
# Cada conexao MQTT consome um descritor de arquivo e um socket. Para milhares
# de sensores simultaneos e preciso elevar o teto de FDs, a fila de aceite de
# conexoes (somaxconn/syn_backlog) e ampliar a faixa de portas efemeras.
ajustar_kernel() {
  log "Aplicando ajuste de kernel para muitas conexoes (${SYSCTL_FILE})..."
  cat > "${SYSCTL_FILE}" <<EOF
# Ajuste do broker Mosquitto - PoC de qualidade do ar (Atividade 3)
fs.file-max = 2097152
net.core.somaxconn = 65535
net.core.netdev_max_backlog = 65535
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.ip_local_port_range = 1024 65535
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 15
EOF
  sysctl --quiet -p "${SYSCTL_FILE}" || warn "sysctl nao aplicou tudo (comum em containers)."

  log "Elevando o limite de descritores do servico para ${MAX_FDS}..."
  mkdir -p "${SYSTEMD_OVERRIDE_DIR}"
  cat > "${SYSTEMD_OVERRIDE_DIR}/override.conf" <<EOF
[Service]
LimitNOFILE=${MAX_FDS}
EOF
  systemctl daemon-reload
}

# ----------------------------------------------------------------------------
# 3. Configuracao tunada do broker
# ----------------------------------------------------------------------------
instalar_config() {
  log "Instalando configuracao tunada em ${CONF_FILE}..."
  mkdir -p "${CONF_DIR}/conf.d"
  cat > "${CONF_FILE}" <<EOF
# Configuracao gerada por setup_ubuntu_broker.sh - Atividade 3
# Broker de ingestao de qualidade do ar.

persistence true
persistence_location /var/lib/mosquitto/
autosave_interval 1800

log_dest file /var/log/mosquitto/mosquitto.log
log_type error
log_type warning
log_type notice
log_type information
connection_messages true
log_timestamp true
sys_interval 10

# Desempenho e concorrencia
max_connections -1
max_inflight_messages 100
max_queued_messages 2000
queue_qos0_messages false
max_packet_size 8192

# Listener texto 1883 (rede interna/confiavel)
listener 1883 0.0.0.0
protocol mqtt
EOF

  if [[ "${USAR_AUTH}" == true ]]; then
    cat >> "${CONF_FILE}" <<EOF
allow_anonymous false
password_file ${PASSWD_FILE}
acl_file ${ACL_FILE}
EOF
  else
    cat >> "${CONF_FILE}" <<EOF
# ATENCAO: anonimo habilitado - use apenas em rede isolada/PoC.
allow_anonymous true
EOF
  fi
}

# ----------------------------------------------------------------------------
# 4. Autenticacao e ACL
# ----------------------------------------------------------------------------
configurar_auth() {
  local usuario="${MQTT_USER:-ingestor}"
  local senha="${MQTT_PASSWORD:-}"

  if [[ -z "${senha}" ]]; then
    read -r -s -p "Senha para o usuario MQTT '${usuario}': " senha; echo
    [[ -n "${senha}" ]] || erro "senha vazia."
  fi

  log "Criando/atualizando usuario MQTT '${usuario}'..."
  # -c cria o arquivo; usamos -b (batch). Recria para garantir idempotencia.
  touch "${PASSWD_FILE}"
  mosquitto_passwd -b "${PASSWD_FILE}" "${usuario}" "${senha}"
  chown mosquitto: "${PASSWD_FILE}"
  chmod 600 "${PASSWD_FILE}"

  log "Instalando ACL de menor privilegio em ${ACL_FILE}..."
  cat > "${ACL_FILE}" <<'EOF'
# ACL do broker de qualidade do ar - menor privilegio.
# Topico do contrato: qualidade-ar/{site_id}/{device_id}/telemetria

# Dispositivos publicam apenas no proprio topico (usuario == device_id).
pattern write qualidade-ar/+/%u/telemetria

# Servico de ingestao le toda a arvore do projeto.
user ingestor
topic read qualidade-ar/#

# Operador observa as metricas internas do broker.
user operador
topic read $SYS/#
EOF
  chown mosquitto: "${ACL_FILE}"
  chmod 640 "${ACL_FILE}"
}

# ----------------------------------------------------------------------------
# 5. TLS de teste (CA propria)
# ----------------------------------------------------------------------------
# Gera uma CA e um certificado de servidor para habilitar o listener 8883.
# E uma CA de TESTE. Em producao, use certificados de uma autoridade real e
# certificado por dispositivo (mTLS), como no plano de AWS IoT Core.
configurar_tls() {
  mkdir -p "${CERTS_DIR}"
  if [[ -f "${CERTS_DIR}/server.crt" ]]; then
    log "Certificados TLS ja existem; mantendo os atuais."
  else
    log "Gerando CA e certificado de servidor de teste em ${CERTS_DIR}..."
    local host_cn; host_cn="$(hostname -f 2>/dev/null || hostname)"
    openssl req -new -x509 -days 825 -nodes \
      -subj "/CN=QAR-Broker-CA" \
      -keyout "${CERTS_DIR}/ca.key" -out "${CERTS_DIR}/ca.crt" 2>/dev/null
    openssl req -new -nodes \
      -subj "/CN=${host_cn}" \
      -keyout "${CERTS_DIR}/server.key" -out "${CERTS_DIR}/server.csr" 2>/dev/null
    openssl x509 -req -in "${CERTS_DIR}/server.csr" -days 825 \
      -CA "${CERTS_DIR}/ca.crt" -CAkey "${CERTS_DIR}/ca.key" -CAcreateserial \
      -out "${CERTS_DIR}/server.crt" 2>/dev/null
    rm -f "${CERTS_DIR}/server.csr"
  fi
  chown -R mosquitto: "${CERTS_DIR}"
  chmod 600 "${CERTS_DIR}"/*.key

  log "Habilitando listener TLS 8883..."
  cat >> "${CONF_FILE}" <<EOF

# Listener TLS 8883 (habilitado por --tls)
listener 8883 0.0.0.0
protocol mqtt
cafile   ${CERTS_DIR}/ca.crt
certfile ${CERTS_DIR}/server.crt
keyfile  ${CERTS_DIR}/server.key
tls_version tlsv1.2
EOF
}

# ----------------------------------------------------------------------------
# 6. Ativacao do servico
# ----------------------------------------------------------------------------
ativar_servico() {
  log "Validando a configuracao..."
  # -c so valida a sintaxe; mosquitto sai apos carregar quando sem stdin util.
  if ! mosquitto -c /etc/mosquitto/mosquitto.conf -t 2>/dev/null; then
    warn "nao foi possivel validar via '-t' nesta versao; seguindo."
  fi

  log "Reiniciando o Mosquitto..."
  systemctl restart mosquitto
  sleep 1
  if systemctl is-active --quiet mosquitto; then
    log "Mosquitto ativo."
  else
    erro "o Mosquitto nao subiu. Veja: journalctl -u mosquitto -n 50"
  fi
}

# ----------------------------------------------------------------------------
# Execucao
# ----------------------------------------------------------------------------
main() {
  log "Iniciando provisionamento do broker (auth=${USAR_AUTH}, tls=${USAR_TLS})."
  instalar_pacotes
  ajustar_kernel
  instalar_config
  [[ "${USAR_AUTH}" == true ]] && configurar_auth
  [[ "${USAR_TLS}"  == true ]] && configurar_tls
  ativar_servico

  echo
  log "Concluido. Resumo:"
  echo "    Config .......... ${CONF_FILE}"
  echo "    Listener texto .. 1883"
  [[ "${USAR_TLS}"  == true ]] && echo "    Listener TLS .... 8883 (CA: ${CERTS_DIR}/ca.crt)"
  [[ "${USAR_AUTH}" == true ]] && echo "    Autenticacao .... ativa (${PASSWD_FILE}, ${ACL_FILE})"
  [[ "${USAR_AUTH}" == false ]] && warn "Anonimo habilitado - apropriado somente para PoC em rede isolada."
  echo
  echo "  Teste rapido (de outra maquina/terminal):"
  echo "    mosquitto_sub -h <IP> -p 1883 -t 'qualidade-ar/#' -v"
  echo "    python poc/ingestao_teste.py --host <IP> --sensores 5000"
}

main
