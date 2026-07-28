// =============================================================================
//  leitura.h — O dado unificado que TODA fonte de sensores produz
// =============================================================================
//
//  Esta struct e o "contrato interno" da HAL: tanto a FonteSimulada (que le
//  JSON pela USB) quanto a FonteFisica (que le I2C/UART/ADC) preenchem
//  exatamente esta mesma estrutura. A aplicacao consome so isto e nunca sabe
//  de onde veio. Cada grandeza tem um flag "_ok": false significa medida
//  ausente (vira null no payload), o que o contrato v1.1 preve.
// =============================================================================
#pragma once
#include <stdint.h>

enum SensorStatus { STATUS_OK, STATUS_DEGRADED, STATUS_ERROR };

struct Leitura {
  // Gases (co2/voc/lpg sao inteiros no contrato)
  int32_t co2_ppm;      bool co2_ok;      // SCD41
  int32_t voc_index;    bool voc_ok;      // SGP40 (indice 1-500)
  int32_t lpg_ppm;      bool lpg_ok;      // MiCS-5524

  // Particulados (float)
  float pm1_ugm3;       bool pm1_ok;      // PMS7003
  float pm25_ugm3;      float pm10_ugm3;  bool pm_ok;

  // Ambiente (float)
  float temperature_c;  float humidity_pct;  bool th_ok;   // SHT31

  uint32_t sequence;    // sequencia da fonte (detecta lacunas no elo)
  SensorStatus status;  // OK / DEGRADED / ERROR
  bool recente;         // houve leitura dentro do timeout?

  void limpar() {
    co2_ok = voc_ok = lpg_ok = pm1_ok = pm_ok = th_ok = false;
    co2_ppm = voc_index = lpg_ppm = 0;
    pm1_ugm3 = pm25_ugm3 = pm10_ugm3 = 0.0f;
    temperature_c = humidity_pct = 0.0f;
    sequence = 0;
    status = STATUS_ERROR;
    recente = false;
  }
};
