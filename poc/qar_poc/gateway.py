# -*- coding: utf-8 -*-
"""
gateway.py — A entidade "Gateway de Borda".

Papel na arquitetura: um gateway concentra os sensores de UM site (uma sala,
um andar, um predio) e mantem UMA conexao MQTT de uplink para o broker. E o
equivalente, na PoC, ao par ESP32+roteador da Atividade 1 e ao "gateway"
citado explicitamente na Etapa 3 da Atividade 3.

Por que isso deixa a PoC "mais distribuida por papeis":
  * o Sensor so mede; o Gateway so agenda e transporta;
  * cada Gateway roda em sua propria thread e e independente dos demais —
    nenhuma trava compartilhada no caminho de publicacao;
  * o particionamento por site espelha a chave de particao do S3
    (`site_id`) no plano de armazenamento do Wilson.

Estrategia de comunicacao (reducao de latencia): cada sensor recebe um
**deslocamento de fase** fixo dentro da janela de envio, de modo que os N
sensores do site NAO disparam todos em t=0. As publicacoes ficam espalhadas ao
longo da janela, o que achata o pico instantaneo no broker e mantem o PUBACK
baixo. Internamente, um min-heap ordena os sensores pelo proximo vencimento.
"""

from __future__ import annotations

import heapq
import json
import threading

from .metricas import MetricasConexao
from .sensor import Dispositivo
from .transporte import ClienteMQTT, ParametrosConexao, client_id_gateway


class Gateway(threading.Thread):
    """Concentrador de borda: sensores de um site sobre uma conexao MQTT."""

    def __init__(
        self,
        gateway_id: int,
        dispositivos: list[Dispositivo],
        params_base: dict,
        intervalo: float,
        prob_degradar: float,
        prefixo_client: str,
        parar: threading.Event,
        inicio_janela: float,
        dry_run: bool = False,
    ):
        super().__init__(name=f"gateway-{gateway_id}", daemon=True)
        self.gateway_id = gateway_id
        self.dispositivos = dispositivos
        self.intervalo = intervalo
        self.prob_degradar = prob_degradar
        self.parar = parar
        self.inicio_janela = inicio_janela
        self.dry_run = dry_run

        # Cada gateway tem sua propria observabilidade e seu proprio cliente.
        self.metricas = MetricasConexao()
        params = ParametrosConexao(
            client_id=client_id_gateway(prefixo_client, gateway_id),
            **params_base,
        )
        self.cliente = ClienteMQTT(params, self.metricas)

    # Sites atendidos por este gateway (normalmente um; util para logs/relatorio).
    @property
    def sites(self) -> set[str]:
        return {d.site_id for d in self.dispositivos}

    def run(self) -> None:
        if not self.dry_run:
            if not self.cliente.conectar():
                return

        # Agenda inicial: cada dispositivo com um phase offset fixo, para
        # espalhar a carga uniformemente ao longo da janela de envio.
        heap: list[tuple[float, int]] = []
        n = len(self.dispositivos)
        for i in range(n):
            fase = (i / n) * self.intervalo if n else 0.0
            heapq.heappush(heap, (self.inicio_janela + fase, i))

        while not self.parar.is_set() and heap:
            venc, idx = heap[0]
            agora = _monotonic()
            if venc > agora:
                # Dorme ate o proximo envio, mas acorda para checar parada.
                self.parar.wait(timeout=min(venc - agora, 0.5))
                continue

            heapq.heappop(heap)
            disp = self.dispositivos[idx]
            payload = disp.proxima_leitura(self.prob_degradar)

            if not self.dry_run:
                corpo = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
                self.cliente.publicar(disp.topico(), corpo)
            else:
                # Em dry-run so ha geracao: conta para medir a vazao do gerador.
                json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
                self.metricas.publicadas += 1

            heapq.heappush(heap, (venc + self.intervalo, idx))

        if not self.dry_run:
            self.cliente.desconectar()


def _monotonic() -> float:
    # Isolado para facilitar teste/instrumentacao futura.
    import time

    return time.monotonic()
