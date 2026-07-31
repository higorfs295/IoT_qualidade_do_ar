// Wi-Fi + MQTT QoS 1 + serializacao do contrato v1.1.
#include "publicador_mqtt.h"
#include "../config.h"
#include "../contrato.h"
#include <Arduino.h>
#include <ArduinoJson.h>
#include <MQTT.h>
#include <WiFi.h>
#include <time.h>

#ifdef MQTT_TLS
#include <WiFiClientSecure.h>
static WiFiClientSecure rede;
#else
static WiFiClient rede;
#endif

static MQTTClient mqtt(1024);

// ULID canonico: 48 bits de timestamp em ms + 80 bits aleatorios, codificados
// em Crockford Base32. Os dois bits mais altos dos 130 bits de texto sao zero.
static String gerarUlid() {
  static const char* B32 = "0123456789ABCDEFGHJKMNPQRSTVWXYZ";
  uint8_t bytes[16];
  uint64_t ms = static_cast<uint64_t>(time(nullptr)) * 1000ULL + millis() % 1000ULL;
  for (int i = 5; i >= 0; --i) { bytes[i] = ms & 0xFF; ms >>= 8; }
  esp_fill_random(bytes + 6, 10);

  char id[27];
  for (int grupo = 0; grupo < 26; ++grupo) {
    uint8_t valor = 0;
    for (int bit = 0; bit < 5; ++bit) {
      int pos = grupo * 5 + bit - 2;
      valor <<= 1;
      if (pos >= 0) valor |= (bytes[pos / 8] >> (7 - (pos % 8))) & 1;
    }
    id[grupo] = B32[valor];
  }
  id[26] = '\0';
  return String(id);
}

static String agoraRfc3339() {
  time_t agora = time(nullptr);
  struct tm tmUtc;
  gmtime_r(&agora, &tmUtc);
  char buf[25];
  strftime(buf, sizeof(buf), "%Y-%m-%dT%H:%M:%SZ", &tmUtc);
  return String(buf);
}

bool PublicadorMqtt::relogioValido() const {
  return time(nullptr) >= 1704067200;  // 2024-01-01 UTC
}

bool PublicadorMqtt::conectarWiFi() {
  if (WiFi.status() == WL_CONNECTED) return true;
  const unsigned long agora = millis();
  if (_ultimaTentativaWiFiMs && agora - _ultimaTentativaWiFiMs < MQTT_RECONNECT_MS)
    return false;
  _ultimaTentativaWiFiMs = agora;
  WiFi.disconnect(false, false);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  return false;  // conexao segue assincrona; manter() verificara depois
}

bool PublicadorMqtt::conectarBroker() {
  if (mqtt.connected()) return true;
  if (WiFi.status() != WL_CONNECTED) return false;
  const unsigned long agora = millis();
  if (_ultimaTentativaMqttMs && agora - _ultimaTentativaMqttMs < MQTT_RECONNECT_MS)
    return false;
  _ultimaTentativaMqttMs = agora;

  const char* user = strlen(MQTT_USER) ? MQTT_USER : nullptr;
  const char* pass = strlen(MQTT_PASS) ? MQTT_PASS : nullptr;
  bool ok = user ? mqtt.connect(DEVICE_ID, user, pass) : mqtt.connect(DEVICE_ID);
  if (ok) {
    String status = String(TOPICO_PREFIXO) + "/" + SITE_ID + "/" + DEVICE_ID + "/status";
    mqtt.publish(status, "online", true, MQTT_QOS);
  }
  return ok;
}

void PublicadorMqtt::iniciar() {
  WiFi.mode(WIFI_STA);
  WiFi.setHostname(DEVICE_ID);
  WiFi.setAutoReconnect(true);
#ifdef MQTT_TLS
  if (strlen(MQTT_CA_CERT) == 0) {
    Serial.println("[erro] MQTT_TLS ativo, mas MQTT_CA_CERT esta vazio");
  } else {
    rede.setCACert(MQTT_CA_CERT);
  }
#endif
  mqtt.begin(MQTT_HOST, MQTT_PORT, rede);
  mqtt.setOptions(MQTT_KEEPALIVE, true, 3000);
  String status = String(TOPICO_PREFIXO) + "/" + SITE_ID + "/" + DEVICE_ID + "/status";
  mqtt.setWill(status.c_str(), "offline", true, MQTT_QOS);

  conectarWiFi();
  configTime(0, 0, "pool.ntp.org", "time.google.com", "time.cloudflare.com");
  _bootId = gerarUlid();
}

void PublicadorMqtt::manter() {
  if (WiFi.status() != WL_CONNECTED) {
    conectarWiFi();
    return;
  }
  if (!mqtt.connected()) conectarBroker();
  mqtt.loop();
}

bool PublicadorMqtt::conectado() { return mqtt.connected(); }

bool PublicadorMqtt::publicar(const Leitura& l) {
  if (!mqtt.connected() || !relogioValido()) return false;

  JsonDocument doc;
  doc["schema_version"] = SCHEMA_VERSION_STR;
  doc["message_id"] = gerarUlid();
  doc["device_id"] = DEVICE_ID;
  doc["site_id"] = SITE_ID;
  doc["sent_at"] = agoraRfc3339();
  doc["sequence"] = ++_sequence;

  JsonObject m = doc["measurements"].to<JsonObject>();
  if (l.co2_ok) m["co2_ppm"] = l.co2_ppm; else m["co2_ppm"] = nullptr;
  if (l.voc_ok) m["voc_index"] = l.voc_index; else m["voc_index"] = nullptr;
  if (l.lpg_ok) m["lpg_ppm"] = l.lpg_ppm; else m["lpg_ppm"] = nullptr;
  if (l.gas_raw_ok) m["gas_raw_v"] = l.gas_raw_v;
  if (l.pm1_ok) m["pm1_ugm3"] = l.pm1_ugm3; else m["pm1_ugm3"] = nullptr;
  if (l.pm_ok) {
    m["pm25_ugm3"] = l.pm25_ugm3; m["pm10_ugm3"] = l.pm10_ugm3;
  } else {
    m["pm25_ugm3"] = nullptr; m["pm10_ugm3"] = nullptr;
  }
  if (l.th_ok) {
    m["temperature_c"] = l.temperature_c; m["humidity_pct"] = l.humidity_pct;
  } else {
    m["temperature_c"] = nullptr; m["humidity_pct"] = nullptr;
  }

  const char* gas = "SAFE";
  if (l.status == STATUS_ERROR) gas = "UNKNOWN";
  else if ((l.co2_ok && l.co2_ppm > LIMIAR_CO2_PPM) ||
           (l.voc_ok && l.voc_index > LIMIAR_VOC_INDEX) ||
           (l.lpg_ok && l.lpg_ppm > LIMIAR_LPG_PPM) ||
           (l.pm_ok && l.pm25_ugm3 > LIMIAR_PM25_UGM3)) gas = "UNSAFE";

  JsonObject q = doc["quality"].to<JsonObject>();
  q["gas_status"] = gas;
  q["sensor_status"] = l.status == STATUS_OK ? "OK"
                       : l.status == STATUS_DEGRADED ? "DEGRADED" : "ERROR";

  JsonObject meta = doc["metadata"].to<JsonObject>();
  meta["firmware_version"] = FIRMWARE_VERSION;
  meta["boot_id"] = _bootId;
  meta["rssi_dbm"] = WiFi.RSSI();
  meta["sensor_mode"] = MODO_SENSOR == FONTE_SIMULADA ? "HIL" : "PHYSICAL";

  char payload[1024];
  size_t n = serializeJson(doc, payload, sizeof(payload));
  if (n == 0 || n >= sizeof(payload)) return false;
  String topico = montarTopico(SITE_ID, DEVICE_ID);
  return mqtt.publish(topico.c_str(), payload, static_cast<int>(n), false, MQTT_QOS);
}
