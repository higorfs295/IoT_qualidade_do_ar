#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
 central_sensores.py — Central de Sensores Virtual (Hardware-in-the-Loop)
 Projeto: Estacao de Monitoramento de Qualidade do Ar (base_final)
=============================================================================

Papel na arquitetura HIL (ver BASE_FINAL.md): este script roda no PC e faz o
papel dos sensores fisicos DURANTE o desenvolvimento. Ele gera leituras
ambientais coerentes e as envia, em JSON delimitado por linha (NDJSON), pela
porta Serial/USB ao ESP32. O ESP32 (firmware real) decodifica cada quadro e o
trata como se viesse de um sensor real — a "FonteSimulada" da HAL.

Quando os sensores fisicos chegarem, o firmware troca `MODO_SENSOR` para
FONTE_FISICA e este script deixa de ser necessario, sem mudar mais nada.

-----------------------------------------------------------------------------
 Sensores emulados (modulos escolhidos no BASE_FINAL.md)
-----------------------------------------------------------------------------
   SCD41     -> co2_ppm            (NDIR)
   SGP40     -> voc_index          (indice VOC 1-500, ~100 em ar limpo)
   MiCS-5524 -> lpg_ppm            (somente cenário sintético de integração)
   PMS7003   -> pm1/pm25/pm10_ugm3 (particulados)
   SHT31     -> temperature_c, humidity_pct

-----------------------------------------------------------------------------
 Cenarios (a "central" varia de normal a emergencia)
-----------------------------------------------------------------------------
   normal          operacao tipica de ambiente fechado
   pico_poluicao   particulado alto (transito, obra, fumaca externa)
   incendio        CO2 e particulado muito altos, VOC alto, temperatura sobe
   vazamento_glp   valor sintético alto em lpg_ppm; não é curva do MiCS-5524
   auto            majoritariamente normal, injetando eventos aleatorios

-----------------------------------------------------------------------------
 Formato do quadro NDJSON (uma linha por leitura, terminada em \\n)
-----------------------------------------------------------------------------
 {"t":"sensors","seq":128,"co2_ppm":812,"voc_index":140,"lpg_ppm":6,
  "pm1_ugm3":9.2,"pm25_ugm3":14.7,"pm10_ugm3":22.1,
  "temperature_c":24.8,"humidity_pct":51.3,"cenario":"normal"}

-----------------------------------------------------------------------------
 Uso
-----------------------------------------------------------------------------
  # Sem hardware: imprime os quadros (util para inspecionar/validar)
  python central_sensores.py --dry-run --intervalo 1

  # Alimentando o ESP32 pela serial (requer pyserial)
  python central_sensores.py --porta COM5 --baud 115200 --cenario auto

  # Forcar um cenario de emergencia por 30 s
  python central_sensores.py --dry-run --cenario incendio --duracao 30

  # Conferir a geracao antes de usar
  python central_sensores.py --self-test

 Requisitos: Python 3.10+; pyserial (apenas para enviar pela porta serial).
 O pacote qar_poc (da PoC) e reutilizado para a geracao coerente das leituras.
=============================================================================
"""

from __future__ import annotations

import argparse
import json
import os
import random
import signal
import sys
import time

# Reutiliza o modelo de sensor coerente (random walk em faixas plausiveis) da
# PoC. Adiciona-se a ele uma camada de CENARIOS que perturba as medicoes.
_RAIZ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_RAIZ, "..", "poc"))

from qar_poc.sensor import Dispositivo  # noqa: E402

CENARIOS = ("normal", "pico_poluicao", "incendio", "vazamento_glp", "auto")


def _clamp(v, lo, hi):
    # Retorna float mesmo ao bater no limite (evita round(int,1) virar int).
    return float(max(lo, min(hi, v)))


def aplicar_cenario(m: dict, cenario: str, rng: random.Random) -> None:
    """Perturba as medicoes-base conforme o cenario, in-place.

    Recebe o dicionario `measurements` (co2_ppm, voc_index, lpg_ppm, pm*, temp,
    umidade) e o modifica para refletir a situacao. co2/voc/lpg permanecem
    inteiros; particulados/temperatura/umidade, ponto flutuante.
    """
    if cenario == "pico_poluicao":
        m["pm1_ugm3"] = round(_clamp(m["pm1_ugm3"] * rng.uniform(3, 5), 0, 500), 1)
        m["pm25_ugm3"] = round(_clamp(m["pm25_ugm3"] * rng.uniform(3, 5), 0, 500), 1)
        m["pm10_ugm3"] = round(_clamp(m["pm10_ugm3"] * rng.uniform(3, 5), 0, 600), 1)
        m["voc_index"] = int(_clamp(m["voc_index"] + rng.uniform(80, 150), 1, 500))

    elif cenario == "incendio":
        m["co2_ppm"] = int(_clamp(rng.uniform(1500, 3500), 400, 5000))
        m["pm1_ugm3"] = round(_clamp(m["pm1_ugm3"] * rng.uniform(6, 10), 0, 500), 1)
        m["pm25_ugm3"] = round(_clamp(m["pm25_ugm3"] * rng.uniform(6, 10), 0, 800), 1)
        m["pm10_ugm3"] = round(_clamp(m["pm10_ugm3"] * rng.uniform(6, 10), 0, 900), 1)
        m["voc_index"] = int(_clamp(rng.uniform(300, 480), 1, 500))
        m["temperature_c"] = round(_clamp(m["temperature_c"] + rng.uniform(8, 20), 0, 80), 1)
        m["lpg_ppm"] = int(_clamp(m["lpg_ppm"] + rng.uniform(40, 120), 0, 1000))

    elif cenario == "vazamento_glp":
        m["lpg_ppm"] = int(_clamp(rng.uniform(300, 900), 0, 1000))
        m["voc_index"] = int(_clamp(m["voc_index"] + rng.uniform(60, 140), 1, 500))

    # "normal": mantem a leitura-base do random walk.


class CentralSensores:
    """Gera quadros HIL para um dispositivo, aplicando o cenario ativo."""

    def __init__(self, device_id: str, site_id: str, seed: int):
        self.disp = Dispositivo(device_id, site_id, seed=seed)
        self.rng = self.disp.rng
        # Estado do modo "auto": quantos quadros ainda durara o evento atual.
        self._evento_restante = 0
        self._evento_atual = "normal"

    def _cenario_efetivo(self, cenario: str) -> str:
        """No modo 'auto', decide quando injetar um evento e por quanto tempo."""
        if cenario != "auto":
            return cenario
        if self._evento_restante > 0:
            self._evento_restante -= 1
            return self._evento_atual
        # ~8% de chance de iniciar um evento de 5 a 12 quadros.
        if self.rng.random() < 0.08:
            self._evento_atual = self.rng.choice(
                ["pico_poluicao", "incendio", "vazamento_glp"]
            )
            self._evento_restante = self.rng.randint(5, 12)
            return self._evento_atual
        return "normal"

    def proximo_quadro(self, cenario: str) -> dict:
        # Gera a leitura-base (random walk). prob_degradar=0: os cenarios
        # controlam integralmente as anomalias.
        base = self.disp.proxima_leitura(0.0)
        efetivo = self._cenario_efetivo(cenario)
        medidas = dict(base["measurements"])
        aplicar_cenario(medidas, efetivo, self.rng)
        return {"t": "sensors", "seq": base["sequence"], **medidas, "cenario": efetivo}


def serializar(quadro: dict) -> str:
    """Serializa um quadro como uma linha NDJSON (sem espacos, com \\n)."""
    return json.dumps(quadro, separators=(",", ":"), ensure_ascii=False)


# ---------------------------------------------------------------------------
# Saidas: stdout (dry-run) ou porta serial
# ---------------------------------------------------------------------------
def abrir_serial(porta: str, baud: int):
    """Abre a porta serial (import tardio de pyserial com mensagem clara)."""
    try:
        import serial  # type: ignore
    except ImportError:
        print("ERRO: pyserial nao instalado. Rode 'pip install -r "
              "requirements.txt' ou use --dry-run.", file=sys.stderr)
        raise SystemExit(2)
    try:
        return serial.Serial(porta, baudrate=baud, timeout=1)
    except Exception as exc:
        print(f"ERRO: nao foi possivel abrir {porta} @ {baud}: {exc}",
              file=sys.stderr)
        raise SystemExit(1)


def self_test() -> int:
    """Gera alguns quadros por cenario e confere tipos e faixas."""
    central = CentralSensores("esp32-selftest", "bancada", seed=1)
    inteiros = ("co2_ppm", "voc_index", "lpg_ppm")
    for cen in ("normal", "pico_poluicao", "incendio", "vazamento_glp"):
        for _ in range(50):
            q = central.proximo_quadro(cen)
            for k in inteiros:
                assert isinstance(q[k], int), f"{k} deveria ser int em {cen}"
            for k in ("pm1_ugm3", "pm25_ugm3", "pm10_ugm3", "temperature_c",
                      "humidity_pct"):
                assert isinstance(q[k], float), f"{k} deveria ser float em {cen}"
            # a linha serializada deve reparsear identica
            assert json.loads(serializar(q))["seq"] == q["seq"]
    # o cenario incendio deve, em geral, elevar o co2
    altos = [central.proximo_quadro("incendio")["co2_ppm"] for _ in range(20)]
    assert sum(altos) / len(altos) > 1000, "incendio deveria elevar o CO2"
    print("[self-test] OK: quadros validos em todos os cenarios.")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        description="Central de sensores virtual (HIL) para o firmware da estacao.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--porta", default=os.getenv("SERIAL_PORT"),
                   help="Porta serial do ESP32 (ex.: COM5, /dev/ttyUSB0).")
    p.add_argument("--baud", type=int, default=115200, help="Baud rate da serial.")
    p.add_argument("--dry-run", action="store_true",
                   help="Imprime os quadros no stdout (sem serial/hardware).")
    p.add_argument("--cenario", choices=CENARIOS, default="auto",
                   help="Cenario ambiental a simular.")
    p.add_argument("--intervalo", type=float, default=2.0,
                   help="Segundos entre quadros.")
    p.add_argument("--duracao", type=float, default=0,
                   help="Duracao em segundos (0 = continuo).")
    p.add_argument("--device-id", default="esp32-proto-01",
                   help="Identificador do dispositivo (so informativo no HIL).")
    p.add_argument("--site-id", default="bancada-dev")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--self-test", action="store_true",
                   help="Confere a geracao e sai.")
    p.add_argument("--silenciar-logs", action="store_true",
                   help="Drena, mas nao mostra, os logs recebidos do ESP32.")
    a = p.parse_args(argv if argv is not None else sys.argv[1:])

    if a.intervalo <= 0:
        p.error("--intervalo deve ser > 0")
    if a.duracao < 0:
        p.error("--duracao deve ser >= 0")
    if not 300 <= a.baud <= 4_000_000:
        p.error("--baud fora da faixa suportada")

    if a.self_test:
        return self_test()

    usar_serial = bool(a.porta) and not a.dry_run
    ser = abrir_serial(a.porta, a.baud) if usar_serial else None
    destino = f"{a.porta} @ {a.baud}" if usar_serial else "STDOUT (dry-run)"

    print("=" * 70, file=sys.stderr)
    print(" Central de sensores virtual (HIL) — base_final", file=sys.stderr)
    print("=" * 70, file=sys.stderr)
    print(f"  destino .... {destino}", file=sys.stderr)
    print(f"  cenario .... {a.cenario}", file=sys.stderr)
    print(f"  intervalo .. {a.intervalo:g} s", file=sys.stderr)
    print("=" * 70, file=sys.stderr)

    central = CentralSensores(a.device_id, a.site_id, seed=a.seed)
    parar = {"v": False}
    signal.signal(signal.SIGINT, lambda *_: parar.__setitem__("v", True))

    t0 = time.monotonic()
    enviados = 0
    try:
        while not parar["v"]:
            # A UART USB e bidirecional: alem de escrever os quadros HIL, drene
            # os logs do firmware para o buffer do adaptador nao encher.
            if ser is not None and ser.in_waiting:
                logs = ser.read(ser.in_waiting).decode("utf-8", errors="replace")
                if logs and not a.silenciar_logs:
                    print(logs, end="", file=sys.stderr, flush=True)
            quadro = central.proximo_quadro(a.cenario)
            linha = serializar(quadro)
            if ser is not None:
                ser.write((linha + "\n").encode("utf-8"))
            else:
                print(linha, flush=True)
            enviados += 1
            if a.duracao > 0 and (time.monotonic() - t0) >= a.duracao:
                break
            time.sleep(a.intervalo)
    finally:
        if ser is not None:
            ser.close()
        print(f"\n[fim] {enviados} quadros enviados em "
              f"{time.monotonic() - t0:.1f}s.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
