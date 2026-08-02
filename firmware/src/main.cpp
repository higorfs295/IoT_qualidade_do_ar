// =============================================================================
//  main.cpp — Orquestracao do firmware da Estacao de Qualidade do Ar
//  Projeto: base_final (Hardware-in-the-Loop + Strategy)
// =============================================================================
//
//  O main NAO sabe se os dados vem da USB (simulado) ou dos sensores (fisico).
//  Ele so conversa com a interface FonteSensores. A escolha e feita em tempo de
//  compilacao pelo #define MODO_SENSOR em config.h — trocar sim<->fisico e uma
//  linha, sem tocar nesta logica.
//
//  Fluxo:
//    setup(): Serial + fonte->iniciar() + publicador->iniciar()
//    loop():  fonte->atualizar(leitura); a cada INTERVALO, publica a telemetria
//
// Compilado nos ambientes esp32-hil e esp32-fisico; validar eletricamente em
// bancada antes de interpretar medidas reais.
// =============================================================================
#include <Arduino.h>
#include <esp_idf_version.h>
#include <esp_task_wdt.h>
#include "config.h"
#include "hal/fonte_sensores.h"
#include "hal/fonte_simulada.h"
#include "hal/fonte_fisica.h"
#include "net/publicador_mqtt.h"

// --- Selecao da estrategia (Strategy) em tempo de compilacao ------------------
#if MODO_SENSOR == FONTE_SIMULADA
static FonteSimulada fonteConcreta;
#else
static FonteFisica fonteConcreta;
#endif
static FonteSensores* fonte = &fonteConcreta;   // a aplicacao so ve a interface

static PublicadorMqtt publicador;
static Leitura leitura;
static unsigned long ultimaPublicacaoMs = 0;
static bool watchdogAtivo = false;

static void iniciarWatchdog() {
#if ESP_IDF_VERSION_MAJOR >= 5
  esp_task_wdt_config_t cfg = {
    .timeout_ms = WATCHDOG_TIMEOUT_S * 1000U,
    .idle_core_mask = (1U << portNUM_PROCESSORS) - 1U,
    .trigger_panic = true,
  };
  esp_err_t erro = esp_task_wdt_init(&cfg);
  if (erro == ESP_ERR_INVALID_STATE) erro = esp_task_wdt_reconfigure(&cfg);
#else
  esp_err_t erro = esp_task_wdt_init(WATCHDOG_TIMEOUT_S, true);
#endif
  if (erro == ESP_OK || erro == ESP_ERR_INVALID_STATE) {
    const esp_err_t inscricao = esp_task_wdt_add(nullptr);
    watchdogAtivo = inscricao == ESP_OK || inscricao == ESP_ERR_INVALID_STATE;
  }
  Serial.printf("[watchdog] %s (%us)\n", watchdogAtivo ? "ativo" : "falha",
                WATCHDOG_TIMEOUT_S);
}

void setup() {
  Serial.begin(SERIAL_BAUD);
  delay(200);
  Serial.println();
  Serial.println("=== Estacao de Qualidade do Ar (base_final) ===");
  Serial.print("Fonte de sensores: ");
  Serial.println(fonte->nome());

  fonte->iniciar();
  publicador.iniciar();
  iniciarWatchdog();

  Serial.println("Setup concluido. Aguardando leituras...");
}

void loop() {
  if (watchdogAtivo) esp_task_wdt_reset();
  // 1) mantem a rede viva (reconecta, processa MQTT)
  publicador.manter();

  // 2) atualiza a leitura mais recente (nao bloqueia)
  bool valida = fonte->atualizar(leitura);

  // 3) publica no ritmo do contrato (1 leitura consolidada por intervalo)
  unsigned long agora = millis();
  if (agora - ultimaPublicacaoMs >= INTERVALO_PUBLICACAO_MS) {
    ultimaPublicacaoMs = agora;

    if (!valida) {
      Serial.println("[aviso] sem leitura recente da fonte (heartbeat). "
                     "Publicando status degradado/erro.");
    }
    bool ok = publicador.publicar(leitura);
    Serial.print("[publicacao] seq=");
    Serial.print(leitura.sequence);
    Serial.print(" status=");
    Serial.print(leitura.status == STATUS_OK ? "OK"
               : leitura.status == STATUS_DEGRADED ? "DEGRADED" : "ERROR");
    Serial.print(" -> ");
    Serial.print(ok ? "aceito" : "FALHOU (relogio/heap?)");
    Serial.print(" fila=");
    Serial.print(publicador.pendentes());
    Serial.print(" descartadas=");
    Serial.println(publicador.descartadas());
  }

  delay(10);  // cede CPU; o loop e nao bloqueante
}
