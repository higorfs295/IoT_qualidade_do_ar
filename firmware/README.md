# Firmware — Estação de Qualidade do Ar (ESP32)

Firmware do protótipo real, com **camada de abstração de hardware (HAL)** e o
padrão **Strategy** para alternar entre sensores **simulados** (Hardware-in-the-
Loop, via `central_sensores.py` pela USB) e **físicos** (I2C/UART/ADC) trocando
**uma única linha** de configuração. Ver o blueprint completo em
[`../BASE_FINAL.md`](../BASE_FINAL.md).

> ⚠️ **Cautela (leia antes de flashar):** este firmware é um **esqueleto
> cuidadosamente estruturado** — pinos, endereços I2C, uso de bibliotecas e
> arquitetura estão corretos, **mas ele não foi compilado nem flashado aqui**.
> Compile e valide no seu ambiente (PlatformIO/Arduino), sensor a sensor. É a
> mesma convenção do seu firmware do IoT-IDEA.

## Estrutura

```text
firmware/
├── platformio.ini          # placa, libs (ArduinoJson, PubSubClient), flags
└── src/
    ├── config.h            # ⇦ MODO_SENSOR (SIMULADO/FÍSICO), pinos, Wi-Fi/MQTT
    ├── contrato.h          # nomes de campos e tópico (espelha o Python v1.1)
    ├── main.cpp            # orquestra: escolhe a fonte, lê, publica
    ├── hal/
    │   ├── leitura.h           # struct Leitura (dado unificado)
    │   ├── fonte_sensores.h    # interface FonteSensores (o Strategy)
    │   ├── fonte_simulada.*    # lê NDJSON da USB e preenche Leitura (HIL)
    │   └── fonte_fisica.*      # lê sensores reais (esqueleto + TODOs)
    └── net/
        └── publicador_mqtt.*   # Wi-Fi + MQTT + serialização v1.1
```

## Como a troca simulado ↔ físico funciona

Em `src/config.h`:

```c
#define MODO_SENSOR FONTE_SIMULADA   // desenvolvimento (HIL pela USB)
// #define MODO_SENSOR FONTE_FISICA  // protótipo com sensores reais
```

O `main.cpp` só conhece a interface `FonteSensores`; ele **não sabe** qual
implementação está ativa. Toda a aplicação (montar telemetria, publicar em
MQTT) permanece idêntica nos dois modos.

## Fluxo de desenvolvimento (HIL) — passo a passo

1. Ajuste Wi-Fi/MQTT em `src/config.h` (aponte `MQTT_HOST` para o seu broker
   Mosquitto — ver [`../infra/server_config`](../infra/server_config)).
2. Deixe `MODO_SENSOR FONTE_SIMULADA`.
3. Compile e grave: `pio run -t upload` (ou pela Arduino IDE).
4. No PC, alimente o ESP32 com dados simulados pela mesma porta USB:
   ```bash
   python ../simulador/central_sensores.py --porta COM5 --cenario auto
   ```
5. Observe o ESP32 publicar no broker; valide com o `sink` da PoC:
   ```bash
   python ../poc/consumidor_metricas.py --host localhost
   ```

## Sensores (modo físico)

| Grandeza | Módulo | Barramento | Endereço/Pino |
|---|---|---|---|
| CO₂ | SCD41 | I2C | `0x62` |
| Temp/Umidade | SHT31-D | I2C | `0x44` |
| VOC | SGP40 | I2C | `0x59` |
| Partículas | PMS7003 | UART2 | RX=16, TX=17 |
| GLP | MiCS-5524 | ADC | GPIO34 |

Ao montar o protótipo: habilite as bibliotecas em `platformio.ini`, preencha os
`ler*()` em `hal/fonte_fisica.cpp` e **calibre** cada sensor (em especial o
MiCS-5524, que tem aquecedor e curva própria).

## Notas de robustez e limitações

- **Heartbeat do elo serial:** sem quadro por `TIMEOUT_SENSOR_MS`, a leitura
  vira `DEGRADED` e depois `ERROR` — nunca dado velho silencioso.
- **`message_id`** é um pseudo-ULID (tempo + aleatório) — cumpre a idempotência.
- **`sent_at`** exige **NTP** (o firmware chama `configTime`); sem rede/hora, a
  data sai incorreta.
- **QoS:** o `PubSubClient` publica em **QoS 0**; o contrato pede **QoS 1**. Para
  QoS 1 de saída real, avalie uma lib MQTT assíncrona numa evolução (nota em
  `publicador_mqtt.cpp`).
- **TLS:** defina `MQTT_TLS` e carregue a CA para o listener 8883.
