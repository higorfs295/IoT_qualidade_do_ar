# -*- coding: utf-8 -*-
"""
qar_poc — Pacote da Prova de Conceito de ingestao (Atividade 3).

Monitoramento de Qualidade do Ar — UFG, Internet das Coisas.

A PoC e organizada por PAPEIS (entidades), cada um em seu modulo:

    contrato    fonte unica de verdade do schema v1.0 (topico, validacao, ULID)
    sensor      a "Coisa": modela um dispositivo e gera leituras (Dispositivo)
    transporte  camada de comunicacao MQTT (ClienteMQTT sobre paho-mqtt)
    gateway     concentrador de borda de um site (Gateway); 1 gateway = 1 conexao
    metricas    observabilidade (MetricasConexao, agregacao, percentis)
    coordenador plano de controle: monta a topologia, agrega metricas, relatorio
    config      configuracao imutavel e picklavel (ConfigCarga)
    sink        ingestor/validador que fecha o laco (Ingestor)

Fluxo de dados:

    Sensor -> Gateway -> (MQTT) -> Broker -> Sink
      |          |                              |
      | mede     | agenda por fase + publica    | valida contrato,
      |          | 1 conexao por site           | detecta lacunas por sequence

Entradas de linha de comando (na pasta poc/):
    ingestao_teste.py       -> qar_poc.coordenador.executar
    consumidor_metricas.py  -> qar_poc.sink.Ingestor
"""

from . import contrato  # noqa: F401

__all__ = [
    "contrato",
    "sensor",
    "transporte",
    "gateway",
    "metricas",
    "coordenador",
    "config",
    "sink",
]

__version__ = "1.1.0"
