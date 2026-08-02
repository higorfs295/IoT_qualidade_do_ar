# BASE_FINAL — Estação de Monitoramento de Qualidade do Ar (projeto real)

> **Nota de revisão (02/08/2026):** este arquivo preserva o blueprint original
> e foi alinhado à instalação local final.
> O estado auditado, correções e gates atuais estão no [`README.md`](README.md)
> e em [`docs/STATUS_PROJETO.md`](docs/STATUS_PROJETO.md). Em caso de divergência,
> esses documentos mais recentes prevalecem.

> Blueprint mestre da evolução do projeto acadêmico para um **produto real**:
> um protótipo físico (ESP32 + shield PCB + case) com **sensores emulados por
> software** durante o desenvolvimento (Hardware-in-the-Loop), ecossistema
> completo de ingestão, dashboard web e app mobile.
>
> UFG — Engenharia de Computação — Internet das Coisas — Higor Ferreira Silva.
> Este documento **define e documenta** a base; o software local está funcional
> e as etapas que exigem hardware, fabricação ou conta AWS permanecem marcadas.

---

## Sumário

1. [Visão e princípio-guia](#1-visão-e-princípio-guia)
2. [A ideia central: HAL + Strategy + HIL](#2-a-ideia-central-hal--strategy--hil)
3. [Seleção de sensores e barramentos](#3-seleção-de-sensores-e-barramentos)
4. [O protótipo físico: ESP32, shield PCB e case](#4-o-protótipo-físico-esp32-shield-pcb-e-case)
5. [Contrato de dados v1.1](#5-contrato-de-dados-v11)
6. [Serialização e o elo HIL (PC ↔ ESP32)](#6-serialização-e-o-elo-hil-pc--esp32)
7. [Arquitetura de software ponta a ponta](#7-arquitetura-de-software-ponta-a-ponta)
8. [Firmware (a camada de abstração)](#8-firmware-a-camada-de-abstração)
9. [Ingestão, dashboard web e app mobile](#9-ingestão-dashboard-web-e-app-mobile)
10. [Princípios de redes e sistemas distribuídos aplicados](#10-princípios-de-redes-e-sistemas-distribuídos-aplicados)
11. [Reuso dos 3 projetos de referência](#11-reuso-dos-3-projetos-de-referência)
12. [Segurança](#12-segurança)
13. [Estrutura de pastas da branch base_final](#13-estrutura-de-pastas-da-branch-base_final)
14. [Roadmap por fases](#14-roadmap-por-fases)
15. [O que já está executável nesta branch](#15-o-que-já-está-executável-nesta-branch)

---

## 1. Visão e princípio-guia

Transformar a prova de conceito das atividades anteriores em uma **estação de
monitoramento ambiental de nível profissional**, começando por **um único
protótipo** físico e um ecossistema de software completo em volta dele.

O princípio-guia é **desacoplar a lógica da aplicação do hardware**. A aplicação
(publicar em MQTT, alimentar dashboards, alertar, processar na borda) é
construída e validada **hoje**, com sensores emulados por software, e continua
idêntica **amanhã**, quando os sensores físicos chegarem. A troca entre "modo
simulado" e "modo físico" é **uma variável de configuração no firmware** — zero
alteração na lógica principal.

Isso resolve o problema clássico de projetos IoT: esperar o hardware para
começar o software. Aqui os dois caminham em paralelo desde o dia 1.

---

## 2. A ideia central: HAL + Strategy + HIL

Três conceitos combinados:

- **HAL (Hardware Abstraction Layer):** uma camada no firmware que expõe um
  **contrato único** — "me dê as métricas ambientais" — sem revelar de onde os
  dados vêm.
- **Strategy (padrão de projeto):** a HAL tem uma interface abstrata
  (`FonteSensores`) e implementações intercambiáveis. Trocar a estratégia troca
  a origem dos dados sem tocar em quem a consome.
- **HIL (Hardware-in-the-Loop):** durante o desenvolvimento, um **script Python
  no PC** ("central de sensores virtual") gera leituras coerentes e as envia por
  **Serial/USB** ao ESP32. O ESP32 real executa o firmware real; só a **origem
  dos sensores** é emulada.

```text
                    ┌─────────────────────────────────────────────┐
                    │            APLICAÇÃO (não muda)              │
                    │  monta telemetria v1.1 → publica em MQTT     │
                    └───────────────────┬─────────────────────────┘
                                        │ pede Leitura
                            ┌───────────▼───────────┐
                            │   FonteSensores (IF)   │  ← Strategy
                            └───────────┬───────────┘
                 ┌──────────────────────┴──────────────────────┐
                 ▼                                              ▼
      ┌────────────────────┐                       ┌────────────────────────┐
      │  FonteSimulada      │  MODO_SENSOR=SIMULADO │  FonteFisica            │
      │  lê JSON via Serial │◄──── (config) ───────►│  lê I2C/UART/ADC reais  │
      └─────────▲──────────┘                        └───────────▲────────────┘
                │ JSON por USB                                    │ barramentos
      ┌─────────┴──────────┐                          ┌──────────┴───────────┐
      │ central_sensores.py │                          │ SHT31 SGP40 SCD41    │
      │ (PC — cenários)     │                          │ PMS7003 MiCS-5524    │
      └────────────────────┘                          └──────────────────────┘
```

**Ganho prático:** a mudança física é `#define MODO_SENSOR FONTE_SIMULADA` →
`FONTE_FISICA`. Nada mais.

---

## 3. Seleção de sensores e barramentos

Decisão de projeto (priorizando **I2C robusto**, baixo consumo e menor taxa de
falhas, coerente com a Atividade 1 que já usava SCD41):

| Grandeza | Módulo escolhido | Barramento | Por quê (vs. opção padrão) |
|---|---|---|---|
| **CO₂ (NDIR)** | **Sensirion SCD41** | I2C `0x62` | fotoacústico NDIR, precisão de laboratório, minúsculo; já era o da Ativ. 1 |
| **Temp + Umidade** | **Sensirion SHT31-D** | I2C `0x44` | sem o timing crítico do DHT22 (single-wire) que trava a CPU e falha |
| **TVOC** | **Sensirion SGP40** | I2C `0x59` | entrega **VOC Index** direto, melhor compensação de umidade, mais durável que o SGP30 |
| **Partículas PM1/2.5/10** | **Plantower PMS7003** | UART2 | compacto, baixo consumo, **adiciona PM1.0** (vs. PMS5003/SDS011) |
| **GLP / combustíveis** | **MiCS-5524** | Analógico (ADC1) | MEMS: menor, menos corrente e calor que os resistivos MQ-5/MQ-6 |

**Mapa de barramentos no ESP-WROOM-32 DevKit 30P USB-C:**

| Recurso | Pino(s) | Ligado a |
|---|---|---|
| I2C — SDA | GPIO 21 | SHT31, SGP40, SCD41 (endereços distintos, mesmo barramento) |
| I2C — SCL | GPIO 22 | idem |
| UART2 — RX | GPIO 16 | PMS7003 TX |
| UART2 — TX | GPIO 17 | PMS7003 RX (SET/RESET opcionais) |
| ADC1 — CH6 | GPIO 34 (só entrada) | MiCS-5524 VOUT |
| USB (UART0) | GPIO 1/3 | **elo HIL com o PC** (modo simulado) + logs |

> Observações de projeto: o PMS7003 alimenta a ventoinha em **5 V** (dados são
> 3.3 V-tolerantes); o MiCS-5524 tem **aquecedor** e precisa de estabilização
> térmica antes da primeira leitura confiável.

**Estratégia de alimentação (resumo — detalhes em [`hardware/pcb`](hardware/pcb/README.md)):**

- **5 V** para ventoinha (PMS7003) e aquecedor (MiCS-5524); **3.3 V** para os
  três sensores I2C (Sensirion).
- No modo físico, use a entrada externa regulada de **5 V/2 A** da shield e
  feche `JP1` somente com o USB desconectado. Para gravação/debug, deixe `JP1`
  aberto e alimente apenas pelo USB-C. A Rev A não autoriza as duas fontes ao
  mesmo tempo. O capacitor bulk especificado é de **1000 µF** no rail de 5 V.
- **Redutor de tensão (obrigatório):** o VOUT analógico do MiCS-5524 pode chegar
  perto de 5 V e queimaria o GPIO34 (máx. 3.3 V). A revisão atual usa
  **15 kΩ/10 kΩ (ganho 0,4) + RC**. O firmware multiplica a leitura por
  `MICS_DIVISOR=2.5` para estimar a tensão antes do divisor; ppm permanece nulo
  até existir calibração rastreável do conjunto real.
- Nenhum outro nível precisa de conversão: I2C e a UART do PMS7003 já são 3.3 V.

---

## 4. O protótipo físico: ESP32, shield PCB e case

- **ESP32 real**: DevKit de 30 pinos com módulo Wi-Fi ESP-WROOM-32 e USB-C;
  executa o mesmo firmware em HIL, físico ou AWS.
- **Shield PCB** (prototipada): uma placa que encaixa sobre o ESP32 e organiza
  I2C (com pull-ups de 4.7 kΩ), a UART do PMS7003, a entrada ADC do MiCS-5524,
  alimentação (5 V para ventoinha/heater, 3.3 V para I2C) e conectores JST para
  cada módulo. Especificação em [`hardware/pcb/`](hardware/pcb/).
- **Case (SolidWorks)**: invólucro com **circulação de ar** para os sensores,
  isolamento térmico do ESP32 (para não contaminar a leitura de temperatura),
  passagem para a ventoinha do PMS7003 e recorte para USB. Especificação
  paramétrica em [`hardware/case/`](hardware/case/) (os arquivos `.sldprt` você
  modela no SolidWorks a partir da especificação; não são gerados aqui).

---

## 5. Contrato de dados v1.1

Evolui o contrato v1.0 do Wilson **de forma aditiva e retrocompatível**. As
mudanças refletem os módulos escolhidos:

| Campo (measurements) | v1.0 | v1.1 | Fonte |
|---|:---:|:---:|---|
| `co2_ppm` | ✔ | ✔ | SCD41 |
| `temperature_c`, `humidity_pct` | ✔ | ✔ | SHT31 |
| `pm1_ugm3`, `pm25_ugm3`, `pm10_ugm3` | ✔ | ✔ | PMS7003 |
| `tvoc_ppb` | ✔ | opcional (legado) | — |
| `voc_index` | — | **✔ (novo)** | SGP40 (índice 1–500) |
| `gas_raw_v` | — | **✔ (diagnóstico)** | MiCS-5524 via divisor ADC |
| `lpg_ppm` | — | condicional | somente após calibração rastreável |

O `schema_version` passa a aceitar **"1.0"** e **"1.1"**. Mensagens v1.0
continuam válidas; v1.1 exige os novos campos. O validador em
[`poc/qar_poc/contrato.py`](poc/qar_poc/contrato.py) trata as duas versões.
Todo o resto do contrato (tópico, `message_id` ULID, `sequence`, `quality`,
`metadata`, política de retenção) permanece como no v1.0 — ver
[`docs/modelagem_dados.json`](docs/modelagem_dados.json) e
[`ARQUITETURA.md`](ARQUITETURA.md).

---

## 6. Serialização e o elo HIL (PC ↔ ESP32)

O elo entre a "central de sensores virtual" (PC) e o ESP32 usa **JSON
delimitado por linha** (NDJSON) sobre a Serial/USB — simples, legível e
depurável, coerente com a escolha de JSON do contrato MQTT.

**Formato do quadro (PC → ESP32):** uma linha JSON por leitura, terminada em
`\n`:

```json
{"t":"sensors","seq":128,"co2_ppm":812,"voc_index":140,"lpg_ppm":6,"pm1_ugm3":9.2,"pm25_ugm3":14.7,"pm10_ugm3":22.1,"temperature_c":24.8,"humidity_pct":51.3,"cenario":"normal"}
```

**Regras de robustez (princípios de rede aplicados ao enlace serial):**

- **Enquadramento (framing):** `\n` delimita quadros; linhas que não fazem parse
  são descartadas (o firmware não trava com lixo na linha).
- **Sequência e detecção de perda:** `seq` cresce a cada quadro; o firmware
  detecta lacunas (mesma ideia do `sequence` do MQTT).
- **Heartbeat / timeout:** se nenhum quadro chega em `TIMEOUT_SENSOR_MS`, o
  firmware marca `sensor_status = DEGRADED` e depois `ERROR`, e o `gas_status`
  vira `UNKNOWN` — falha explícita, nunca dado velho silencioso.
- **Direções independentes:** o PC **escreve** quadros na RX do ESP32; o ESP32
  **escreve** logs na TX. Mesmo cabo, sem colisão.
- **Evolução opcional:** para produção de altíssimo volume, o mesmo contrato
  pode migrar de JSON para **protobuf/CBOR** (ver §10 e o reuso do `sd-main`),
  mantendo os campos.

O firmware transforma o quadro na **mesma `Leitura`** que a fonte física
produziria. A partir daí, aplicação e rede não distinguem sim de físico.

---

## 7. Arquitetura de software ponta a ponta

```text
[central_sensores.py]                    (PC, modo desenvolvimento)
        │ NDJSON via USB
        ▼
   [ESP32 real] ── firmware HAL (Strategy) ── monta telemetria v1.1
        │ MQTT/TLS, QoS 1, tópico qualidade-ar/{site}/{device}/telemetria
        ▼
   [Broker MQTT]  Mosquitto local  ▶ AWS IoT Core (perfil mTLS disponível)
        │
        ├──► [Ingestão]  serviço que assina o broker, valida o contrato,
        │                persiste série temporal e expõe API REST + WebSocket
        │                     │
        │                     ├──► [Dashboard/PWA]  web responsiva e instalável
        │                     └──► [App Flutter]    opcional, se houver requisito nativo
        │
        └──► [Alertas]  regras de limiar → Telegram/e-mail (futuro)
```

- **Broker:** Mosquitto (já pronto em [`infra/server_config`](infra/server_config))
  ou conexão mTLS direta com AWS IoT Core. O sandbox reproduzível está em
  [`infra/aws/`](infra/aws/).
- **Ingestão:** serviço Node.js enxuto que assina o tópico de telemetria, valida
  contrato e tópico, mantém séries limitadas, persiste snapshots atômicos e
  serve REST, WebSocket, health e métricas Prometheus.
- **Dashboard/PWA:** aplicação web responsiva, sem dependências em runtime,
  **legível e conduzível por um leigo**, com cartões, histórico curto, texto
  além de cor, atualização em tempo real e shell offline.
- **Mobile:** a PWA é o cliente móvel funcional. Flutter permanece opcional para
  push em segundo plano, BLE ou integrações nativas futuras.

---

## 8. Firmware (a camada de abstração)

Estrutura em [`firmware/`](firmware/) (PlatformIO + Arduino). Os ambientes
`esp32-hil`, `esp32-fisico` e `esp32-aws` foram compilados para
`esp32doit-devkit-v1`; flash, sensores, pinout rotulado e alimentação ainda
exigem validação na unidade física.

| Arquivo | Papel |
|---|---|
| `config.h` | `MODO_SENSOR` (SIMULADO/FÍSICO), pinos, Wi-Fi/MQTT, intervalos, timeouts |
| `contrato.h` | nomes de campos/tópico do contrato v1.1 (espelha o Python) |
| `hal/leitura.h` | `struct Leitura` — o dado unificado que ambas as fontes produzem |
| `hal/fonte_sensores.h` | interface `FonteSensores` (o Strategy) |
| `hal/fonte_simulada.{h,cpp}` | lê NDJSON da Serial e preenche `Leitura` |
| `hal/fonte_fisica.{h,cpp}` | SHT31, SGP40/VOC, SCD41, PMS7003 e ADC calibrável |
| `net/publicador_mqtt.{h,cpp}` | publica a `Leitura` como telemetria v1.1 |
| `main.cpp` | orquestra: escolhe a fonte, lê, monta payload, publica |

A troca sim↔físico é só o `#define MODO_SENSOR` em `config.h`. O `main.cpp`
**não sabe** qual fonte está ativa.

---

## 9. Ingestão, dashboard web e cliente móvel

- **Ingestão + API** — [`dashboard/backend/`](dashboard/backend/): MQTT, contrato
  v1.1, deduplicação/lacunas, persistência local limitada, REST, WebSocket,
  healthcheck e Prometheus. A API está em [`docs/openapi.yaml`](docs/openapi.yaml).
- **Dashboard/PWA** — [`dashboard/web/`](dashboard/web/): cartões de estado,
  séries curtas, conectividade, explicações, manifest e service worker. É servido
  pelo próprio backend e funciona no navegador desktop ou móvel.
- **Instalação** — [`compose.yaml`](compose.yaml) sobe Mosquitto, backend, painel
  e gerador de três estações; os scripts em [`scripts/`](scripts/) aguardam a
  stack ficar pronta antes de retornar sucesso.
- **App nativo** — [`mobile/`](mobile/) documenta a opção Flutter, sem duplicar a
  funcionalidade que a PWA já entrega.

Para histórico longo, usuários concorrentes e alta disponibilidade, o próximo
gate é PostgreSQL/TimescaleDB e autenticação; o snapshot local não se apresenta
como substituto de um banco de produção.

---

## 10. Princípios de redes e sistemas distribuídos aplicados

- **Serialização versionada:** o `schema_version` no payload permite evoluir o
  contrato sem quebrar consumidores (lição do `dfs.v1`/`dfs.dataplane` do
  `sd-main`). JSON hoje; caminho para protobuf/CBOR no alto volume.
- **Entrega confiável e idempotência:** MQTT QoS 1 + `message_id` (ULID) +
  `sequence` — já validados na PoC (0 perdas). O mesmo `sequence` protege o elo
  serial HIL.
- **Heartbeat e falha explícita:** timeout no elo serial e **Last Will &
  Testament** no MQTT sinalizam dispositivo offline — inspirado no heartbeat do
  DFS do `sd-main`.
- **Backpressure:** limites de inflight/fila no cliente MQTT (PoC) e amortecimento
  por fila na nuvem (SQS) — evita colapso sob pico.
- **Desacoplamento produtor/consumidor:** o broker separa quem publica de quem
  consome; a ingestão pode escalar independente dos dispositivos.
- **Observabilidade:** métricas → CSV → gráficos, metodologia de benchmark
  herdada do `sd-main` (throughput/latência/concorrência), e endpoint `/metrics`
  estilo Prometheus (herdado do simulador do IoT-IDEA).

---

## 11. Reuso dos 3 projetos de referência

| Projeto | O que reaproveitamos |
|---|---|
| **Painel_UFG** | Referência de organização, testes, Docker, documentação e caminho futuro para backend/banco e frontend de maior escala. A base atual permaneceu menor para caber na instalação local. |
| **IoT-IDEA** | Padrão de **firmware** (`#define` de modo, disclaimer de esqueleto, PubSubClient + TLS), **simulador de dispositivo** (argparse, threads, `/metrics`, self-test), **dashboard leve** (`charts.js` SVG sem deps, `config.js` modo auto/live/mock, SSE+polling), e **hardening** de segurança. |
| **sd-main** | Princípios de **sistemas distribuídos e serialização**: contrato versionado (protobuf), separação plano de controle/dados, **heartbeat**, e a metodologia **benchmark → CSV → gráficos** para as métricas. |

---

## 12. Segurança

Herda o já feito (TLS 8883, ACL por dispositivo, `setup_ubuntu_broker.sh --auth
--tls`, `gerar_certs.sh`) e o hardening do IoT-IDEA:

- **mTLS** por dispositivo em produção (certificado X.509 por ESP32).
- **Autenticação MQTT** e **ACL de menor privilégio** (device só publica no seu
  tópico).
- **Rate limiting** e senha forte em qualquer painel HTTP.
- **Sem segredos no repositório** (`.gitignore` cobre `*.env`, `*.key`, `*.crt`).
- **Payload sem dados sensíveis** (regra do contrato).

---

## 13. Estrutura de pastas da branch base_final

```text
├── BASE_FINAL.md              ◄─ ESTE blueprint
├── SINTESE.md                 explicação do projeto em linguagem simples (analogias)
├── ARQUITETURA.md             arquitetura da ingestão (já existente)
│
├── firmware/                  ESP32: HAL + Strategy (sim/físico)
│   ├── platformio.ini
│   ├── README.md
│   └── src/{config.h, contrato.h, main.cpp, hal/*, net/*}
│
├── simulador/                 "central de sensores virtual" (HIL)
│   ├── central_sensores.py    gera cenários e envia NDJSON pela Serial
│   ├── requirements.txt
│   └── README.md
│
├── poc/                       PoC de carga (já existente) + contrato v1.1
│   └── qar_poc/               contrato, sensor, gateway, coordenador, sink...
│
├── compose.yaml               instalação local completa e persistente
├── scripts/                   instaladores e configurador do firmware
├── dashboard/                 ingestão persistente + PWA funcional
│   ├── backend/src/           MQTT, validação, REST/WS, snapshot e métricas
│   └── web/public/            painel responsivo, manifest e service worker
│
├── mobile/                    roadmap opcional do app Flutter
│
├── hardware/                  especificações e roteiros físicos
│   ├── pcb/                    shield PCB (barramentos, conectores)
│   └── case/                   case SolidWorks (especificação paramétrica)
│
├── infra/                     broker/compose/AWS (já existente)
└── docs/                      modelagem, estimativa, diagramas (grupo)
```

---

## 14. Roadmap por fases

- **Fase 0 — Base (esta branch):** contrato v1.1, firmware HAL compilável,
  simulador, backend persistente, PWA, Compose e IaC AWS. ✅
- **Fase 1 — HIL de ponta a ponta:** flashar o firmware; `central_
  sensores.py` alimentando o ESP32; ESP32 publicando no Mosquitto; validar com
  o `sink` da PoC.
- **Fase 2 — Ingestão + Dashboard Web:** **pronta e validada** — persistência
  limitada, REST/WebSocket, health/Prometheus e PWA em
  [`dashboard/`](dashboard/README.md). Evolução: banco temporal, usuários e HA.
- **Fase 3 — Produto + Alertas:** regras com histerese/auditoria; Flutter apenas
  se a PWA não cobrir os requisitos móveis.
- **Fase 4 — Físico + Nuvem:** montar shield PCB e case; trocar `MODO_SENSOR`
  para físico; migrar o broker para AWS IoT Core (bridge).

---

## 15. O que já está executável nesta branch

- **Contrato v1.1** validado (aceita v1.0 e v1.1) em
  [`poc/qar_poc/contrato.py`](poc/qar_poc/contrato.py).
- **Simulador HIL** [`simulador/central_sensores.py`](simulador/central_sensores.py):
  gera cenários coerentes (normal, pico de poluição, incêndio, vazamento de GLP)
  e emite NDJSON — com modo `--dry-run` (imprime os quadros) que roda sem
  hardware, e modo serial (`--porta COMx`) para alimentar o ESP32.
- **Firmware HAL** [`firmware/src/`](firmware/src/): Strategy HIL/físico e perfil
  AWS, todos compilados com partições OTA para flash de 4 MB.
- **PoC de carga** continua funcional (agora emitindo v1.1).

- **Stack local completa** em [`compose.yaml`](compose.yaml): Mosquitto, gerador,
  ingestão persistente, REST/WebSocket/Prometheus e PWA, validada inclusive após
  reinício do backend.
- **Projeto da PCB** em [`hardware/pcb`](hardware/pcb/README.md): arquitetura,
  pinagem completa, netlist, BOM e a **estratégia de alimentação** (fonte ≥ 1 A,
  bulk no 5 V, e o **divisor de tensão** do MiCS-5524) para o EasyEDA Pro.

`mobile/` documenta a evolução nativa opcional. `hardware/case/` e
`hardware/pcb/` contêm especificações e roadmaps detalhados, mas os arquivos
nativos dependem das medidas e da revisão nas ferramentas reais.
