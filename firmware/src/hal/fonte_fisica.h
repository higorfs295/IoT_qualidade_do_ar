// =============================================================================
//  fonte_fisica.h — Fonte de sensores FISICA (I2C/UART/ADC reais)
// =============================================================================
//
// Leitura nao bloqueante dos sensores fisicos. A entrada analogica do MiCS e
// disponibilizada como tensao bruta; ppm exige calibracao especifica.
// =============================================================================
#pragma once
#include "fonte_sensores.h"
#include "../config.h"

class FonteFisica : public FonteSensores {
 public:
  void iniciar() override;
  bool atualizar(Leitura& out) override;
  const char* nome() const override { return "FISICA (I2C/UART/ADC)"; }

 private:
  bool lerSHT31(Leitura& l);    // temperatura + umidade (I2C 0x44)
  bool lerSGP40(Leitura& l);    // voc_index (I2C 0x59)
  bool lerSCD41(Leitura& l);    // co2 (I2C 0x62)
  bool lerPMS7003(Leitura& l);  // pm1/pm2.5/pm10 (UART2)
  bool lerMiCS5524(Leitura& l); // gas_raw_v (ADC); ppm exige calibracao

  Leitura _ultima;
  uint32_t _sequence = 0;
  unsigned long _ultimoCicloMs = 0;
  unsigned long _thMs = 0, _vocMs = 0, _co2Ms = 0, _pmMs = 0, _gasRawMs = 0;
  uint8_t _pmsBuf[32] = {0};
  uint8_t _pmsIndex = 0;
  bool _shtDisponivel = false;
  bool _sgpDisponivel = false;
  bool _scdDisponivel = false;
};
