// =============================================================================
//  fonte_sensores.h — A interface do padrao Strategy (a "tomada" da HAL)
// =============================================================================
//
//  Qualquer origem de dados (simulada ou fisica) implementa esta interface. A
//  aplicacao guarda um ponteiro FonteSensores* e chama atualizar(); ela nunca
//  precisa de #ifdef nem sabe qual implementacao esta por tras.
// =============================================================================
#pragma once
#include "leitura.h"

class FonteSensores {
 public:
  virtual ~FonteSensores() {}

  // Chamado uma vez no setup(): abre barramentos/serial, inicializa sensores.
  virtual void iniciar() = 0;

  // Chamado com frequencia no loop(): atualiza `out` com a leitura mais
  // recente. Retorna true se ha uma leitura valida e recente; false se a fonte
  // ainda nao produziu dados ou estourou o timeout (heartbeat).
  virtual bool atualizar(Leitura& out) = 0;

  // Nome curto da fonte, para log.
  virtual const char* nome() const = 0;
};
