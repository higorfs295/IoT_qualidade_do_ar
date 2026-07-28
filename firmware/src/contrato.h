// =============================================================================
//  contrato.h — Espelho, no firmware, do contrato de dados v1.1
// =============================================================================
//
//  Mantem os nomes de campos e a estrutura do topico iguais aos do lado Python
//  (poc/qar_poc/contrato.py). Se o contrato mudar, mude aqui tambem.
// =============================================================================
#pragma once
#include <Arduino.h>

#define SCHEMA_VERSION_STR  "1.1"
#define TOPICO_PREFIXO      "qualidade-ar"
#define TOPICO_SUFIXO       "telemetria"

// qualidade-ar/{site_id}/{device_id}/telemetria
inline String montarTopico(const char* site, const char* device) {
  return String(TOPICO_PREFIXO) + "/" + site + "/" + device + "/" + TOPICO_SUFIXO;
}
