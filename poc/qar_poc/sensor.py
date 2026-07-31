# -*- coding: utf-8 -*-
"""
sensor.py — A entidade "Coisa" (dispositivo de borda).

Papel na arquitetura: representa **uma estacao virtual** equivalente ao ESP32 +
SCD41 + SHT31 + SGP40 + PMS7003 + entrada analogica experimental. Cada
instancia carrega sua identidade, sequencia e estado das medicoes e produz uma
leitura por vez no contrato v1.1.

Este objeto NAO conhece MQTT nem rede — ele so sabe "medir". Quem transporta a
leitura e o Gateway. Essa separacao de responsabilidades e o que torna a PoC
"distribuida por papeis": trocar o transporte (MQTT, HTTP, fila) nao mexe no
sensor.

As medicoes sao ficticias porem plausiveis: cada dispositivo evolui por
**passeio aleatorio** (random walk) dentro de faixas realistas de ambiente
interno, gerando series continuas (e nao ruido branco), o que torna o dashboard
e a deteccao de picos representativos.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from . import contrato


@dataclass
class Faixa:
    """Faixa plausivel de uma grandeza e o passo maximo por leitura."""

    minimo: float
    maximo: float
    passo: float  # variacao maxima por leitura (magnitude do random walk)
    casas: int = 1  # casas decimais; 0 => a grandeza e serializada como inteiro


# Faixas tipicas de ambiente interno. NAO sao limites regulatorios; servem para
# gerar dados verossimeis. Alinhadas aos modulos escolhidos no BASE_FINAL.md:
#   SCD41    -> co2, temperatura, umidade
#   SGP40    -> voc_index (indice VOC 0-500, ~100 em ar limpo)
#   MiCS-5524-> lpg_ppm (valor sintético; hardware real publica tensão bruta)
#   PMS7003  -> pm1, pm2.5, pm10
#   SHT31    -> temperatura, umidade
#
# IMPORTANTE: estas faixas descrevem a operacao NORMAL. Grandezas que so sobem
# em emergencia (lpg, voc) tem linha de base baixa aqui; os picos criticos sao
# aplicados pela camada de CENARIOS do simulador HIL (simulador/central_sensores.py),
# nunca pelo passeio aleatorio. Assim, "normal" nao dispara UNSAFE por acaso.
FAIXAS: dict[str, Faixa] = {
    "co2_ppm": Faixa(400, 1400, 50, casas=0),      # ambiente fechado tipico
    "voc_index": Faixa(50, 180, 12, casas=0),       # ~100 = ar limpo (limiar 250)
    "lpg_ppm": Faixa(0, 30, 3, casas=0),            # traco; vazamento e cenario
    "pm1_ugm3": Faixa(0, 25, 2, casas=1),
    "pm25_ugm3": Faixa(0, 30, 2.5, casas=1),        # limiar 35 (raramente cruza)
    "pm10_ugm3": Faixa(0, 45, 3, casas=1),
    "temperature_c": Faixa(18, 30, 0.3, casas=1),
    "humidity_pct": Faixa(30, 75, 1.0, casas=1),
}


class Dispositivo:
    """Estado de um sensor virtual: identidade, sequencia e leituras correntes."""

    __slots__ = ("device_id", "site_id", "sequence", "rng", "_valores", "firmware", "boot_id")

    def __init__(self, device_id: str, site_id: str, seed: int):
        self.device_id = device_id
        self.site_id = site_id
        self.sequence = 0
        self.firmware = "1.1.0-sim"
        # RNG por dispositivo => reprodutivel e sem lock global.
        self.rng = random.Random(seed)
        self.boot_id = contrato.gerar_ulid(self.rng)
        # Ponto de partida aleatorio na metade inferior de cada faixa.
        self._valores = {
            nome: self.rng.uniform(
                f.minimo, min(f.maximo, f.minimo + (f.maximo - f.minimo) * 0.5)
            )
            for nome, f in FAIXAS.items()
        }

    def _passo(self, nome: str):
        """Avanca uma grandeza por random walk, com clamp na faixa."""
        f = FAIXAS[nome]
        atual = self._valores[nome]
        atual += self.rng.uniform(-f.passo, f.passo)
        atual = float(max(f.minimo, min(f.maximo, atual)))  # clamp; garante float
        self._valores[nome] = atual
        # Campos com 0 casas (CO2, TVOC) saem como inteiros, como no contrato.
        return int(round(atual)) if f.casas == 0 else round(atual, f.casas)

    def proxima_leitura(self, prob_degradar: float) -> dict:
        """
        Produz um payload no contrato v1.1. Injeta falhas ocasionais para
        exercitar o tratamento de nulos e o `sensor_status` do contrato.

        prob_degradar: probabilidade de a leitura vir DEGRADED/ERROR.
        """
        self.sequence += 1
        medidas = {nome: self._passo(nome) for nome in FAIXAS}

        sensor_status = "OK"
        sorte = self.rng.random()
        if sorte < prob_degradar * 0.3:
            # ERROR: a medicao critica de gas fica indisponivel (null).
            sensor_status = "ERROR"
            medidas["co2_ppm"] = None
            medidas["voc_index"] = None
        elif sorte < prob_degradar:
            # DEGRADED: particulado momentaneamente ausente.
            sensor_status = "DEGRADED"
            medidas["pm1_ugm3"] = None

        # gas_status derivado das medicoes (regra didatica, coerente com a
        # Atividade 2, onde o gas era SAFE/UNSAFE). Em v1.1, um pico de GLP
        # (lpg_ppm) tambem dispara UNSAFE — util para o cenario de vazamento.
        if sensor_status == "ERROR":
            gas_status = "UNKNOWN"
        else:
            inseguro = (
                (medidas["co2_ppm"] is not None and medidas["co2_ppm"] > 1000)
                or (medidas["voc_index"] is not None and medidas["voc_index"] > 250)
                or medidas.get("lpg_ppm", 0) > 100
                or medidas["pm25_ugm3"] > 35
            )
            gas_status = "UNSAFE" if inseguro else "SAFE"

        return {
            "schema_version": contrato.SCHEMA_VERSION,
            "message_id": contrato.gerar_ulid(self.rng),
            "device_id": self.device_id,
            "site_id": self.site_id,
            "sent_at": contrato.agora_rfc3339(),
            "sequence": self.sequence,
            "measurements": medidas,
            "quality": {
                "gas_status": gas_status,
                "sensor_status": sensor_status,
            },
            "metadata": {
                "firmware_version": self.firmware,
                "boot_id": self.boot_id,
                "rssi_dbm": -40 - int(self.rng.random() * 50),  # -40 a -90 dBm
            },
        }

    def topico(self) -> str:
        """Topico de publicacao deste dispositivo (delegado ao contrato)."""
        return contrato.montar_topico(self.site_id, self.device_id)
