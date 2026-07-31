#pragma once

// Copie para `secrets.h` e ajuste. `secrets.h` e ignorado pelo Git.
#define WIFI_SSID "<SSID_DA_REDE>"
#define WIFI_PASS "<SENHA_DO_WIFI>"

#define MQTT_HOST "192.168.0.10"
#define MQTT_PORT 1883
#define MQTT_USER ""
#define MQTT_PASS ""

// Para TLS, use a porta 8883, defina MQTT_TLS em config.h e cole a CA que
// assinou o certificado do broker. Nunca use setInsecure() em producao.
#define MQTT_CA_CERT ""
