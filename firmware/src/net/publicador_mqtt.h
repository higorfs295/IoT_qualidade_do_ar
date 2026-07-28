// =============================================================================
//  publicador_mqtt.h — Publica a Leitura como telemetria v1.1 no broker
// =============================================================================
//
//  Encapsula Wi-Fi + MQTT (PubSubClient). Recebe uma Leitura (venha ela da
//  fonte simulada ou fisica — nao importa) e a serializa no contrato v1.1,
//  publicando no topico do dispositivo com QoS configurado. Inclui Last Will
//  & Testament (LWT) para o broker saber quando o dispositivo cai.
// =============================================================================
#pragma once
#include "../hal/leitura.h"

class PublicadorMqtt {
 public:
  void iniciar();
  void manter();                 // chamar no loop(): reconecta e faz mqtt.loop()
  bool publicar(const Leitura& l);
  bool conectado();

 private:
  bool conectarWiFi();
  bool conectarBroker();
  uint32_t _sequence = 0;        // sequencia crescente por dispositivo
};
