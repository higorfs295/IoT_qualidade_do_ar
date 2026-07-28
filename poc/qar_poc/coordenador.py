# -*- coding: utf-8 -*-
"""
coordenador.py — A entidade "Plano de Controle".

Papel na arquitetura: orquestrar todo o experimento de carga. Ele nao publica
nada; ele **coordena** quem publica. Responsabilidades:

  * montar a topologia: criar os sensores, agrupa-los por site e instanciar um
    Gateway por site;
  * iniciar os gateways com uma rampa suave (evita abrir todas as conexoes no
    mesmo instante);
  * agregar as metricas de todos os gateways e imprimir o painel ao vivo;
  * encerrar com elegancia (SIGINT/prazo) e emitir o relatorio final.

Dois modos de paralelismo (o segundo e opcional, ativado por --processos):

  1. THREADS (padrao): um Coordenador neste processo, um thread por gateway.
     Ideal para carga de I/O (MQTT solta o GIL durante a rede).

  2. MULTIPROCESSOS: os gateways sao repartidos (sharding por site) entre P
     processos independentes. Cada processo roda seu proprio conjunto de
     gateways e reporta metricas ao processo pai por uma fila (Queue). Isso usa
     varios nucleos da CPU para geracao de payload e distribui as conexoes,
     demonstrando escala horizontal e uma estrategia de comunicacao entre
     processos.
"""

from __future__ import annotations

import multiprocessing as mp
import signal
import sys
import threading
import time
from datetime import datetime, timezone

from .config import ConfigCarga
from .gateway import Gateway
from .metricas import MetricasConexao, agregar, percentil
from .sensor import Dispositivo
from .transporte import PAHO_DISPONIVEL


# ===========================================================================
# Topologia — construcao determinista de sensores e gateways
# ===========================================================================
def dispositivos_do_gateway(cfg: ConfigCarga, gid: int) -> list[Dispositivo]:
    """
    Sensores de UM gateway (site). A distribuicao e determinista: dado o mesmo
    cfg, o gateway `gid` sempre recebe exatamente os mesmos device_ids e seeds,
    tanto no modo threads quanto no modo multiprocessos.
    """
    base, resto = divmod(cfg.sensores, cfg.gateways)
    if gid < resto:
        inicio, qtd = gid * (base + 1), base + 1
    else:
        inicio, qtd = resto * (base + 1) + (gid - resto) * base, base

    site = f"{cfg.prefixo_site}-site-{gid:04d}"
    dispositivos = []
    for k in range(qtd):
        gindex = inicio + k
        dispositivos.append(
            Dispositivo(f"esp32-{gindex:06d}", site, seed=cfg.seed + gindex)
        )
    return dispositivos


def criar_gateways(
    cfg: ConfigCarga,
    parar,
    inicio_janela: float,
    filtro=None,
) -> list[Gateway]:
    """Cria os gateways cujo id passa por `filtro` (None = todos)."""
    gateways = []
    for gid in range(cfg.gateways):
        if filtro is not None and not filtro(gid):
            continue
        dispositivos = dispositivos_do_gateway(cfg, gid)
        if not dispositivos:
            continue
        gateways.append(
            Gateway(
                gateway_id=gid,
                dispositivos=dispositivos,
                params_base=cfg.params_base(),
                intervalo=cfg.intervalo,
                prob_degradar=cfg.prob_degradar,
                prefixo_client=cfg.prefixo_site,
                parar=parar,
                inicio_janela=inicio_janela,
                dry_run=cfg.dry_run,
            )
        )
    return gateways


def _iniciar_com_rampa(gateways: list[Gateway]) -> None:
    """Sobe os gateways de forma escalonada para nao abrir tudo de uma vez."""
    atraso = min(0.02, 2.0 / max(1, len(gateways)))
    for gw in gateways:
        gw.start()
        if atraso:
            time.sleep(atraso)


# ===========================================================================
# Painel de metricas
# ===========================================================================
_CAB = (f"{'t(s)':>6} {'conn':>6} {'enviadas':>12} {'msg/s':>10} "
        f"{'falhas':>8} {'bp':>7} {'p50':>7} {'p95':>7} {'p99':>8}")


def _imprimir_cabecalho() -> None:
    print("\n" + _CAB)
    print("-" * len(_CAB))


def _fmt(n) -> str:
    return f"{n:,}".replace(",", ".")


def _imprimir_linha(t, conn, total_conn, enviadas, taxa, falhas, bp, p50, p95, p99) -> None:
    print(f"{t:6.0f} {conn:>3}/{total_conn:<2} {enviadas:12,d} {taxa:10,.0f} "
          f"{falhas:8,d} {bp:7,d} {p50:7.1f} {p95:7.1f} {p99:8.1f}"
          .replace(",", "."))


# ===========================================================================
# Coordenador local (modo threads)
# ===========================================================================
class Coordenador:
    """Orquestra os gateways deste processo (um thread por gateway)."""

    def __init__(self, cfg: ConfigCarga):
        self.cfg = cfg
        self.parar = threading.Event()
        self.gateways: list[Gateway] = []

    def _instalar_sinais(self) -> None:
        def _sinal(signum, frame):
            print("\n[sinal] encerrando com elegancia...", file=sys.stderr)
            self.parar.set()

        signal.signal(signal.SIGINT, _sinal)
        try:
            signal.signal(signal.SIGTERM, _sinal)
        except (ValueError, AttributeError):
            pass

    def rodar_local(self) -> int:
        cfg = self.cfg
        self._instalar_sinais()
        inicio_janela = time.monotonic()
        self.gateways = criar_gateways(cfg, self.parar, inicio_janela)
        _iniciar_com_rampa(self.gateways)

        conexoes = [gw.metricas for gw in self.gateways]
        t0 = time.monotonic()
        prazo = t0 + cfg.duracao if cfg.duracao > 0 else None
        ultimo_total, ultimo_t = 0, t0
        lat_acumulada: list[float] = []

        _imprimir_cabecalho()
        try:
            while not self.parar.is_set():
                self.parar.wait(timeout=cfg.periodo_reporte)
                agora = time.monotonic()

                lat_janela: list[float] = []
                for gw in self.gateways:
                    lat_janela.extend(gw.metricas.coletar_latencias())
                lat_acumulada.extend(lat_janela)

                snap = agregar(conexoes, lat_janela)
                dt = max(agora - ultimo_t, 1e-6)
                taxa = (snap.publicadas - ultimo_total) / dt
                ultimo_total, ultimo_t = snap.publicadas, agora

                _imprimir_linha(agora - t0, snap.conectados, snap.total_conexoes,
                                snap.publicadas, taxa, snap.falhas, snap.backpressure,
                                snap.lat_p50, snap.lat_p95, snap.lat_p99)

                if prazo is not None and agora >= prazo:
                    self.parar.set()
                    break
        finally:
            self.parar.set()
            for gw in self.gateways:
                gw.join(timeout=5.0)

        return relatorio_final(cfg, conexoes, time.monotonic() - t0, lat_acumulada)


# ===========================================================================
# Modo multiprocessos — sharding de gateways por processo
# ===========================================================================
def rodar_shard_processo(cfg: ConfigCarga, indice: int, fila: "mp.Queue", parar_mp) -> None:
    """
    Alvo de cada processo filho. Roda os gateways cujo id satisfaz
    `gid % cfg.processos == indice` e empurra snapshots de metricas para a fila.
    """
    # O filho ignora Ctrl+C: quem coordena o encerramento e o pai, via parar_mp.
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    inicio_janela = time.monotonic()
    gateways = criar_gateways(
        cfg, parar_mp, inicio_janela, filtro=lambda gid: gid % cfg.processos == indice
    )
    _iniciar_com_rampa(gateways)
    conexoes = [gw.metricas for gw in gateways]

    cadencia = min(1.0, cfg.periodo_reporte / 2.0)
    try:
        while not parar_mp.is_set():
            time.sleep(cadencia)
            lat = []
            for gw in gateways:
                lat.extend(gw.metricas.coletar_latencias())
            snap = agregar(conexoes, list(lat))
            fila.put({
                "shard": indice,
                "publicadas": snap.publicadas,
                "falhas": snap.falhas,
                "backpressure": snap.backpressure,
                "conectados": snap.conectados,
                "total_conexoes": snap.total_conexoes,
                "latencias": lat[:500],  # amostra limitada para a fila
                "final": False,
            })
    finally:
        parar_mp.set()
        for gw in gateways:
            gw.join(timeout=5.0)
        lat = []
        for gw in gateways:
            lat.extend(gw.metricas.coletar_latencias())
        snap = agregar(conexoes, list(lat))
        fila.put({
            "shard": indice,
            "publicadas": snap.publicadas,
            "falhas": snap.falhas,
            "backpressure": snap.backpressure,
            "conectados": snap.conectados,
            "total_conexoes": snap.total_conexoes,
            "latencias": lat[:2000],
            "final": True,
        })


def rodar_multiprocessos(cfg: ConfigCarga) -> int:
    """Processo pai: cria os shards, agrega a fila e imprime o painel unificado."""
    ctx = mp.get_context("spawn")
    fila: "mp.Queue" = ctx.Queue()
    parar_mp = ctx.Event()

    processos = [
        ctx.Process(target=rodar_shard_processo, args=(cfg, i, fila, parar_mp),
                    name=f"shard-{i}", daemon=False)
        for i in range(cfg.processos)
    ]

    def _sinal(signum, frame):
        print("\n[sinal] encerrando com elegancia...", file=sys.stderr)
        parar_mp.set()

    signal.signal(signal.SIGINT, _sinal)
    try:
        signal.signal(signal.SIGTERM, _sinal)
    except (ValueError, AttributeError):
        pass

    for p in processos:
        p.start()

    t0 = time.monotonic()
    prazo = t0 + cfg.duracao if cfg.duracao > 0 else None
    ultimo_por_shard: dict[int, dict] = {}
    finais: dict[int, dict] = {}
    lat_janela: list[float] = []
    lat_total: list[float] = []
    ultimo_total, ultimo_t = 0, t0

    _imprimir_cabecalho()
    try:
        while not parar_mp.is_set():
            time.sleep(cfg.periodo_reporte)
            # Drena tudo que os shards enviaram desde o ultimo tick.
            while True:
                try:
                    msg = fila.get_nowait()
                except Exception:
                    break
                ultimo_por_shard[msg["shard"]] = msg
                if msg.get("final"):
                    finais[msg["shard"]] = msg
                lat_janela.extend(msg.get("latencias", []))

            agora = time.monotonic()
            total = sum(m["publicadas"] for m in ultimo_por_shard.values())
            falhas = sum(m["falhas"] for m in ultimo_por_shard.values())
            bp = sum(m["backpressure"] for m in ultimo_por_shard.values())
            conn = sum(m["conectados"] for m in ultimo_por_shard.values())
            total_conn = sum(m["total_conexoes"] for m in ultimo_por_shard.values())

            lat_total.extend(lat_janela)
            if len(lat_total) > 50000:
                del lat_total[:25000]
            p50 = p95 = p99 = 0.0
            if lat_janela:
                lat_janela.sort()
                p50, p95, p99 = (percentil(lat_janela, 50),
                                 percentil(lat_janela, 95),
                                 percentil(lat_janela, 99))
            lat_janela = []

            dt = max(agora - ultimo_t, 1e-6)
            taxa = (total - ultimo_total) / dt
            ultimo_total, ultimo_t = total, agora
            _imprimir_linha(agora - t0, conn, total_conn, total, taxa,
                            falhas, bp, p50, p95, p99)

            if prazo is not None and agora >= prazo:
                parar_mp.set()
                break
    finally:
        parar_mp.set()
        # Aguarda os relatorios finais dos shards.
        fim = time.monotonic() + 6.0
        while len(finais) < cfg.processos and time.monotonic() < fim:
            try:
                msg = fila.get(timeout=0.5)
            except Exception:
                continue
            ultimo_por_shard[msg["shard"]] = msg
            if msg.get("final"):
                finais[msg["shard"]] = msg
            lat_total.extend(msg.get("latencias", []))
        for p in processos:
            p.join(timeout=5.0)

    fonte = finais if finais else ultimo_por_shard
    total = sum(m["publicadas"] for m in fonte.values())
    falhas = sum(m["falhas"] for m in fonte.values())
    bp = sum(m["backpressure"] for m in fonte.values())
    return _relatorio_final_valores(cfg, total, falhas, bp,
                                    time.monotonic() - t0, lat_total)


# ===========================================================================
# Relatorio final
# ===========================================================================
def relatorio_final(cfg, conexoes: list[MetricasConexao], decorrido, latencias) -> int:
    total = sum(m.publicadas for m in conexoes)
    falhas = sum(m.falhas for m in conexoes)
    bp = sum(m.backpressure for m in conexoes)
    return _relatorio_final_valores(cfg, total, falhas, bp, decorrido, latencias)


def _relatorio_final_valores(cfg, total, falhas, bp, decorrido, latencias) -> int:
    vazao = total / decorrido if decorrido > 0 else 0.0
    print("\n" + "=" * 70)
    print(" Relatorio final")
    print("=" * 70)
    print(f"  modo ................. {'multiprocessos (%d)' % cfg.processos if cfg.processos > 1 else 'threads'}")
    print(f"  duracao efetiva ...... {decorrido:.1f} s")
    print(f"  mensagens publicadas . {_fmt(total)}")
    print(f"  vazao media .......... {vazao:,.1f} msg/s".replace(",", "."))
    print(f"  falhas ............... {_fmt(falhas)}")
    print(f"  backpressure (fila) .. {_fmt(bp)}")
    if latencias:
        latencias.sort()
        print(f"  latencia PUBACK (ms) . p50={percentil(latencias,50):.1f} "
              f"p95={percentil(latencias,95):.1f} "
              f"p99={percentil(latencias,99):.1f} max={latencias[-1]:.1f}")
    print("=" * 70)

    if cfg.relatorio:
        import json

        dados = {
            "gerado_em": datetime.now(timezone.utc).isoformat(),
            "config": {
                "host": cfg.host, "porta": cfg.porta, "sensores": cfg.sensores,
                "gateways": cfg.gateways, "processos": cfg.processos,
                "intervalo_s": cfg.intervalo, "qos": cfg.qos, "tls": cfg.tls,
                "dry_run": cfg.dry_run,
            },
            "resultado": {
                "duracao_s": round(decorrido, 2), "publicadas": total,
                "vazao_media_msg_s": round(vazao, 2), "falhas": falhas,
                "backpressure": bp,
                "taxa_alvo_msg_s": round(cfg.sensores / cfg.intervalo, 2),
            },
            "latencia_puback_ms": (
                {
                    "p50": round(percentil(latencias, 50), 2),
                    "p95": round(percentil(latencias, 95), 2),
                    "p99": round(percentil(latencias, 99), 2),
                    "max": round(latencias[-1], 2), "amostras": len(latencias),
                } if latencias else None
            ),
        }
        with open(cfg.relatorio, "w", encoding="utf-8") as fh:
            json.dump(dados, fh, ensure_ascii=False, indent=2)
        print(f"  relatorio salvo em: {cfg.relatorio}")
    return 0


# ===========================================================================
# Dispatcher
# ===========================================================================
def executar(cfg: ConfigCarga) -> int:
    """Ponto de entrada: escolhe o modo (threads x multiprocessos) e roda."""
    if not cfg.dry_run and not PAHO_DISPONIVEL:
        print("ERRO: paho-mqtt nao esta instalado. Rode 'pip install -r "
              "requirements.txt' ou use --dry-run.", file=sys.stderr)
        return 2

    _imprimir_resumo(cfg)
    if cfg.processos > 1 and not cfg.dry_run:
        return rodar_multiprocessos(cfg)
    if cfg.processos > 1 and cfg.dry_run:
        print("[aviso] --dry-run usa apenas threads; ignorando --processos.\n",
              file=sys.stderr)
    return Coordenador(cfg).rodar_local()


def _imprimir_resumo(cfg: ConfigCarga) -> None:
    print("=" * 70)
    print(" Gerador de carga MQTT - PoC de ingestao (Atividade 3)")
    print("=" * 70)
    modo = "DRY-RUN (sem broker)" if cfg.dry_run else f"{cfg.host}:{cfg.porta}"
    print(f"  destino .............. {modo}")
    print(f"  sensores ............. {_fmt(cfg.sensores)}")
    print(f"  gateways (sites/conn)  {cfg.gateways}")
    par = f"multiprocessos ({cfg.processos})" if cfg.processos > 1 else "threads"
    print(f"  paralelismo .......... {par}")
    print(f"  intervalo ............ {cfg.intervalo:g} s por sensor")
    print(f"  QoS .................. {cfg.qos}   TLS: {'sim' if cfg.tls else 'nao'}")
    alvo = cfg.sensores / cfg.intervalo
    print(f"  taxa alvo ............ {alvo:,.1f} msg/s (pico 2x ~ {alvo*2:,.1f})"
          .replace(",", "."))
    dur = f"{cfg.duracao:g} s" if cfg.duracao > 0 else "continua (Ctrl+C encerra)"
    print(f"  duracao .............. {dur}")
    print("=" * 70)
