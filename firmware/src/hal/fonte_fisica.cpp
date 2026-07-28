// =============================================================================
//  fonte_fisica.cpp — implementacao (ESQUELETO) da fonte FISICA
// =============================================================================
//
//  Este arquivo mostra a ESTRUTURA correta de leitura dos sensores reais, mas
//  os corpos concretos dependem das bibliotecas dos fabricantes e de calibracao.
//  Descomente os #include e as chamadas conforme instalar cada biblioteca no
//  platformio.ini. Enquanto um sensor nao estiver validado, deixe o seu ler*()
//  retornando false: a Leitura marcara a medida como ausente (null), e o
//  contrato v1.1 lida com isso normalmente.
// =============================================================================
#include "fonte_fisica.h"
#include <Arduino.h>
#include <Wire.h>

// --- Bibliotecas sugeridas (habilite no platformio.ini e descomente) ---------
// #include <Adafruit_SHT31.h>       // SHT31-D (temp/umidade)
// #include <SensirionI2CSgp40.h>    // SGP40 (voc_index)
// #include <SensirionI2CScd4x.h>    // SCD41 (co2)
// #include <PMS.h>                  // Plantower PMS7003 (particulados)

// static Adafruit_SHT31 sht31;
// static SensirionI2CSgp40 sgp40;
// static SensirionI2CScd4x scd41;
// static PMS pms(Serial2);

void FonteFisica::iniciar() {
  Wire.begin(I2C_SDA, I2C_SCL);
  // sht31.begin(0x44);
  // sgp40.begin(Wire);
  // scd41.begin(Wire); scd41.startPeriodicMeasurement();
  Serial2.begin(9600, SERIAL_8N1, PMS_UART_RX, PMS_UART_TX);  // PMS7003
  analogReadResolution(12);                                    // ADC do MiCS
  // Atencao: o MiCS-5524 precisa de aquecimento (minutos) para leitura estavel.
}

bool FonteFisica::lerSHT31(Leitura& l) {
  // float t = sht31.readTemperature();
  // float h = sht31.readHumidity();
  // if (isnan(t) || isnan(h)) return false;
  // l.temperature_c = t; l.humidity_pct = h; l.th_ok = true; return true;
  return false;  // TODO: habilitar apos validar o SHT31
}

bool FonteFisica::lerSGP40(Leitura& l) {
  // uint16_t vocRaw; sgp40.measureRawSignal(umidade, temp, vocRaw);
  // l.voc_index = /* converter raw->index com o algoritmo VOC */; l.voc_ok = true;
  return false;  // TODO: SGP40 exige o algoritmo de VOC Index (lib Sensirion)
}

bool FonteFisica::lerSCD41(Leitura& l) {
  // uint16_t co2; float t, h; scd41.readMeasurement(co2, t, h);
  // if (co2 == 0) return false;  // 0 = ainda sem amostra
  // l.co2_ppm = co2; l.co2_ok = true; return true;
  return false;  // TODO: habilitar apos validar o SCD41
}

bool FonteFisica::lerPMS7003(Leitura& l) {
  // PMS::DATA data;
  // if (!pms.readUntil(data)) return false;
  // l.pm1_ugm3 = data.PM_AE_UG_1_0; l.pm1_ok = true;
  // l.pm25_ugm3 = data.PM_AE_UG_2_5; l.pm10_ugm3 = data.PM_AE_UG_10_0; l.pm_ok = true;
  return false;  // TODO: habilitar apos validar o PMS7003
}

bool FonteFisica::lerMiCS5524(Leitura& l) {
  // Leitura analogica bruta -> ppm de GLP exige CALIBRACAO (Rs/Ro e curva).
  // int raw = analogRead(MICS_ADC_PIN);
  // float ppm = calibrarLpg(raw);   // implemente a curva do seu modulo
  // l.lpg_ppm = (int)ppm; l.lpg_ok = true; return true;
  return false;  // TODO: calibrar o MiCS-5524 antes de confiar no valor
}

bool FonteFisica::atualizar(Leitura& out) {
  Leitura l;
  l.limpar();

  bool algum = false;
  algum |= lerSHT31(l);
  algum |= lerSGP40(l);
  algum |= lerSCD41(l);
  algum |= lerPMS7003(l);
  algum |= lerMiCS5524(l);

  l.sequence = (out.sequence + 1);  // sequencia crescente local
  if (!algum) {
    l.status = STATUS_ERROR;
    l.recente = false;
  } else if (!(l.co2_ok && l.th_ok && l.pm_ok)) {
    l.status = STATUS_DEGRADED;  // algum sensor critico faltou
    l.recente = true;
  } else {
    l.status = STATUS_OK;
    l.recente = true;
  }

  _ultimaLeituraMs = millis();
  out = l;
  return l.recente;
}
