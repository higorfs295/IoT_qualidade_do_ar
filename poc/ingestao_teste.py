#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
 ingestao_teste.py — CLI do gerador de carga MQTT
 Projeto: Monitoramento de Qualidade do Ar - Atividade 3
=============================================================================

Este arquivo e apenas a "casca" de linha de comando. Toda a logica vive no
pacote `qar_poc`, organizado por papeis (sensor, gateway, transporte,
coordenador, metricas, contrato). Ver poc/README.md e ARQUITETURA.md.

Simula milhares de sensores publicando telemetria no contrato v1.0
(docs/modelagem_dados.json) para demonstrar e medir o fluxo de ingestao.

-----------------------------------------------------------------------------
 Modelo mental
-----------------------------------------------------------------------------
  --sensores   quantos dispositivos virtuais existem (a volumetria)
  --gateways   quantos concentradores de borda (1 gateway = 1 site = 1 conexao)
  --processos  quantos processos paralelos repartem os gateways (sharding)

Espalhamento de fase por gateway mantem a latencia baixa; particionamento por
site espelha a chave de particao do S3 no plano da AWS.

-----------------------------------------------------------------------------
 Uso rapido
-----------------------------------------------------------------------------
  # Sem broker: valida geracao e mede vazao do gerador
  python ingestao_teste.py --dry-run --sensores 10000

  # Contra o Mosquitto local (docker-compose da infra)
  python ingestao_teste.py --host localhost --sensores 5000 --duracao 120

  # Presets de volumetria alinhados a docs/estimativa_carga.md
  python ingestao_teste.py --host localhost --cenario 50000 --gateways 200

  # Paralelismo real: 4 processos repartindo os gateways
  python ingestao_teste.py --host localhost --cenario 100000 --gateways 300 --processos 4

Requisitos: paho-mqtt >= 2.0  (pip install -r requirements.txt)
=============================================================================
"""

from __future__ import annotations

import argparse
import os
import sys

# Garante que o pacote qar_poc seja importavel ao rodar o script diretamente.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from qar_poc.config import ConfigCarga
from qar_poc.coordenador import executar

# Presets de volumetria alinhados a docs/estimativa_carga.md (Wilson).
_CENARIOS = {5000, 10000, 50000, 100000}


def parse_args(argv):
    p = argparse.ArgumentParser(
        description="Gerador de carga MQTT para a PoC de ingestao (Atividade 3).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--host", default=os.getenv("MQTT_HOST", "localhost"))
    p.add_argument("--porta", type=int, default=int(os.getenv("MQTT_PORT", "1883")))
    p.add_argument("--sensores", type=int, default=1000,
                   help="Numero de sensores virtuais (volumetria).")
    p.add_argument("--cenario", type=int, choices=sorted(_CENARIOS),
                   help="Preset de volumetria (5000/10000/50000/100000).")
    p.add_argument("--gateways", type=int, default=100,
                   help="Gateways de borda (1 gateway = 1 site = 1 conexao MQTT).")
    p.add_argument("--conexoes", type=int, default=None,
                   help="Apelido retrocompativel de --gateways.")
    p.add_argument("--processos", type=int, default=1,
                   help="Processos paralelos que repartem os gateways (sharding).")
    p.add_argument("--intervalo", type=float,
                   default=float(os.getenv("MQTT_INTERVALO", "60")),
                   help="Segundos entre leituras de cada sensor.")
    p.add_argument("--duracao", type=float, default=0,
                   help="Duracao do teste em segundos (0 = continuo).")
    p.add_argument("--qos", type=int, choices=[0, 1, 2], default=1)
    p.add_argument("--prefixo-site", default="campus-ufg")
    p.add_argument("--usuario", default=os.getenv("MQTT_USER"))
    p.add_argument("--senha", default=os.getenv("MQTT_PASSWORD"))
    p.add_argument("--tls", action="store_true")
    p.add_argument("--tls-inseguro", action="store_true")
    p.add_argument("--keepalive", type=int, default=60)
    p.add_argument("--max-inflight", type=int, default=100)
    p.add_argument("--max-fila", type=int, default=2000)
    p.add_argument("--prob-degradar", type=float, default=0.02)
    p.add_argument("--periodo-reporte", type=float, default=2.0)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--relatorio", default=None)
    p.add_argument("--seed", type=int, default=42)

    a = p.parse_args(argv)
    if a.sensores < 1:
        p.error("--sensores deve ser >= 1")
    if a.gateways < 1 or (a.conexoes is not None and a.conexoes < 1):
        p.error("--gateways/--conexoes deve ser >= 1")
    if a.processos < 1:
        p.error("--processos deve ser >= 1")
    if a.intervalo <= 0:
        p.error("--intervalo deve ser > 0")
    if a.duracao < 0:
        p.error("--duracao deve ser >= 0")
    if not 0 <= a.prob_degradar <= 1:
        p.error("--prob-degradar deve estar entre 0 e 1")
    if a.periodo_reporte <= 0:
        p.error("--periodo-reporte deve ser > 0")
    if a.tls_inseguro and not a.tls:
        p.error("--tls-inseguro exige --tls")
    sensores = a.cenario if a.cenario else a.sensores
    gateways = a.conexoes if a.conexoes is not None else a.gateways
    gateways = max(1, min(gateways, sensores))  # nunca mais gateways que sensores
    processos = max(1, min(a.processos, gateways))

    return ConfigCarga(
        host=a.host, porta=a.porta, sensores=sensores, gateways=gateways,
        processos=processos, prefixo_site=a.prefixo_site, intervalo=a.intervalo,
        duracao=a.duracao, prob_degradar=a.prob_degradar, qos=a.qos,
        usuario=a.usuario, senha=a.senha, tls=a.tls, tls_inseguro=a.tls_inseguro,
        keepalive=a.keepalive, max_inflight=a.max_inflight, max_fila=a.max_fila,
        dry_run=a.dry_run, relatorio=a.relatorio,
        periodo_reporte=a.periodo_reporte, seed=a.seed,
    )


def main(argv=None) -> int:
    cfg = parse_args(argv if argv is not None else sys.argv[1:])
    return executar(cfg)


if __name__ == "__main__":
    raise SystemExit(main())
