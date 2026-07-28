# -*- coding: utf-8 -*-
"""
transporte.py — A entidade "Camada de Comunicacao" (uplink MQTT).

Papel na arquitetura: encapsular TODA a conversa com o broker (paho-mqtt) atras
de uma interface pequena: `conectar`, `publicar`, `desconectar`. O Gateway usa
essa camada sem saber detalhes de MQTT; se amanha o transporte virar HTTP ou
AMQP, so este arquivo muda.

Responsabilidades desta camada:
  * abrir e manter UMA conexao persistente (reaproveitada, sem reconectar por
    mensagem) com a sua propria thread de rede (loop_start do paho);
  * aplicar backpressure (inflight/fila) e traduzir o resultado de publish em
    contadores;
  * medir a latencia real de PUBACK (publish -> on_publish via `mid`);
  * atualizar o objeto MetricasConexao correspondente.
"""

from __future__ import annotations

import os
import sys
import threading
import time

from .metricas import MetricasConexao

try:
    import paho.mqtt.client as mqtt

    PAHO_DISPONIVEL = True
except ImportError:  # pragma: no cover
    mqtt = None
    PAHO_DISPONIVEL = False


class ParametrosConexao:
    """Tudo que a camada de transporte precisa para abrir a conexao."""

    __slots__ = (
        "host", "porta", "keepalive", "qos", "usuario", "senha",
        "tls", "tls_inseguro", "max_inflight", "max_fila", "client_id",
    )

    def __init__(self, host, porta, keepalive, qos, usuario, senha,
                 tls, tls_inseguro, max_inflight, max_fila, client_id):
        self.host = host
        self.porta = porta
        self.keepalive = keepalive
        self.qos = qos
        self.usuario = usuario
        self.senha = senha
        self.tls = tls
        self.tls_inseguro = tls_inseguro
        self.max_inflight = max_inflight
        self.max_fila = max_fila
        self.client_id = client_id


class ClienteMQTT:
    """Uma conexao MQTT persistente com medicao de latencia e backpressure."""

    def __init__(self, params: ParametrosConexao, metricas: MetricasConexao):
        self.p = params
        self.metricas = metricas
        self._cliente = None
        # mid -> timestamp de publicacao, para medir latencia de PUBACK.
        self._pendentes: dict[int, float] = {}
        self._pend_lock = threading.Lock()

    # ---- callbacks paho (assinaturas compativeis com v1 e v2) -----------
    def _on_connect(self, *args, **kwargs):
        self.metricas.conectado = True

    def _on_disconnect(self, *args, **kwargs):
        if self.metricas.conectado:
            self.metricas.reconexoes += 1
        self.metricas.conectado = False

    def _on_publish(self, client, userdata, mid, *args, **kwargs):
        agora = time.perf_counter()
        with self._pend_lock:
            t0 = self._pendentes.pop(mid, None)
        if t0 is not None:
            self.metricas.registrar_latencia((agora - t0) * 1000.0)

    # ---- ciclo de vida --------------------------------------------------
    def conectar(self) -> bool:
        """Abre a conexao e inicia a thread de rede. True se conectou."""
        try:
            cliente = mqtt.Client(
                mqtt.CallbackAPIVersion.VERSION2,
                client_id=self.p.client_id,
                clean_session=None,
                protocol=mqtt.MQTTv311,
            )
        except (AttributeError, TypeError):
            cliente = mqtt.Client(client_id=self.p.client_id, protocol=mqtt.MQTTv311)

        cliente.on_connect = self._on_connect
        cliente.on_disconnect = self._on_disconnect
        cliente.on_publish = self._on_publish
        # Backpressure explicito: limita inflight e tamanho de fila.
        cliente.max_inflight_messages_set(self.p.max_inflight)
        cliente.max_queued_messages_set(self.p.max_fila)
        # Reconexao automatica com recuo exponencial (1s..30s).
        cliente.reconnect_delay_set(min_delay=1, max_delay=30)

        if self.p.usuario:
            cliente.username_pw_set(self.p.usuario, self.p.senha)
        if self.p.tls:
            cliente.tls_set()  # usa a CA do sistema
            if self.p.tls_inseguro:
                cliente.tls_insecure_set(True)

        try:
            cliente.connect(self.p.host, self.p.porta, keepalive=self.p.keepalive)
        except Exception as exc:
            print(f"[transporte] falha ao conectar em "
                  f"{self.p.host}:{self.p.porta}: {exc}", file=sys.stderr)
            return False

        cliente.loop_start()  # thread de rede propria do paho
        self._cliente = cliente
        return True

    def publicar(self, topico: str, corpo: str) -> None:
        """Publica um payload ja serializado, atualizando as metricas."""
        try:
            info = self._cliente.publish(topico, corpo, qos=self.p.qos)
        except Exception:
            self.metricas.falhas += 1
            return

        rc = info.rc
        if rc == mqtt.MQTT_ERR_SUCCESS:
            self.metricas.publicadas += 1
            if self.p.qos > 0 and info.mid is not None:
                with self._pend_lock:
                    self._pendentes[info.mid] = time.perf_counter()
                    # Evita crescer sem limite se PUBACKs se perderem.
                    if len(self._pendentes) > self.p.max_fila * 2:
                        self._pendentes.clear()
        elif rc == mqtt.MQTT_ERR_QUEUE_SIZE:
            self.metricas.backpressure += 1
        else:
            self.metricas.falhas += 1
            self.metricas.conectado = self._cliente.is_connected()

    def desconectar(self) -> None:
        if self._cliente is not None:
            try:
                self._cliente.loop_stop()
                self._cliente.disconnect()
            except Exception:
                pass
            self._cliente = None


def client_id_gateway(prefixo: str, gateway_id: int) -> str:
    """Client id estavel e unico por gateway (inclui PID p/ multiprocessing)."""
    return f"gw-{prefixo}-{gateway_id:04d}-{os.getpid()}"
