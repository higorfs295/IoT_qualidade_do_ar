// =============================================================================
//  fonte_fisica.h — Fonte de sensores FISICA (I2C/UART/ADC reais)
// =============================================================================
//
//  ESQUELETO. Le os modulos escolhidos no BASE_FINAL.md quando MODO_SENSOR ==
//  FONTE_FISICA. As leituras reais dependem das bibliotecas dos fabricantes e
//  de CALIBRACAO (em especial o MiCS-5524, que tem aquecedor e curva propria).
//  Preencha os TODOs e valide modulo a modulo antes de confiar nos numeros.
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
  bool lerMiCS5524(Leitura& l); // lpg_ppm (ADC) — precisa de calibracao

  unsigned long _ultimaLeituraMs = 0;
};
