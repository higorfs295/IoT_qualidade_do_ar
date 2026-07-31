#include "fonte_fisica.h"
#include <Arduino.h>
#include <Wire.h>

#if MODO_SENSOR == FONTE_FISICA
#include <Adafruit_SHT31.h>
#include <SensirionI2CSgp40.h>
#include <SensirionI2cScd4x.h>
#include <VOCGasIndexAlgorithm.h>

static Adafruit_SHT31 sht31;
static SensirionI2CSgp40 sgp40;
static SensirionI2cScd4x scd41;
static VOCGasIndexAlgorithm vocAlgorithm;

static uint16_t limitarTicks(float valor, float minimo, float maximo) {
  valor = constrain(valor, minimo, maximo);
  return static_cast<uint16_t>((valor - minimo) * 65535.0f / (maximo - minimo));
}

void FonteFisica::iniciar() {
  _ultima.limpar();
  Wire.begin(I2C_SDA, I2C_SCL);
  Wire.setClock(100000);

  _shtDisponivel = sht31.begin(0x44);

  sgp40.begin(Wire);
  uint16_t selfTest = 0;
  _sgpDisponivel = sgp40.executeSelfTest(selfTest) == 0 && selfTest == 0xD400;

  scd41.begin(Wire, SCD41_I2C_ADDR_62);
  delay(30);
  scd41.wakeUp();
  scd41.stopPeriodicMeasurement();
  scd41.reinit();
  _scdDisponivel = scd41.startPeriodicMeasurement() == 0;

  Serial2.begin(9600, SERIAL_8N1, PMS_UART_RX, PMS_UART_TX);
  analogReadResolution(12);
  analogSetPinAttenuation(MICS_ADC_PIN, ADC_11db);

  Serial.printf("[sensores] SHT31=%s SGP40=%s SCD41=%s\n",
                _shtDisponivel ? "ok" : "falha",
                _sgpDisponivel ? "ok" : "falha",
                _scdDisponivel ? "ok" : "falha");
}

bool FonteFisica::lerSHT31(Leitura& l) {
  if (!_shtDisponivel) return false;
  float t = sht31.readTemperature();
  float h = sht31.readHumidity();
  if (!isfinite(t) || !isfinite(h) || h < 0.0f || h > 100.0f) return false;
  l.temperature_c = t;
  l.humidity_pct = h;
  l.th_ok = true;
  _thMs = millis();
  return true;
}

bool FonteFisica::lerSGP40(Leitura& l) {
  if (!_sgpDisponivel) return false;
  const float t = l.th_ok ? l.temperature_c : 25.0f;
  const float h = l.th_ok ? l.humidity_pct : 50.0f;
  uint16_t sraw = 0;
  uint16_t rhTicks = limitarTicks(h, 0.0f, 100.0f);
  uint16_t tTicks = limitarTicks(t, -45.0f, 130.0f);
  if (sgp40.measureRawSignal(rhTicks, tTicks, sraw) != 0 || sraw == 0) return false;
  l.voc_index = static_cast<int32_t>(vocAlgorithm.process(sraw));
  l.voc_ok = l.voc_index >= 0 && l.voc_index <= 500;
  if (l.voc_ok) _vocMs = millis();
  return l.voc_ok;
}

bool FonteFisica::lerSCD41(Leitura& l) {
  if (!_scdDisponivel) return false;
  bool pronto = false;
  if (scd41.getDataReadyStatus(pronto) != 0 || !pronto) return false;
  uint16_t co2 = 0;
  float temperatura = 0.0f, umidade = 0.0f;
  if (scd41.readMeasurement(co2, temperatura, umidade) != 0 || co2 == 0) return false;
  l.co2_ppm = co2;
  l.co2_ok = true;
  _co2Ms = millis();
  return true;
}

bool FonteFisica::lerPMS7003(Leitura& l) {
  bool atualizou = false;
  while (Serial2.available() > 0) {
    uint8_t b = static_cast<uint8_t>(Serial2.read());
    if (_pmsIndex == 0 && b != 0x42) continue;
    if (_pmsIndex == 1 && b != 0x4D) {
      _pmsIndex = b == 0x42 ? 1 : 0;
      if (_pmsIndex == 1) _pmsBuf[0] = b;
      continue;
    }
    _pmsBuf[_pmsIndex++] = b;
    if (_pmsIndex < sizeof(_pmsBuf)) continue;
    _pmsIndex = 0;

    const uint16_t tamanho = (_pmsBuf[2] << 8) | _pmsBuf[3];
    uint16_t soma = 0;
    for (int i = 0; i < 30; ++i) soma += _pmsBuf[i];
    const uint16_t checksum = (_pmsBuf[30] << 8) | _pmsBuf[31];
    if (tamanho != 28 || soma != checksum) continue;

    l.pm1_ugm3 = static_cast<float>((_pmsBuf[10] << 8) | _pmsBuf[11]);
    l.pm25_ugm3 = static_cast<float>((_pmsBuf[12] << 8) | _pmsBuf[13]);
    l.pm10_ugm3 = static_cast<float>((_pmsBuf[14] << 8) | _pmsBuf[15]);
    l.pm1_ok = l.pm_ok = true;
    _pmMs = millis();
    atualizou = true;
  }
  return atualizou;
}

bool FonteFisica::lerMiCS5524(Leitura& l) {
  uint32_t somaMv = 0;
  for (int i = 0; i < MICS_AMOSTRAS_ADC; ++i) somaMv += analogReadMilliVolts(MICS_ADC_PIN);
  float adcV = (somaMv / static_cast<float>(MICS_AMOSTRAS_ADC)) / 1000.0f;
  l.gas_raw_v = adcV * MICS_DIVISOR;
  l.gas_raw_ok = isfinite(l.gas_raw_v) && l.gas_raw_v >= 0.0f && l.gas_raw_v <= 5.5f;
  l.lpg_ok = false;  // somente apos calibracao rastreavel do conjunto real
  if (l.gas_raw_ok) _gasRawMs = millis();
  return l.gas_raw_ok;
}

bool FonteFisica::atualizar(Leitura& out) {
  lerPMS7003(_ultima);  // drena a UART continuamente
  const unsigned long agora = millis();
  if (!_ultimoCicloMs || agora - _ultimoCicloMs >= 1000UL) {
    _ultimoCicloMs = agora;
    lerSHT31(_ultima);
    lerSGP40(_ultima);  // algoritmo VOC requer cadencia de 1 Hz
    lerSCD41(_ultima);  // so atualiza quando o SCD41 sinaliza dado pronto
    lerMiCS5524(_ultima);
    _ultima.sequence = ++_sequence;
  }

  if (_thMs == 0 || agora - _thMs > 5000UL) _ultima.th_ok = false;
  if (_vocMs == 0 || agora - _vocMs > 5000UL) _ultima.voc_ok = false;
  if (_co2Ms == 0 || agora - _co2Ms > 15000UL) _ultima.co2_ok = false;
  if (_pmMs == 0 || agora - _pmMs > 15000UL) _ultima.pm1_ok = _ultima.pm_ok = false;
  if (_gasRawMs == 0 || agora - _gasRawMs > 5000UL) _ultima.gas_raw_ok = false;

  const bool criticos = _ultima.co2_ok && _ultima.th_ok && _ultima.pm1_ok && _ultima.pm_ok;
  const bool completa = criticos && _ultima.voc_ok && _ultima.lpg_ok;
  _ultima.status = completa ? STATUS_OK : criticos ? STATUS_DEGRADED : STATUS_ERROR;
  _ultima.recente = criticos;
  out = _ultima;
  return out.recente;
}

#else

// Mantem o arquivo compilavel no ambiente HIL sem puxar bibliotecas fisicas.
void FonteFisica::iniciar() { _ultima.limpar(); }
bool FonteFisica::atualizar(Leitura& out) { out = _ultima; return false; }
bool FonteFisica::lerSHT31(Leitura&) { return false; }
bool FonteFisica::lerSGP40(Leitura&) { return false; }
bool FonteFisica::lerSCD41(Leitura&) { return false; }
bool FonteFisica::lerPMS7003(Leitura&) { return false; }
bool FonteFisica::lerMiCS5524(Leitura&) { return false; }

#endif
