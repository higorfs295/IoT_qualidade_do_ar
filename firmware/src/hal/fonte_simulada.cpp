// =============================================================================
//  fonte_simulada.cpp — implementacao da fonte SIMULADA (HIL)
// =============================================================================
#include "fonte_simulada.h"
#include <Arduino.h>
#include <ArduinoJson.h>   // requer ArduinoJson >= 7 (ver platformio.ini)

static bool numero(JsonVariantConst v) {
  return v.is<long>() || v.is<unsigned long>() || v.is<double>();
}

void FonteSimulada::iniciar() {
  _ultima.limpar();
  _len = 0;
  // A Serial ja foi iniciada no main (Serial.begin). Aqui nada de I2C/UART.
  // O PC escreve os quadros na RX; os logs do firmware saem pela TX — mesmo
  // cabo, direcoes independentes, sem colisao.
}

// Converte uma linha JSON em Leitura. Linha invalida e simplesmente descartada
// (o firmware nunca trava com lixo na serial).
void FonteSimulada::processarLinha(const char* linha) {
  JsonDocument doc;
  DeserializationError err = deserializeJson(doc, linha);
  if (err) return;
  if (strcmp(doc["t"] | "", "sensors") != 0) return;

  Leitura l;
  l.limpar();
  if (numero(doc["co2_ppm"])) {
    l.co2_ppm = doc["co2_ppm"].as<long>();
    l.co2_ok = l.co2_ppm >= 0 && l.co2_ppm <= 100000;
  }
  if (numero(doc["voc_index"])) {
    l.voc_index = doc["voc_index"].as<long>();
    l.voc_ok = l.voc_index >= 0 && l.voc_index <= 500;
  }
  if (numero(doc["lpg_ppm"])) {
    l.lpg_ppm = doc["lpg_ppm"].as<long>();
    l.lpg_ok = l.lpg_ppm >= 0 && l.lpg_ppm <= 1000000;
  }
  if (numero(doc["gas_raw_v"])) {
    l.gas_raw_v = doc["gas_raw_v"].as<float>();
    l.gas_raw_ok = isfinite(l.gas_raw_v) && l.gas_raw_v >= 0.0f && l.gas_raw_v <= 5.5f;
  }
  if (numero(doc["pm1_ugm3"])) {
    l.pm1_ugm3 = doc["pm1_ugm3"].as<float>();
    l.pm1_ok = isfinite(l.pm1_ugm3) && l.pm1_ugm3 >= 0.0f && l.pm1_ugm3 <= 10000.0f;
  }
  if (numero(doc["pm25_ugm3"]) && numero(doc["pm10_ugm3"])) {
    l.pm25_ugm3 = doc["pm25_ugm3"].as<float>();
    l.pm10_ugm3 = doc["pm10_ugm3"].as<float>();
    l.pm_ok = isfinite(l.pm25_ugm3) && isfinite(l.pm10_ugm3) &&
      l.pm25_ugm3 >= 0.0f && l.pm25_ugm3 <= 10000.0f &&
      l.pm10_ugm3 >= 0.0f && l.pm10_ugm3 <= 10000.0f;
  }
  if (numero(doc["temperature_c"]) && numero(doc["humidity_pct"])) {
    l.temperature_c = doc["temperature_c"].as<float>();
    l.humidity_pct = doc["humidity_pct"].as<float>();
    l.th_ok = isfinite(l.temperature_c) && isfinite(l.humidity_pct) &&
      l.temperature_c >= -50.0f && l.temperature_c <= 100.0f &&
      l.humidity_pct >= 0.0f && l.humidity_pct <= 100.0f;
  }
  l.sequence = doc["seq"] | 0UL;
  bool completa = l.co2_ok && l.voc_ok && l.lpg_ok && l.pm1_ok && l.pm_ok && l.th_ok;
  l.status = completa ? STATUS_OK : STATUS_DEGRADED;
  l.recente = true;

  _ultima = l;
  _ultimoQuadroMs = millis();
  _recebeuAlgum = true;
}

bool FonteSimulada::atualizar(Leitura& out) {
  // Consome tudo que houver na serial montando linhas (nao bloqueia).
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '\n' || c == '\r') {
      if (_len > 0) {
        _buf[_len] = '\0';
        processarLinha(_buf);
        _len = 0;
      }
    } else if (_len < LINHA_MAX - 1) {
      _buf[_len++] = c;
    } else {
      _len = 0;  // linha longa demais: descarta para nao estourar o buffer
    }
  }

  if (!_recebeuAlgum) {
    out = _ultima;  // ainda sem nenhum quadro
    return false;
  }

  // Heartbeat: classifica o frescor da ultima leitura.
  unsigned long dt = millis() - _ultimoQuadroMs;
  if (dt > TIMEOUT_SENSOR_MS * 2) {
    _ultima.status = STATUS_ERROR;
    _ultima.recente = false;
  } else if (dt > TIMEOUT_SENSOR_MS) {
    _ultima.status = STATUS_DEGRADED;
    _ultima.recente = false;
  } else {
    const bool completa = _ultima.co2_ok && _ultima.voc_ok && _ultima.lpg_ok &&
      _ultima.pm1_ok && _ultima.pm_ok && _ultima.th_ok;
    _ultima.status = completa ? STATUS_OK : STATUS_DEGRADED;
    _ultima.recente = true;
  }
  out = _ultima;
  return _ultima.recente;
}
