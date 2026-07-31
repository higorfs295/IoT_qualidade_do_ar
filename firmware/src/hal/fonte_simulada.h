// =============================================================================
//  fonte_simulada.h — Fonte de sensores SIMULADA (Hardware-in-the-Loop)
// =============================================================================
//
//  Le quadros NDJSON enviados pela central_sensores.py (PC) pela Serial/USB e
//  preenche a Leitura unificada. Implementa o timeout (heartbeat): se os
//  quadros param de chegar, a leitura vira DEGRADED e depois ERROR.
// =============================================================================
#pragma once
#include <cstddef>
#include "fonte_sensores.h"
#include "../config.h"

class FonteSimulada : public FonteSensores {
 public:
  void iniciar() override;
  bool atualizar(Leitura& out) override;
  const char* nome() const override { return "SIMULADA (HIL serial)"; }

 private:
  void processarLinha(const char* linha);

  char _buf[LINHA_MAX];
  size_t _len = 0;
  Leitura _ultima;
  unsigned long _ultimoQuadroMs = 0;
  bool _recebeuAlgum = false;
};
