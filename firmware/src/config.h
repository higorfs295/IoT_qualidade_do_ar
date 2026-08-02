// =============================================================================
//  config.h — Configuracao central do firmware da estacao (base_final)
//  Projeto: Monitoramento de Qualidade do Ar
// =============================================================================
//
// O ambiente do PlatformIO seleciona HIL ou sensores fisicos. Credenciais
// ficam em include/secrets.h, nunca neste arquivo versionado.
// =============================================================================
#pragma once

// -----------------------------------------------------------------------------
// Modo da fonte de sensores (Strategy) — TROQUE AQUI
// -----------------------------------------------------------------------------
#define FONTE_SIMULADA 0   // le NDJSON da central_sensores.py pela Serial/USB
#define FONTE_FISICA   1   // le os sensores reais (I2C/UART/ADC)

#ifndef MODO_SENSOR
#define MODO_SENSOR FONTE_SIMULADA
#endif

#if __has_include("secrets.h")
#include "secrets.h"
#else
#include "secrets.example.h"
#endif

#ifndef MQTT_CLIENT_CERT
#define MQTT_CLIENT_CERT ""
#endif
#ifndef MQTT_PRIVATE_KEY
#define MQTT_PRIVATE_KEY ""
#endif

// -----------------------------------------------------------------------------
// Identidade do dispositivo (entra no topico e no payload v1.1)
// -----------------------------------------------------------------------------
#ifndef DEVICE_ID
#define DEVICE_ID        "esp32-proto-01"
#endif
#ifndef SITE_ID
#define SITE_ID          "campus-ufg-bloco-inf"
#endif
#define FIRMWARE_VERSION "1.2.0"
#define BOARD_MODEL      "ESP-WROOM-32 DevKit 30P USB-C"
#define HARDWARE_REVISION "PROTO-REV-A"

// -----------------------------------------------------------------------------
// MQTT (broker Mosquitto local ou AWS IoT Core no ambiente esp32-aws)
// -----------------------------------------------------------------------------
#define MQTT_KEEPALIVE  60
#define MQTT_QOS        1
#define MQTT_RECONNECT_MS 5000UL
#define MQTT_BUFFER_SIZE 896
#define MQTT_PAYLOAD_MAX 896
#define MQTT_TOPIC_MAX   160
#define MIN_FREE_HEAP_BYTES 30000UL
// #define MQTT_TLS                       // descomente p/ TLS 8883 (carregar CA)

// -----------------------------------------------------------------------------
// Ritmo de publicacao (contrato: 1 leitura consolidada por sensor a cada 60 s)
// -----------------------------------------------------------------------------
#ifndef INTERVALO_PUBLICACAO_MS
#define INTERVALO_PUBLICACAO_MS 60000UL
#endif

// -----------------------------------------------------------------------------
// Elo HIL (modo simulado) — Serial/USB
// -----------------------------------------------------------------------------
#define SERIAL_BAUD        115200
// Sem quadro por este tempo => a leitura vira DEGRADED e depois ERROR (nunca
// dado velho silencioso). E o "heartbeat" do enlace serial.
#define TIMEOUT_SENSOR_MS  10000UL
// Tamanho maximo de uma linha NDJSON aceita (protege a memoria).
#define LINHA_MAX          512

// -----------------------------------------------------------------------------
// Pinos fisicos do DevKit 30P ESP-WROOM-32 informado pelo usuario.
// Ver docs/PINOUT_ESP32_WROOM32_30P.md. Nenhum pino de strapping e usado.
// -----------------------------------------------------------------------------
#define I2C_SDA       21   // SHT31 (0x44), SGP40 (0x59), SCD41 (0x62)
#define I2C_SCL       22
#define PMS_UART_RX   16   // ESP32 RX  <- PMS7003 TX
#define PMS_UART_TX   17   // ESP32 TX  -> PMS7003 RX
#define MICS_ADC_PIN  34   // MiCS-5524 VOUT (GPIO34 = ADC1, so entrada)
// A entrada analogica passa pelo divisor 15k/10k da Rev A (ganho 0,4).
// Multiplique a tensao no ADC por 2,5 para estimar a tensao antes do divisor.
#define MICS_DIVISOR  2.5f
#define MICS_AMOSTRAS_ADC 32

#define PINO_STRAPPING(p) ((p) == 0 || (p) == 2 || (p) == 5 || (p) == 12 || (p) == 15)
#if PINO_STRAPPING(I2C_SDA) || PINO_STRAPPING(I2C_SCL) || \
    PINO_STRAPPING(PMS_UART_RX) || PINO_STRAPPING(PMS_UART_TX)
#error "Pino de strapping selecionado; nao o use nestas interfaces"
#endif

// O MiCS-5524 nao fornece ppm diretamente. Sem uma curva obtida para o modulo,
// carga e gas-alvo usados, o firmware publica apenas gas_raw_v e mantem
// lpg_ppm=null. Veja docs/ROADMAP_HARDWARE_EASYEDA.md.
#define MICS_LPG_CALIBRADO 0

// -----------------------------------------------------------------------------
// Limiares de qualidade do ar (derivam o gas_status; ver contrato)
// -----------------------------------------------------------------------------
#define LIMIAR_CO2_PPM    1000
#define LIMIAR_VOC_INDEX  250
#define LIMIAR_LPG_PPM    100
#define LIMIAR_PM25_UGM3  35.0f
