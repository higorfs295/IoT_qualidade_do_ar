// =============================================================================
//  contrato.h — Espelho, no firmware, do contrato de dados v1.1
// =============================================================================
//
//  Mantem os nomes de campos e a estrutura do topico iguais aos do lado Python
//  (poc/qar_poc/contrato.py). Se o contrato mudar, mude aqui tambem.
// =============================================================================
#pragma once
#include <Arduino.h>
#include <stdio.h>

#define SCHEMA_VERSION_STR  "1.1"
#define TOPICO_PREFIXO      "qualidade-ar"
#define TOPICO_SUFIXO       "telemetria"

// Monta sem String dinamica para reduzir fragmentacao de heap no ESP32.
inline bool montarTopico(char* destino, size_t capacidade, const char* site,
                         const char* device, const char* sufixo = TOPICO_SUFIXO) {
  const int n = snprintf(destino, capacidade, "%s/%s/%s/%s",
                         TOPICO_PREFIXO, site, device, sufixo);
  return n > 0 && static_cast<size_t>(n) < capacidade;
}
