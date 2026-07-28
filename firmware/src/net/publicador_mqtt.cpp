// =============================================================================
//  publicador_mqtt.cpp — Wi-Fi + MQTT + serializacao v1.1 (ESQUELETO)
// =============================================================================
#include "publicador_mqtt.h"
#include "../config.h"
#include "../contrato.h"
#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <time.h>

#ifdef MQTT_TLS
  #include <WiFiClientSecure.h>
  static WiFiClientSecure rede;
#else
  static WiFiClient rede;
#endif
static PubSubClient mqtt(rede);

// message_id pseudo-ULID: base36 do tempo + aleatorio. Nao e um ULID canonico,
// mas cumpre o papel de chave de idempotencia (unico por leitura).
static String gerarMessageId() {
  static const char* B36 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ";
  uint64_t t = (uint64_t)time(nullptr) * 1000ULL + (millis() % 1000ULL);
  char id[27];
  for (int i = 9; i >= 0; --i) { id[i] = B36[t % 36]; t /= 36; }
  for (int i = 10; i < 26; ++i) id[i] = B36[esp_random() % 36];
  id[26] = '\0';
  return String(id);
}

// sent_at em RFC 3339 UTC. Requer NTP sincronizado (ver iniciar()).
static String agoraRfc3339() {
  time_t agora = time(nullptr);
  struct tm tmUtc;
  gmtime_r(&agora, &tmUtc);
  char buf[25];
  strftime(buf, sizeof(buf), "%Y-%m-%dT%H:%M:%SZ", &tmUtc);
  return String(buf);
}

bool PublicadorMqtt::conectarWiFi() {
  if (WiFi.status() == WL_CONNECTED) return true;
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  unsigned long inicio = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - inicio < 15000) {
    delay(250);
    Serial.print('.');
  }
  return WiFi.status() == WL_CONNECTED;
}

bool PublicadorMqtt::conectarBroker() {
  if (mqtt.connected()) return true;
  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  mqtt.setKeepAlive(MQTT_KEEPALIVE);
#ifdef MQTT_TLS
  // rede.setCACert(CA_CERT);  // carregue a CA do broker para validar o servidor
#endif
  String topicoStatus = String(TOPICO_PREFIXO) + "/" + SITE_ID + "/" + DEVICE_ID + "/status";
  const char* user = strlen(MQTT_USER) ? MQTT_USER : nullptr;
  const char* pass = strlen(MQTT_PASS) ? MQTT_PASS : nullptr;
  // LWT: se o dispositivo cair, o broker publica "offline" nesse topico.
  bool ok = mqtt.connect(DEVICE_ID, user, pass,
                         topicoStatus.c_str(), MQTT_QOS, true, "offline");
  if (ok) {
    mqtt.publish(topicoStatus.c_str(), "online", true);
  }
  return ok;
}

void PublicadorMqtt::iniciar() {
  mqtt.setBufferSize(768);  // payload v1.1 cabe com folga
  conectarWiFi();
  // NTP para o sent_at em UTC (fuso 0). Ajuste os servidores se preciso.
  configTime(0, 0, "pool.ntp.org", "time.nist.gov");
  conectarBroker();
}

void PublicadorMqtt::manter() {
  if (WiFi.status() != WL_CONNECTED) conectarWiFi();
  if (!mqtt.connected()) conectarBroker();
  mqtt.loop();
}

bool PublicadorMqtt::conectado() { return mqtt.connected(); }

bool PublicadorMqtt::publicar(const Leitura& l) {
  if (!mqtt.connected()) return false;

  JsonDocument doc;
  doc["schema_version"] = SCHEMA_VERSION_STR;
  doc["message_id"] = gerarMessageId();
  doc["device_id"] = DEVICE_ID;
  doc["site_id"] = SITE_ID;
  doc["sent_at"] = agoraRfc3339();
  doc["sequence"] = ++_sequence;

  JsonObject m = doc["measurements"].to<JsonObject>();
  if (l.co2_ok) m["co2_ppm"] = l.co2_ppm;       else m["co2_ppm"] = nullptr;
  if (l.voc_ok) m["voc_index"] = l.voc_index;    else m["voc_index"] = nullptr;
  if (l.lpg_ok) m["lpg_ppm"] = l.lpg_ppm;        else m["lpg_ppm"] = nullptr;
  if (l.pm1_ok) m["pm1_ugm3"] = l.pm1_ugm3;      else m["pm1_ugm3"] = nullptr;
  if (l.pm_ok)  { m["pm25_ugm3"] = l.pm25_ugm3; m["pm10_ugm3"] = l.pm10_ugm3; }
  else          { m["pm25_ugm3"] = nullptr;     m["pm10_ugm3"] = nullptr; }
  if (l.th_ok)  { m["temperature_c"] = l.temperature_c; m["humidity_pct"] = l.humidity_pct; }
  else          { m["temperature_c"] = nullptr;         m["humidity_pct"] = nullptr; }

  // gas_status derivado dos limiares (ver config.h). ERROR => UNKNOWN.
  const char* gas = "SAFE";
  if (l.status == STATUS_ERROR) {
    gas = "UNKNOWN";
  } else if ((l.co2_ok && l.co2_ppm > LIMIAR_CO2_PPM) ||
             (l.voc_ok && l.voc_index > LIMIAR_VOC_INDEX) ||
             (l.lpg_ok && l.lpg_ppm > LIMIAR_LPG_PPM) ||
             (l.pm_ok && l.pm25_ugm3 > LIMIAR_PM25_UGM3)) {
    gas = "UNSAFE";
  }
  const char* sensorStatus = l.status == STATUS_OK ? "OK"
                           : l.status == STATUS_DEGRADED ? "DEGRADED" : "ERROR";
  JsonObject q = doc["quality"].to<JsonObject>();
  q["gas_status"] = gas;
  q["sensor_status"] = sensorStatus;

  JsonObject meta = doc["metadata"].to<JsonObject>();
  meta["firmware_version"] = FIRMWARE_VERSION;
  meta["rssi_dbm"] = WiFi.RSSI();

  char payload[768];
  size_t n = serializeJson(doc, payload, sizeof(payload));
  if (n == 0 || n >= sizeof(payload)) return false;  // nao coube: nao publica

  String topico = montarTopico(SITE_ID, DEVICE_ID);
  // PubSubClient::publish(topic, payload, retained) — QoS 0 no publish do
  // PubSubClient; para QoS 1 real, use um cliente MQTT com suporte a QoS de
  // saida (ex.: a lib Async MQTT) numa evolucao. O contrato pede QoS 1.
  return mqtt.publish(topico.c_str(), payload);
}
