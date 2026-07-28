# -*- coding: utf-8 -*-
"""
contrato.py — Fonte unica de verdade do contrato de dados (schema v1.0).

Papel nesta arquitetura: **contrato de interface**. Todo mundo (sensor,
gateway, sink) fala a mesma lingua importando daqui. Se o contrato mudar, muda
em um so lugar. Este modulo espelha, em codigo, o que
`docs/modelagem_dados.json` (autoria do Wilson) define em prosa/JSON.

Ele NAO tem estado nem dependencia de rede: sao apenas constantes e funcoes
puras de (de)serializacao, validacao e montagem de topico. Isso o torna seguro
para ser importado por qualquer processo/thread e picklavel para multiprocessing.
"""

from __future__ import annotations

import random
import time
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Constantes do contrato
# ---------------------------------------------------------------------------
# Versao emitida por padrao. O v1.1 (base_final) evolui o v1.0 do Wilson de
# forma ADITIVA: acrescenta voc_index (SGP40) e lpg_ppm (MiCS-5524), refletindo
# os modulos escolhidos no BASE_FINAL.md. O validador aceita as duas versoes.
SCHEMA_VERSION = "1.1"
SCHEMA_VERSIONS_ACEITAS = ("1.0", "1.1")

# Estrutura do topico: qualidade-ar/{site_id}/{device_id}/telemetria
PREFIXO_TOPICO = "qualidade-ar"
SUFIXO_TOPICO = "telemetria"

# Medidas obrigatorias por versao do schema.
#   v1.0: co2, tvoc_ppb, particulados, temp, umidade.
#   v1.1: troca tvoc_ppb por voc_index (SGP40) e acrescenta lpg_ppm (MiCS-5524).
# co2/tvoc_ppb/voc_index/lpg_ppm sao inteiros; o restante e ponto flutuante
# (o contrato exige numero, nunca texto com unidade).
MEDIDAS_V10 = (
    "co2_ppm",
    "tvoc_ppb",
    "pm1_ugm3",
    "pm25_ugm3",
    "pm10_ugm3",
    "temperature_c",
    "humidity_pct",
)
MEDIDAS_V11 = (
    "co2_ppm",
    "voc_index",
    "lpg_ppm",
    "pm1_ugm3",
    "pm25_ugm3",
    "pm10_ugm3",
    "temperature_c",
    "humidity_pct",
)
# Uniao de todas as medidas conhecidas (usada por consumidores genericos).
MEDIDAS = tuple(dict.fromkeys(MEDIDAS_V10 + MEDIDAS_V11))

# Medidas obrigatorias indexadas pela versao do schema.
MEDIDAS_POR_VERSAO = {"1.0": MEDIDAS_V10, "1.1": MEDIDAS_V11}

# Campos de topo obrigatorios em toda mensagem.
CAMPOS_OBRIGATORIOS = (
    "schema_version",
    "message_id",
    "device_id",
    "site_id",
    "sent_at",
    "sequence",
    "measurements",
)

# Valores controlados (enums) do bloco quality.
GAS_STATUS = ("SAFE", "UNSAFE", "UNKNOWN")
SENSOR_STATUS = ("OK", "DEGRADED", "ERROR")


# ---------------------------------------------------------------------------
# Topico
# ---------------------------------------------------------------------------
def montar_topico(site_id: str, device_id: str) -> str:
    """Topico de publicacao de um dispositivo concreto."""
    return f"{PREFIXO_TOPICO}/{site_id}/{device_id}/{SUFIXO_TOPICO}"


def topico_assinatura(site_id: str = "+", device_id: str = "+") -> str:
    """Filtro de assinatura. Padrao: toda a arvore de telemetria do projeto."""
    if site_id == "+" and device_id == "+":
        return f"{PREFIXO_TOPICO}/#"
    return f"{PREFIXO_TOPICO}/{site_id}/{device_id}/{SUFIXO_TOPICO}"


# ---------------------------------------------------------------------------
# ULID — identificador ordenavel por tempo, sem dependencia externa
# ---------------------------------------------------------------------------
# 48 bits de timestamp (ms) + 80 bits de aleatoriedade, base32 de Crockford.
# Serve de chave de idempotencia (message_id): a Lambda do plano AWS usa esse
# campo para deduplicar reentregas de QoS 1 e da fila SQS.
_CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def _codificar_base32(valor: int, tamanho: int) -> str:
    saida = []
    for _ in range(tamanho):
        saida.append(_CROCKFORD[valor & 0x1F])
        valor >>= 5
    return "".join(reversed(saida))


def gerar_ulid(rng: random.Random, agora_ms: int | None = None) -> str:
    """Gera um ULID de 26 caracteres. Um `rng` local evita contencao entre threads."""
    if agora_ms is None:
        agora_ms = int(time.time() * 1000)
    tempo = _codificar_base32(agora_ms & ((1 << 48) - 1), 10)
    aleatorio = _codificar_base32(rng.getrandbits(80), 16)
    return tempo + aleatorio


# ---------------------------------------------------------------------------
# Tempo
# ---------------------------------------------------------------------------
def agora_rfc3339() -> str:
    """Instante atual em UTC, RFC 3339 com milissegundos e sufixo Z."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def parse_sent_at(valor: str) -> float | None:
    """Converte `sent_at` (RFC 3339) em epoch segundos; None se invalido."""
    if not isinstance(valor, str):
        return None
    try:
        return datetime.fromisoformat(valor.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Validacao
# ---------------------------------------------------------------------------
def validar_contrato(msg: dict) -> str | None:
    """
    Valida uma mensagem contra o schema aceito (v1.0 ou v1.1).

    O conjunto de medidas obrigatorias depende do `schema_version`: mensagens
    v1.0 continuam validas (retrocompatibilidade); v1.1 exige voc_index e
    lpg_ppm. Retorna None se conforme; caso contrario, uma descricao curta do
    primeiro erro (para telemetria de rejeicao no sink).
    """
    if not isinstance(msg, dict):
        return "payload nao e objeto JSON"
    for campo in CAMPOS_OBRIGATORIOS:
        if campo not in msg:
            return f"campo ausente: {campo}"
    versao = msg.get("schema_version")
    if versao not in SCHEMA_VERSIONS_ACEITAS:
        return f"schema_version inesperado: {versao}"
    if not isinstance(msg.get("sequence"), int):
        return "sequence nao inteiro"
    medidas = msg.get("measurements")
    if not isinstance(medidas, dict):
        return "measurements nao e objeto"
    for m in MEDIDAS_POR_VERSAO[versao]:
        if m not in medidas:
            return f"medida ausente: {m}"
    quality = msg.get("quality")
    if isinstance(quality, dict):
        gs = quality.get("gas_status")
        ss = quality.get("sensor_status")
        if gs is not None and gs not in GAS_STATUS:
            return f"gas_status invalido: {gs}"
        if ss is not None and ss not in SENSOR_STATUS:
            return f"sensor_status invalido: {ss}"
    return None
