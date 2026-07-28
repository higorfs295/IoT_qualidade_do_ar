// =============================================================================
//  config.h — Configuracao central do firmware da estacao (base_final)
//  Projeto: Monitoramento de Qualidade do Ar
// =============================================================================
//
//  ESTE E O UNICO LUGAR que muda para alternar entre o modo SIMULADO (HIL, via
//  central_sensores.py pela USB) e o modo FISICO (sensores reais). Nenhuma
//  outra parte do codigo sabe qual fonte esta ativa — esse e o objetivo da HAL.
//
//  >>> CAUTELA: este firmware e um ESQUELETO cuidadosamente estruturado (pinos,
//      enderecos I2C e uso de bibliotecas corretos), porem NAO foi compilado
//      nem flashado aqui. Compile e valide no SEU ambiente (PlatformIO/Arduino),
//      ajustando bibliotecas e calibracao. Mesma convencao dos seus firmwares.
// =============================================================================
#pragma once

// -----------------------------------------------------------------------------
// Modo da fonte de sensores (Strategy) — TROQUE AQUI
// -----------------------------------------------------------------------------
#define FONTE_SIMULADA 0   // le NDJSON da central_sensores.py pela Serial/USB
#define FONTE_FISICA   1   // le os sensores reais (I2C/UART/ADC)

#ifndef MODO_SENSOR
#define MODO_SENSOR FONTE_SIMULADA   // <-- mude para FONTE_FISICA no protótipo real
#endif

// -----------------------------------------------------------------------------
// Identidade do dispositivo (entra no topico e no payload v1.1)
// -----------------------------------------------------------------------------
#define DEVICE_ID        "esp32-proto-01"
#define SITE_ID          "campus-ufg-bloco-inf"
#define FIRMWARE_VERSION "1.1.0"

// -----------------------------------------------------------------------------
// Wi-Fi
// -----------------------------------------------------------------------------
#define WIFI_SSID  "<SSID_DA_REDE>"
#define WIFI_PASS  "<SENHA_DO_WIFI>"

// -----------------------------------------------------------------------------
// MQTT (broker Mosquitto local; futuramente AWS IoT Core)
// -----------------------------------------------------------------------------
#define MQTT_HOST       "192.168.0.10"   // IP do broker na sua rede
#define MQTT_PORT       1883             // 1883 texto (PoC) / 8883 TLS (producao)
#define MQTT_USER       ""               // vazio = anonimo (PoC em rede isolada)
#define MQTT_PASS       ""
#define MQTT_KEEPALIVE  60
#define MQTT_QOS        1                // contrato: QoS 1
// #define MQTT_TLS                       // descomente p/ TLS 8883 (carregar CA)

// -----------------------------------------------------------------------------
// Ritmo de publicacao (contrato: 1 leitura consolidada por sensor a cada 60 s)
// -----------------------------------------------------------------------------
#define INTERVALO_PUBLICACAO_MS 60000UL

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
// Pinos fisicos (modo FONTE_FISICA) — ver mapa em BASE_FINAL.md §3
// -----------------------------------------------------------------------------
#define I2C_SDA       21   // SHT31 (0x44), SGP40 (0x59), SCD41 (0x62)
#define I2C_SCL       22
#define PMS_UART_RX   16   // ESP32 RX  <- PMS7003 TX
#define PMS_UART_TX   17   // ESP32 TX  -> PMS7003 RX
#define MICS_ADC_PIN  34   // MiCS-5524 VOUT (GPIO34 = ADC1, so entrada)
// O VOUT do MiCS (alimentado em 5 V) passa por um DIVISOR ÷2 (2x10k) antes do
// GPIO34, para nunca exceder 3.3 V. Multiplique a leitura por este fator para
// recuperar a tensao real. Ver hardware/pcb/README.md §2.3.
#define MICS_DIVISOR  2.0f
#define ADC_VREF      3.3f   // tensao de referencia efetiva do ADC (aprox.)

// -----------------------------------------------------------------------------
// Limiares de qualidade do ar (derivam o gas_status; ver contrato)
// -----------------------------------------------------------------------------
#define LIMIAR_CO2_PPM    1000
#define LIMIAR_VOC_INDEX  250
#define LIMIAR_LPG_PPM    100
#define LIMIAR_PM25_UGM3  35.0f
