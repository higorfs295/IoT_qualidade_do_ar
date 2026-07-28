// =============================================================================
//  fonte_simulada.cpp — implementacao da fonte SIMULADA (HIL)
// =============================================================================
#include "fonte_simulada.h"
#include <Arduino.h>
#include <ArduinoJson.h>   // requer ArduinoJson >= 7 (ver platformio.ini)

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
  if (doc["co2_ppm"].is<long>() || doc["co2_ppm"].is<double>()) {
    l.co2_ppm = doc["co2_ppm"].as<long>(); l.co2_ok = true;
  }
  if (doc["voc_index"].is<long>() || doc["voc_index"].is<double>()) {
    l.voc_index = doc["voc_index"].as<long>(); l.voc_ok = true;
  }
  if (doc["lpg_ppm"].is<long>() || doc["lpg_ppm"].is<double>()) {
    l.lpg_ppm = doc["lpg_ppm"].as<long>(); l.lpg_ok = true;
  }
  if (doc["pm1_ugm3"].is<double>() || doc["pm1_ugm3"].is<long>()) {
    l.pm1_ugm3 = doc["pm1_ugm3"].as<float>(); l.pm1_ok = true;
  }
  if (!doc["pm25_ugm3"].isNull() && !doc["pm10_ugm3"].isNull()) {
    l.pm25_ugm3 = doc["pm25_ugm3"].as<float>();
    l.pm10_ugm3 = doc["pm10_ugm3"].as<float>();
    l.pm_ok = true;
  }
  if (!doc["temperature_c"].isNull() && !doc["humidity_pct"].isNull()) {
    l.temperature_c = doc["temperature_c"].as<float>();
    l.humidity_pct = doc["humidity_pct"].as<float>();
    l.th_ok = true;
  }
  l.sequence = doc["seq"] | 0UL;
  l.status = STATUS_OK;
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
    _ultima.status = STATUS_OK;
    _ultima.recente = true;
  }
  out = _ultima;
  return _ultima.recente;
}
