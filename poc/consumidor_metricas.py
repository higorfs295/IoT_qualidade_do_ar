#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
 consumidor_metricas.py — CLI do sink de ingestao
 Projeto: Monitoramento de Qualidade do Ar - Atividade 3
=============================================================================

Casca de linha de comando do consumidor. A logica vive em `qar_poc.sink`
(entidade Ingestor). Assina os topicos de telemetria e mede a ingestao:
vazao, dispositivos ativos, latencia, mensagens invalidas e, principalmente,
LACUNAS por `sequence` (a prova concreta de "como evitar perda de mensagens").

-----------------------------------------------------------------------------
 Uso
-----------------------------------------------------------------------------
  python consumidor_metricas.py --host localhost
  python consumidor_metricas.py --host localhost --topico "qualidade-ar/#"

Requisitos: paho-mqtt >= 2.0
=============================================================================
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from qar_poc import contrato
from qar_poc.sink import ConfigSink, Ingestor


def parse_args(argv):
    p = argparse.ArgumentParser(
        description="Consumidor de metricas da PoC de ingestao (Atividade 3).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--host", default=os.getenv("MQTT_HOST", "localhost"))
    p.add_argument("--porta", type=int, default=int(os.getenv("MQTT_PORT", "1883")))
    p.add_argument("--topico", default=contrato.topico_assinatura(),
                   help="Filtro de topico a assinar.")
    p.add_argument("--qos", type=int, choices=[0, 1, 2], default=1)
    p.add_argument("--usuario", default=os.getenv("MQTT_USER"))
    p.add_argument("--senha", default=os.getenv("MQTT_PASSWORD"))
    p.add_argument("--tls", action="store_true")
    p.add_argument("--tls-inseguro", action="store_true")
    p.add_argument("--duracao", type=float, default=0,
                   help="Duracao em segundos (0 = continuo).")
    p.add_argument("--periodo-reporte", type=float, default=2.0)
    a = p.parse_args(argv)
    return ConfigSink(
        host=a.host, porta=a.porta, topico=a.topico, qos=a.qos,
        usuario=a.usuario, senha=a.senha, tls=a.tls, tls_inseguro=a.tls_inseguro,
        duracao=a.duracao, periodo_reporte=a.periodo_reporte,
    )


def main(argv=None) -> int:
    return Ingestor(parse_args(argv if argv is not None else sys.argv[1:])).executar()


if __name__ == "__main__":
    raise SystemExit(main())
