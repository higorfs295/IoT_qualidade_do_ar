# -*- coding: utf-8 -*-
"""
sink.py — A entidade "Ingestor/Validador".

Papel na arquitetura: assina os topicos de telemetria e faz, localmente e sem
AWS, o papel que o plano da nuvem atribui a Lambda: conferir o contrato,
detectar lacunas e observar latencia. E o consumidor que fecha o laco da PoC.

O que ele comprova (mapeado as Questoes para Discussao da Atividade 3):

  * "Como evitar perda de mensagens?"  -> deteccao de lacunas por `sequence`
    (por dispositivo). Sob QoS 1 as lacunas devem ser ~zero; sob QoS 0 elas
    aparecem, evidenciando por que o contrato exige QoS 1.
  * "Como monitorar a solucao?"        -> vazao, dispositivos ativos, latencia,
    taxa de invalidas.
  * "Modelagem dos dados"              -> valida o contrato v1.0 (via contrato.py).

Latencia: `sent_at` vem do relogio do publicador; a latencia fim-a-fim so e
confiavel se publicador e consumidor compartilham relogio (na PoC, a mesma
maquina). Em producao usa-se o tempo de ingestao do broker/IoT Core.
"""

from __future__ import annotations

import json
import os
import signal
import sys
import threading
import time
from dataclasses import dataclass, field

from . import contrato

try:
    import paho.mqtt.client as mqtt
except ImportError:  # pragma: no cover
    print("ERRO: paho-mqtt nao esta instalado. Rode 'pip install -r "
          "requirements.txt'.", file=sys.stderr)
    raise SystemExit(2)


@dataclass
class EstadoSink:
    recebidas: int = 0
    invalidas: int = 0
    lacunas: int = 0        # total de mensagens presumidamente perdidas
    reordenadas: int = 0    # sequence menor que a ultima vista
    duplicadas: int = 0     # message_id repetido
    bytes_total: int = 0
    lat_amostras: list = field(default_factory=list)
    ultimo_seq: dict = field(default_factory=dict)  # device_id -> ultima sequence
    ids_vistos: set = field(default_factory=set)     # message_id (janela recente)
    lock: threading.Lock = field(default_factory=threading.Lock)


@dataclass
class ConfigSink:
    host: str
    porta: int
    topico: str
    qos: int
    usuario: str | None
    senha: str | None
    tls: bool
    tls_inseguro: bool
    duracao: float
    periodo_reporte: float


class Ingestor:
    """Consumidor que valida o contrato e mede a ingestao observada."""

    def __init__(self, cfg: ConfigSink):
        self.cfg = cfg
        self.estado = EstadoSink()
        self.parar = threading.Event()
        self._cliente = None

    # ---- callbacks ------------------------------------------------------
    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        rc = getattr(reason_code, "value", reason_code)
        if rc == 0:
            client.subscribe(self.cfg.topico, qos=self.cfg.qos)
            print(f"[ok] conectado e inscrito em '{self.cfg.topico}' (QoS {self.cfg.qos})")
        else:
            print(f"[erro] conexao recusada, codigo {rc}", file=sys.stderr)

    def _on_message(self, client, userdata, message):
        e = self.estado
        corpo = message.payload
        try:
            msg = json.loads(corpo)
        except (ValueError, UnicodeDecodeError):
            with e.lock:
                e.recebidas += 1
                e.invalidas += 1
            return

        erro = contrato.validar_contrato(msg)
        agora = time.time()
        lat_ms = None
        env = contrato.parse_sent_at(msg.get("sent_at", "")) if isinstance(msg, dict) else None
        if env is not None:
            lat_ms = max(0.0, (agora - env) * 1000.0)

        with e.lock:
            e.recebidas += 1
            e.bytes_total += len(corpo)
            if erro is not None:
                e.invalidas += 1
                return

            mid = msg["message_id"]
            if mid in e.ids_vistos:
                e.duplicadas += 1
            else:
                e.ids_vistos.add(mid)
                if len(e.ids_vistos) > 200_000:
                    e.ids_vistos.clear()  # janela deslizante para limitar memoria

            dev, seq = msg["device_id"], msg["sequence"]
            anterior = e.ultimo_seq.get(dev)
            if anterior is not None:
                delta = seq - anterior
                if delta > 1:
                    e.lacunas += delta - 1       # mensagens que faltaram no meio
                elif delta <= 0:
                    e.reordenadas += 1
            e.ultimo_seq[dev] = max(seq, anterior) if anterior is not None else seq

            if lat_ms is not None:
                e.lat_amostras.append(lat_ms)
                if len(e.lat_amostras) > 20_000:
                    del e.lat_amostras[:10_000]

    # ---- execucao -------------------------------------------------------
    def executar(self) -> int:
        cid = f"sink-ingestor-{os.getpid()}"
        self._cliente = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=cid)
        self._cliente.on_connect = self._on_connect
        self._cliente.on_message = self._on_message
        if self.cfg.usuario:
            self._cliente.username_pw_set(self.cfg.usuario, self.cfg.senha)
        if self.cfg.tls:
            self._cliente.tls_set()
            if self.cfg.tls_inseguro:
                self._cliente.tls_insecure_set(True)

        try:
            self._cliente.connect(self.cfg.host, self.cfg.porta, keepalive=60)
        except Exception as exc:
            print(f"[erro] nao foi possivel conectar em "
                  f"{self.cfg.host}:{self.cfg.porta}: {exc}", file=sys.stderr)
            return 1

        signal.signal(signal.SIGINT, lambda *_: self.parar.set())
        try:
            signal.signal(signal.SIGTERM, lambda *_: self.parar.set())
        except (ValueError, AttributeError):
            pass

        self._cliente.loop_start()
        self._painel()
        self._cliente.loop_stop()
        self._cliente.disconnect()
        return self._resumo()

    def _painel(self) -> None:
        e = self.estado
        t0 = time.monotonic()
        ultimo, ultimo_t = 0, t0
        prazo = t0 + self.cfg.duracao if self.cfg.duracao > 0 else None

        cab = (f"{'t(s)':>6} {'recebidas':>12} {'msg/s':>10} {'devs':>7} "
               f"{'lacunas':>9} {'dup':>7} {'inval':>7} {'lat_med(ms)':>12}")
        print("\n" + cab)
        print("-" * len(cab))

        while not self.parar.is_set():
            self.parar.wait(timeout=self.cfg.periodo_reporte)
            agora = time.monotonic()
            with e.lock:
                recebidas, devs = e.recebidas, len(e.ultimo_seq)
                lacunas, dup, inval = e.lacunas, e.duplicadas, e.invalidas
                lat = list(e.lat_amostras[-2000:])
            dt = max(agora - ultimo_t, 1e-6)
            taxa = (recebidas - ultimo) / dt
            ultimo, ultimo_t = recebidas, agora
            lat_med = sum(lat) / len(lat) if lat else 0.0
            print(f"{agora - t0:6.0f} {recebidas:12,d} {taxa:10,.0f} {devs:7,d} "
                  f"{lacunas:9,d} {dup:7,d} {inval:7,d} {lat_med:12.1f}"
                  .replace(",", "."))
            if prazo is not None and agora >= prazo:
                self.parar.set()

    def _resumo(self) -> int:
        e = self.estado

        def f(n):
            return f"{n:,}".replace(",", ".")

        print("\n" + "=" * 70)
        print(" Resumo da ingestao observada")
        print("=" * 70)
        print(f"  mensagens recebidas .. {f(e.recebidas)}")
        print(f"  dispositivos ativos .. {f(len(e.ultimo_seq))}")
        print(f"  bytes recebidos ...... {f(e.bytes_total)}")
        print(f"  lacunas (perdas) ..... {f(e.lacunas)}")
        print(f"  reordenadas .......... {f(e.reordenadas)}")
        print(f"  duplicadas ........... {f(e.duplicadas)}")
        print(f"  invalidas (contrato) . {f(e.invalidas)}")
        if e.recebidas:
            perda = 100.0 * e.lacunas / (e.recebidas + e.lacunas)
            print(f"  perda estimada ....... {perda:.4f}%")
        if e.lat_amostras:
            a = sorted(e.lat_amostras)
            n = len(a)
            print(f"  latencia sent->recv .. p50={a[n // 2]:.1f} ms  "
                  f"p95={a[min(n - 1, int(n * 0.95))]:.1f} ms  max={a[-1]:.1f} ms")
        print("=" * 70)
        return 0
