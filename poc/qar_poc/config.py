# -*- coding: utf-8 -*-
"""
config.py — Configuracao imutavel e picklavel da carga.

Papel: transportar, num unico objeto de tipos primitivos, tudo que o
Coordenador precisa. Por ser composto so de primitivos, ele e **picklavel** —
requisito para o modo multiprocessos (o objeto e enviado a cada processo filho).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ConfigCarga:
    # destino
    host: str
    porta: int
    # topologia
    sensores: int
    gateways: int          # 1 gateway = 1 site = 1 conexao MQTT
    processos: int         # 1 = so threads; >1 = shards em processos separados
    prefixo_site: str
    # tempo/carga
    intervalo: float
    duracao: float
    prob_degradar: float
    # MQTT
    qos: int
    usuario: str | None
    senha: str | None
    tls: bool
    tls_inseguro: bool
    keepalive: int
    max_inflight: int
    max_fila: int
    # execucao
    dry_run: bool
    relatorio: str | None
    periodo_reporte: float
    seed: int

    def params_base(self) -> dict:
        """Parametros de conexao comuns a todos os gateways (sem client_id)."""
        return {
            "host": self.host,
            "porta": self.porta,
            "keepalive": self.keepalive,
            "qos": self.qos,
            "usuario": self.usuario,
            "senha": self.senha,
            "tls": self.tls,
            "tls_inseguro": self.tls_inseguro,
            "max_inflight": self.max_inflight,
            "max_fila": self.max_fila,
        }
