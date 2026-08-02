// =============================================================================
//  publicador_mqtt.h — Publica a Leitura como telemetria v1.1 no broker
// =============================================================================
//
//  Encapsula Wi-Fi + MQTT QoS 1. Recebe uma Leitura (venha ela da
//  fonte simulada ou fisica — nao importa) e a serializa no contrato v1.1,
//  publicando no topico do dispositivo com QoS configurado. Inclui Last Will
//  & Testament (LWT) para o broker saber quando o dispositivo cai.
// =============================================================================
#pragma once
#include <Arduino.h>
#include "../config.h"
#include "../hal/leitura.h"

class PublicadorMqtt {
 public:
  void iniciar();
  void manter();                 // chamar no loop(): reconecta e faz mqtt.loop()
  bool publicar(const Leitura& l); // true = enviado ou preservado na fila fixa
  bool conectado();
  uint8_t pendentes() const { return _filaQuantidade; }
  uint32_t descartadas() const { return _filaDescartadas; }

 private:
  struct MensagemPendente {
    char payload[MQTT_PAYLOAD_MAX];
    uint16_t tamanho = 0;
  };

  bool conectarWiFi();
  bool conectarBroker();
  bool relogioValido() const;
  bool enfileirar(const char* dados, size_t tamanho);
  void descarregarFila();
  bool _tlsPronto = true;
  uint32_t _sequence = 0;        // sequencia crescente por dispositivo
  unsigned long _ultimaTentativaWiFiMs = 0;
  unsigned long _ultimaTentativaMqttMs = 0;
  char _bootId[27] = {0};
  MensagemPendente _fila[MQTT_OFFLINE_QUEUE_SIZE];
  uint8_t _filaInicio = 0;
  uint8_t _filaQuantidade = 0;
  uint32_t _filaDescartadas = 0;
};
