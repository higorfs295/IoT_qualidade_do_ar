# -*- coding: utf-8 -*-
"""
metricas.py — A entidade "Observabilidade".

Papel na arquitetura: coletar e agregar os numeros que provam o comportamento
do sistema (vazao, falhas, backpressure, latencia). E o equivalente local ao
CloudWatch descrito no plano da AWS.

Decisao de desempenho: cada conexao/gateway tem o SEU proprio objeto
`MetricasConexao`. No caminho quente (a cada publicacao) so ha incrementos
locais, sem lock compartilhado entre threads. O `Coordenador` agrega por soma
de snapshots periodicamente. O unico ponto com lock e o buffer de latencias,
porque ele e alimentado pela thread de rede do paho (callback on_publish).
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field


@dataclass
class MetricasConexao:
    """Contadores de uma unica conexao MQTT (um gateway)."""

    publicadas: int = 0
    falhas: int = 0
    backpressure: int = 0  # publish recusado por fila cheia (MQTT_ERR_QUEUE_SIZE)
    reconexoes: int = 0
    conectado: bool = False
    # Latencias de PUBACK (ms) acumuladas desde o ultimo flush do reporter.
    _latencias: list = field(default_factory=list)
    _lat_lock: threading.Lock = field(default_factory=threading.Lock)

    def registrar_latencia(self, ms: float) -> None:
        """Chamado pela thread de rede do paho ao receber o PUBACK."""
        with self._lat_lock:
            self._latencias.append(ms)
            # Limita memoria: mantem no maximo as ultimas 5000 amostras.
            if len(self._latencias) > 5000:
                del self._latencias[:2500]

    def coletar_latencias(self) -> list:
        """Retira e devolve as latencias acumuladas (esvazia o buffer)."""
        with self._lat_lock:
            amostras = self._latencias
            self._latencias = []
        return amostras


def percentil(ordenada: list[float], pct: float) -> float:
    """Percentil por interpolacao linear. `ordenada` deve estar ordenada."""
    if not ordenada:
        return 0.0
    k = (len(ordenada) - 1) * (pct / 100.0)
    f = int(k)
    c = min(f + 1, len(ordenada) - 1)
    if f == c:
        return ordenada[f]
    return ordenada[f] + (ordenada[c] - ordenada[f]) * (k - f)


@dataclass
class SnapshotAgregado:
    """Fotografia agregada de todas as conexoes num instante."""

    publicadas: int = 0
    falhas: int = 0
    backpressure: int = 0
    conectados: int = 0
    total_conexoes: int = 0
    lat_p50: float = 0.0
    lat_p95: float = 0.0
    lat_p99: float = 0.0

    def como_dict(self) -> dict:
        return {
            "publicadas": self.publicadas,
            "falhas": self.falhas,
            "backpressure": self.backpressure,
            "conectados": self.conectados,
            "total_conexoes": self.total_conexoes,
            "lat_p50": round(self.lat_p50, 2),
            "lat_p95": round(self.lat_p95, 2),
            "lat_p99": round(self.lat_p99, 2),
        }


def agregar(conexoes: list[MetricasConexao], latencias_janela: list[float]) -> SnapshotAgregado:
    """Soma os contadores de todas as conexoes e calcula percentis da janela."""
    snap = SnapshotAgregado(total_conexoes=len(conexoes))
    for m in conexoes:
        snap.publicadas += m.publicadas
        snap.falhas += m.falhas
        snap.backpressure += m.backpressure
        if m.conectado:
            snap.conectados += 1
    if latencias_janela:
        latencias_janela.sort()
        snap.lat_p50 = percentil(latencias_janela, 50)
        snap.lat_p95 = percentil(latencias_janela, 95)
        snap.lat_p99 = percentil(latencias_janela, 99)
    return snap
