# Arquitetura da Solução — Monitoramento de Qualidade do Ar (Atividade 3)

> Documento técnico completo da arquitetura de ingestão de dados IoT.
> Explica, de forma simples e coesa, **todo** o código, todas as pastas, e
> **cada função e método** da prova de conceito (PoC) e da infraestrutura.
>
> Universidade Federal de Goiás — Instituto de Informática — Internet das Coisas
> Grupo: Khalil Alves Motta, Wilson Maranhão Ramos Filho, Lourenço Tabosa
> Paniago, Higor Ferreira Silva.

---

## Sumário

1. [Visão geral em 2 minutos](#1-visão-geral-em-2-minutos)
2. [O que a Atividade 3 pede e como atendemos](#2-o-que-a-atividade-3-pede-e-como-atendemos)
3. [Coesão com as Atividades 1 e 2](#3-coesão-com-as-atividades-1-e-2)
4. [Conceitos-chave explicados de forma simples](#4-conceitos-chave-explicados-de-forma-simples)
5. [A arquitetura completa (borda → nuvem)](#5-a-arquitetura-completa-borda--nuvem)
6. [As entidades e seus papéis](#6-as-entidades-e-seus-papéis)
7. [Estrutura de pastas do repositório](#7-estrutura-de-pastas-do-repositório)
8. [A PoC em detalhe: o pacote `qar_poc`](#8-a-poc-em-detalhe-o-pacote-qar_poc)
9. [Os entrypoints de linha de comando](#9-os-entrypoints-de-linha-de-comando)
10. [A infraestrutura em detalhe](#10-a-infraestrutura-em-detalhe)
11. [Concorrência, paralelismo e comunicação](#11-concorrência-paralelismo-e-comunicação)
12. [Segurança](#12-segurança)
13. [Como executar tudo (passo a passo)](#13-como-executar-tudo-passo-a-passo)
14. [Resultados validados](#14-resultados-validados)
15. [Respostas às Questões para Discussão](#15-respostas-às-questões-para-discussão)
16. [Da PoC local para a produção na AWS](#16-da-poc-local-para-a-produção-na-aws)
17. [Limitações e trabalhos futuros](#17-limitações-e-trabalhos-futuros)
18. [Glossário](#18-glossário)

---

## 1. Visão geral em 2 minutos

O projeto monitora a **qualidade do ar em ambientes fechados** (CO₂, TVOC,
material particulado, temperatura e umidade) e alerta quando algum parâmetro
ultrapassa um limite seguro. Ele evoluiu em três atividades:

| Atividade | Foco | Resultado |
|---|---|---|
| **1 — Planejamento** | Definir problema, hardware, sensores, arquitetura | ESP32 + SCD41/ENS160/PMS5003 → MQTT/TLS → ThingsBoard + PostgreSQL |
| **2 — Comunicação MQTT** | Provar a comunicação na prática | 1 ESP32 (Wokwi) publicando no HiveMQ Cloud, lido por um display |
| **3 — Ingestão em escala** | Projetar a ingestão para **milhares** de sensores | Arquitetura em nuvem (AWS) + **prova de conceito de carga** |

A Atividade 3 pergunta: *"e se não for 1 sensor, mas 100.000?"*. A resposta tem
duas partes:

- **O planejamento** (arquitetura, modelagem de dados, estimativa de carga,
  serviços AWS) — descrito nos documentos do grupo.
- **A prova de conceito** (este repositório de código) — um **gerador de carga**
  que simula milhares de sensores publicando telemetria real em um **broker
  MQTT**, e um **consumidor** que mede a ingestão e prova que **não há perda de
  mensagens**. Ela torna o planejamento *verificável com números*.

Este documento explica a segunda parte em profundidade, mostrando como ela se
conecta à primeira.

---

## 2. O que a Atividade 3 pede e como atendemos

A Atividade 3 tem etapas, entregáveis, questões de discussão e critérios de
avaliação. A tabela abaixo mapeia cada exigência ao que foi entregue e a quem.

### Etapas

| Etapa | O que pede | Como é atendida | Responsável |
|---|---|---|---|
| 1. Revisão | Revisar problema, hardware, sensores, MQTT | Retomados neste doc e nos READMEs; contrato herda os sensores da Ativ. 1 | Todos |
| 2. Cenário | Definir nº de sensores, frequência, volume | 5k/10k/50k/100k; 1 leitura/60 s; `docs/estimativa_carga.md` | Wilson |
| 3. Arquitetura | Diagrama: dispositivos, **gateway**, broker, **filas**, processamento, BD, dashboard, nuvem | Diagrama (§5) com **todas** essas caixas; PoC modela dispositivo→gateway→broker→sink | Lourenço (diagrama) + Higor (PoC) |
| 4. Modelagem | Estrutura das mensagens, formato, retenção | Schema v1.0 em `docs/modelagem_dados.json`; a PoC o implementa em `contrato.py` | Wilson (contrato) + Higor (código) |
| 5. AWS | IoT Core, Lambda, SQS, DynamoDB, S3, CloudWatch, IAM | `infra/aws/planejamento_servicos.md` | Wilson |
| 6. GitHub | Repositório com README, docs, planejamento, PoC | Este repo, organizado por pastas + READMEs | Todos |

> **Ajuste de coesão feito nesta entrega:** a Etapa 3 cita explicitamente um
> **gateway** e **filas** no diagrama. Por isso a PoC foi refatorada para
> **modelar o gateway como uma entidade própria** (`qar_poc/gateway.py`) e o
> papel de "fila/processamento" é exercido localmente pelo par broker + sink
> (e, na nuvem, por SQS + Lambda no plano do Wilson). Assim o código passou a
> refletir 1:1 as caixas exigidas no diagrama.

### Entregáveis

| Entregável | Onde | Responsável |
|---|---|---|
| Documento PDF | compilação final | Lourenço |
| Diagrama da arquitetura | `docs/arquitetura_solucao.pdf` | Lourenço |
| Modelagem dos dados | `docs/modelagem_dados.json` | Wilson |
| Estimativa de carga | `docs/estimativa_carga.{md,xlsx}` | Wilson |
| Planejamento de nuvem | `infra/aws/planejamento_servicos.md` | Wilson |
| **Prova de conceito** | `poc/` + `infra/server_config/` | **Higor** |
| Slides | `docs/apresentacao_slides.pdf` | Lourenço |
| Vídeo (opcional) | — | — |

### Critérios de avaliação (peso)

| Critério | Peso | Onde este trabalho contribui |
|---|---:|---|
| Arquitetura da solução | 25% | §5, §6, diagrama, PoC executável |
| Planejamento da ingestão | 20% | §11, gerador + sink, estimativa de carga |
| Modelagem dos dados | 15% | `contrato.py` (fonte única), §8.1 |
| Infraestrutura em nuvem | 20% | plano AWS (Wilson) + §16 (ponte PoC→AWS) |
| Organização do GitHub | 10% | §7, READMEs, este documento |
| Documentação e apresentação | 10% | este documento + slides |

---

## 3. Coesão com as Atividades 1 e 2

A regra de ouro do grupo é **não quebrar a coerência entre entregas**. A PoC da
Atividade 3 é uma **evolução direta**, não uma reinvenção:

| Aspecto | Atividade 1 (plano) | Atividade 2 (PoC MQTT) | Atividade 3 (esta PoC de carga) |
|---|---|---|---|
| Emissor | ESP32 + 3 sensores | 1 ESP32 no Wokwi | **milhares** de sensores virtuais |
| Sensores | SCD41, ENS160, PMS5003 | DHT22 + MQ2 (limitação do Wokwi) | faixas de SCD41/ENS160/PMS5003 recriadas em software |
| Frequência | 1 min | 5 s (para demonstrar) | **60 s** (operação planejada) |
| Grandezas | CO₂, TVOC, PM2.5, PM10, T, U | T, U, estado de gás | CO₂, TVOC, PM1/2.5/10, T, U (todas) |
| Payload | — | 3 mensagens de texto | **1 JSON consolidado** (schema v1.0) |
| Tópico | — | `INF01/temp`, `INF01/umid`, `INF01/co2` | `qualidade-ar/{site_id}/{device_id}/telemetria` |
| QoS | — | 0 | **1** (idempotência por `message_id`) |
| Broker | ThingsBoard | HiveMQ Cloud | **Mosquitto local** (papel do AWS IoT Core) |
| Plataforma | ThingsBoard + PostgreSQL | — | ThingsBoard + PostgreSQL (no compose) |

O **contrato de dados** (schema, tópico, retenção) é de autoria do Wilson
(`docs/modelagem_dados.json`); o **plano de nuvem**, também
(`infra/aws/planejamento_servicos.md`). A PoC do Higor **consome** essas
definições — não as recria — garantindo que código e planejamento contem a
mesma história.

---

## 4. Conceitos-chave explicados de forma simples

Para que qualquer leitor acompanhe o restante do documento:

- **IoT (Internet das Coisas):** objetos físicos (aqui, sensores de ar) que
  enviam dados pela rede.
- **MQTT:** protocolo leve de mensagens no modelo *publish/subscribe*. Quem
  produz dados **publica** em um "tópico"; quem consome **assina** o tópico. É
  ideal para IoT porque gasta pouca banda e bateria.
- **Broker:** o "correio" do MQTT. Recebe as mensagens dos publicadores e as
  entrega aos assinantes. Aqui é o **Mosquitto** (local) ou o **AWS IoT Core**
  (nuvem).
- **Tópico:** o "endereço" da mensagem, em árvore. Usamos
  `qualidade-ar/{site_id}/{device_id}/telemetria` — o site e o dispositivo ficam
  no caminho, o que facilita filtrar e particionar.
- **QoS (Quality of Service):** a garantia de entrega do MQTT.
  `QoS 0` = "no máximo uma vez" (pode perder); `QoS 1` = "pelo menos uma vez"
  (não perde, mas pode duplicar); `QoS 2` = "exatamente uma vez" (mais caro).
  O contrato usa **QoS 1** + deduplicação por `message_id`.
- **Ingestão de dados:** o ato de **receber, validar, processar e armazenar** os
  dados que chegam dos dispositivos. É o tema central da Atividade 3.
- **Idempotência:** processar a mesma mensagem duas vezes tem o mesmo efeito que
  processar uma vez. Conseguimos isso com o `message_id` único (ULID): se ele já
  foi visto, ignora-se a repetição.
- **Backpressure (contrapressão):** quando o consumidor não dá conta do ritmo,
  o sistema **segura** a produção em vez de estourar a memória. No cliente MQTT,
  isso é a fila de envio ficar cheia; na nuvem, é a fila SQS.
- **Concorrência × paralelismo:** *concorrência* é lidar com muitas tarefas ao
  mesmo tempo (threads intercalando I/O de rede); *paralelismo* é executá-las de
  fato em vários núcleos ao mesmo tempo (processos). A PoC usa os dois (§11).
- **Latência:** o tempo entre publicar e a mensagem ser confirmada/recebida.
  Medimos a **latência de PUBACK** (confirmação do broker) e a **fim-a-fim**
  (do `sent_at` até o sink receber).

---

## 5. A arquitetura completa (borda → nuvem)

A solução tem três zonas: **borda** (onde ficam os sensores), **ingestão** (o
que recebe e valida) e **nuvem** (processamento e armazenamento em escala).

```text
        ZONA DE BORDA                 INGESTÃO                    NUVEM (AWS - plano do Wilson)
 ┌───────────────────────────┐   ┌──────────────┐   ┌───────────────────────────────────────────┐
 │  Sensores (SCD41/ENS160/  │   │              │   │                                           │
 │  PMS5003) → ESP32         │   │   Broker     │   │   AWS IoT Core (broker gerenciado, mTLS)  │
 │        │ 1 leitura/60s    │   │   MQTT       │   │        │ regra de roteamento              │
 │        ▼                  │   │  (Mosquitto  │   │        ▼                                   │
 │   ┌──────────┐            │   │   local /    │   │     Amazon SQS ───────────► DLQ           │
 │   │ Gateway  │ concentra  │──►│   AWS IoT    │──►│        │ lote ≤ 100                        │
 │   │ do site  │ 1 conexão  │   │   Core)      │   │        ▼                                   │
 │   └──────────┘            │   │      │       │   │   AWS Lambda (valida, deduplica, agrega)  │
 │  (1 gateway por site)     │   │      ▼       │   │        │              │                    │
 └───────────────────────────┘   │   Sink /     │   │        ▼              ▼                    │
                                  │   Ingestor   │   │   DynamoDB       Amazon S3 (bruto/Parquet)│
      poc/ingestao_teste.py       │  (valida,    │   │  (estado atual)  (data lake)              │
      simula a zona de borda      │   detecta    │   │        │              │                    │
      inteira (sensores +         │   lacunas)   │   │        ▼              ▼                    │
      gateways) em software       │              │   │   API/Dashboard   Athena (consultas)      │
                                  └──────────────┘   │   CloudWatch (observabilidade) · IAM      │
                                                     └───────────────────────────────────────────┘
       └──────────── PoC LOCAL (este repositório) ───────────┘   └──── PLANEJAMENTO (Wilson) ────┘
```

**Leitura do diagrama:**

- Na **borda**, cada **site** (uma sala, um andar) tem um **gateway** que
  concentra seus sensores e mantém **uma** conexão MQTT de uplink. Isso reduz o
  número de conexões e espelha o par ESP32+roteador da Atividade 1.
- A **ingestão** local usa **Mosquitto** como broker e o **sink** como validador
  — exatamente os papéis que, na nuvem, o **AWS IoT Core** e a **Lambda**
  exercem.
- A **nuvem** (planejada pelo Wilson) recebe via IoT Core, amortece picos na
  **SQS**, processa na **Lambda** (validação/deduplicação/agregação), guarda o
  estado no **DynamoDB** e o histórico no **S3**.

A PoC deste repositório reproduz fielmente a **borda + ingestão** e prepara o
caminho para a nuvem (a bridge MQTT, §10.4, conecta o Mosquitto ao IoT Core).

---

## 6. As entidades e seus papéis

O ponto central da refatoração foi dar a **cada entidade um papel único e bem
definido**. Cada uma vive em seu próprio módulo do pacote `qar_poc`:

| Entidade | Módulo | Papel (uma frase) | Analogia na nuvem |
|---|---|---|---|
| **Contrato** | `contrato.py` | A "língua" comum: schema, tópico, validação, ULID | Schema/registro de dados |
| **Sensor** | `sensor.py` | A "Coisa": mede e produz uma leitura | ESP32 + sensores |
| **Transporte** | `transporte.py` | Fala MQTT com o broker (conectar/publicar) | SDK do dispositivo |
| **Gateway** | `gateway.py` | Concentra os sensores de um site em 1 conexão | Gateway de borda |
| **Métricas** | `metricas.py` | Observabilidade: conta e mede | CloudWatch |
| **Coordenador** | `coordenador.py` | Plano de controle: monta topologia e orquestra | Orquestração/IaC |
| **Config** | `config.py` | Configuração imutável e transportável | Parâmetros/env |
| **Sink** | `sink.py` | Ingestor: valida e detecta perdas | Lambda de validação |

Essa separação é o que torna a PoC **"distribuída por papéis"**: trocar o
transporte (MQTT → HTTP) não mexe no sensor; trocar o sensor não mexe no
gateway; e assim por diante.

---

## 7. Estrutura de pastas do repositório

```text
Iot_qualidade_do_ar/
├── ARQUITETURA.md              ◄─ ESTE documento (visão completa do sistema)
├── README.md                   Apresentação do projeto (Lourenço)
│
├── docs/                       Modelagem, estimativa, diagrama, slides (Wilson/Lourenço)
│   ├── modelagem_dados.json    Contrato de dados v1.0 (fonte de verdade)
│   ├── estimativa_carga.md     Cálculo de volumetria (5k–100k sensores)
│   ├── estimativa_carga.xlsx   Planilha de cenários
│   ├── arquitetura_solucao.pdf Diagrama visual
│   └── apresentacao_slides.pdf Slides
│
├── infra/
│   ├── aws/
│   │   └── planejamento_servicos.md   Plano de nuvem: IoT Core, SQS, Lambda... (Wilson)
│   │
│   └── server_config/          ◄─ ESCOPO DO HIGOR: infraestrutura local
│       ├── docker-compose.yml  Stack: Mosquitto + Sink + Gerador + ThingsBoard + PostgreSQL
│       ├── .env.example        Variáveis do compose (modelo)
│       ├── setup_ubuntu_broker.sh   Provisiona um broker endurecido numa VM Ubuntu
│       ├── gerar_certs.sh       Gera CA/certs de teste para TLS
│       └── mosquitto/config/
│           ├── mosquitto.conf          Configuração tunada do broker
│           ├── aclfile.example         Modelo de ACL (menor privilégio)
│           └── bridge.conf.example     Modelo de bridge borda→nuvem
│
├── firmware/                   Firmware do ESP32 (evolução da Ativ. 2)
│
└── poc/                        ◄─ ESCOPO DO HIGOR: prova de conceito de carga
    ├── ingestao_teste.py       CLI do gerador de carga (casca)
    ├── consumidor_metricas.py  CLI do sink de métricas (casca)
    ├── payload_exemplo.json    Exemplo canônico do contrato v1.0
    ├── requirements.txt        Dependências (paho-mqtt)
    ├── Dockerfile              Imagem do gerador/sink para o compose
    ├── .dockerignore
    ├── .env.example            Variáveis da PoC (modelo)
    ├── README.md               Guia rápido da PoC
    └── qar_poc/                O pacote com as entidades (o "cérebro")
        ├── __init__.py         Documentação e exports do pacote
        ├── contrato.py         Schema v1.0, tópico, validação, ULID
        ├── sensor.py           Dispositivo (a "Coisa")
        ├── transporte.py       ClienteMQTT (camada de comunicação)
        ├── gateway.py          Gateway (concentrador de borda)
        ├── metricas.py         MetricasConexao, agregação, percentis
        ├── config.py           ConfigCarga (configuração picklável)
        ├── coordenador.py      Orquestração (threads e multiprocessos)
        └── sink.py             Ingestor (validação e detecção de perdas)
```

---

## 8. A PoC em detalhe: o pacote `qar_poc`

Aqui explicamos **cada módulo, classe, método e função**. O fluxo de dados é
sempre o mesmo: **Sensor → Gateway → Transporte → Broker → Sink**, com o
**Coordenador** orquestrando e as **Métricas** observando.

### 8.1. `contrato.py` — a fonte única de verdade

Papel: garantir que **todos falem a mesma língua**. Se o contrato mudar, muda
só aqui. Não tem estado nem rede — apenas constantes e funções puras, o que o
torna seguro para qualquer thread/processo.

**Constantes:**
- `SCHEMA_VERSION = "1.0"` — versão do contrato, checada na validação.
- `PREFIXO_TOPICO = "qualidade-ar"`, `SUFIXO_TOPICO = "telemetria"` — as pontas
  fixas do tópico.
- `MEDIDAS` — a tupla das 7 grandezas, na ordem do contrato (co2, tvoc, pm1,
  pm25, pm10, temperatura, umidade).
- `CAMPOS_OBRIGATORIOS` — os campos de topo que toda mensagem precisa ter.
- `GAS_STATUS`, `SENSOR_STATUS` — os valores permitidos (enums) do bloco
  `quality`.

**Funções:**
- `montar_topico(site_id, device_id)` → devolve
  `qualidade-ar/{site_id}/{device_id}/telemetria`. É o tópico onde um
  dispositivo publica.
- `topico_assinatura(site_id="+", device_id="+")` → devolve o filtro de
  assinatura; por padrão, `qualidade-ar/#` (toda a árvore). O sink usa isto.
- `_codificar_base32(valor, tamanho)` → função interna que converte um número
  em texto base32 de Crockford (usada pelo ULID).
- `gerar_ulid(rng, agora_ms=None)` → cria um **ULID** de 26 caracteres:
  48 bits de tempo (ordenável) + 80 bits aleatórios. Vira o `message_id`, a
  chave de **idempotência**. Recebe um `rng` local para não disputar um gerador
  global entre threads.
- `agora_rfc3339()` → o instante atual em UTC no formato do contrato
  (`2026-07-28T06:23:46.124Z`). Vira o `sent_at`.
- `parse_sent_at(valor)` → o inverso: converte o texto do `sent_at` de volta em
  segundos (epoch), para o sink calcular a latência. Devolve `None` se inválido.
- `validar_contrato(msg)` → o **guardião do schema**. Recebe uma mensagem já
  desserializada e devolve `None` se estiver conforme, ou uma **descrição curta
  do primeiro erro** (campo ausente, versão errada, medida faltando, enum
  inválido). É o que o sink usa para contar mensagens inválidas.

### 8.2. `sensor.py` — a entidade "Coisa"

Papel: representar **um sensor físico**. Ele só sabe *medir*; não conhece MQTT.

- `Faixa` (dataclass) → descreve uma grandeza: `minimo`, `maximo`, `passo`
  (variação máxima por leitura) e `casas` (casas decimais; `0` significa que a
  grandeza é serializada como inteiro, como CO₂ e TVOC).
- `FAIXAS` (dict) → o mapa de todas as 7 grandezas para suas faixas plausíveis
  de ambiente interno. As faixas seguem os sensores da Atividade 1 (SCD41 →
  co2/temp/umidade; ENS160 → tvoc; PMS5003 → material particulado).
- `Dispositivo` (classe) → o sensor virtual. Usa `__slots__` para gastar menos
  memória (importa com milhares de instâncias).
  - `__init__(device_id, site_id, seed)` → guarda a identidade, zera a
    `sequence`, cria um gerador aleatório **próprio** (reprodutível e sem lock
    global) e escolhe um ponto de partida aleatório em cada faixa.
  - `_passo(nome)` → avança **uma** grandeza por *random walk* (soma um passo
    aleatório e "prende" o valor dentro da faixa). Devolve inteiro se a faixa
    tem 0 casas, senão float. É o que gera séries **contínuas** (realistas), em
    vez de ruído.
  - `proxima_leitura(prob_degradar)` → produz **uma mensagem completa** no
    contrato v1.0: incrementa a `sequence`, mede todas as grandezas, decide o
    `sensor_status` (às vezes `DEGRADED`/`ERROR`, zerando medidas para exercitar
    o tratamento de nulos), deriva o `gas_status` (`SAFE`/`UNSAFE`/`UNKNOWN`) e
    monta o dicionário final (com `message_id`, `sent_at`, `metadata`).
  - `topico()` → atalho que delega a `contrato.montar_topico`.

### 8.3. `transporte.py` — a camada de comunicação MQTT

Papel: esconder **todo** o `paho-mqtt` atrás de uma interface pequena. Se o
transporte mudar, só este arquivo muda.

- `PAHO_DISPONIVEL` (bool) → indica se a biblioteca está instalada (permite o
  modo `--dry-run` funcionar sem ela).
- `ParametrosConexao` (classe com `__slots__`) → o "pacote" de tudo que uma
  conexão precisa: host, porta, keepalive, qos, usuário/senha, tls, limites de
  inflight/fila e o `client_id`.
- `ClienteMQTT` (classe) → **uma conexão persistente** com medição de latência.
  - `__init__(params, metricas)` → guarda os parâmetros e o objeto de métricas
    daquela conexão; prepara o dicionário `_pendentes` (mid → instante de
    publicação) protegido por um lock.
  - `_on_connect` / `_on_disconnect` → callbacks do paho que atualizam o estado
    `conectado` e contam **reconexões**.
  - `_on_publish` → callback chamado quando o broker confirma (PUBACK). Calcula
    a **latência real** (agora − instante da publicação) e a registra nas
    métricas.
  - `conectar()` → cria o cliente paho (compatível com v1 e v2), configura os
    callbacks, os limites de **backpressure** (`max_inflight`, `max_queued`), a
    **reconexão automática com recuo exponencial**, autenticação e TLS; abre a
    conexão e inicia a *thread de rede* do paho. Devolve `True`/`False`.
  - `publicar(topico, corpo)` → publica um payload já serializado e **traduz o
    resultado em métrica**: sucesso → conta publicada e registra o `mid` para
    medir latência; fila cheia → conta *backpressure*; erro → conta falha.
  - `desconectar()` → encerra a thread de rede e fecha a conexão com segurança.
- `client_id_gateway(prefixo, gateway_id)` → gera um `client_id` único e estável
  por gateway (inclui o PID, importante no modo multiprocessos).

### 8.4. `gateway.py` — o concentrador de borda

Papel: um **gateway** concentra os sensores de **um site** e mantém **uma**
conexão MQTT. É a caixa "gateway" exigida no diagrama da Etapa 3.

- `Gateway(threading.Thread)` → cada gateway roda em sua própria thread.
  - `__init__(...)` → recebe seus dispositivos, os parâmetros de conexão, o
    intervalo, o evento de parada e o instante de início da janela. Cria o
    **seu** objeto de métricas e o **seu** `ClienteMQTT` (com um `client_id`
    único).
  - `sites` (property) → o conjunto de sites que ele atende (normalmente um);
    útil para logs/relatório.
  - `run()` → o coração do gateway. Se não for dry-run, conecta. Depois monta um
    **min-heap** com um **deslocamento de fase** por sensor: o sensor *i* de *n*
    começa em `(i/n) × intervalo`, espalhando as publicações ao longo da janela
    (isso achata o pico no broker e reduz a latência). Em laço: pega o próximo
    sensor a vencer, dorme até a hora, gera a leitura, publica (ou só serializa,
    no dry-run) e reagenda para `+intervalo`. Ao parar, desconecta.
- `_monotonic()` → pequeno wrapper de `time.monotonic()` (relógio que nunca
  "anda para trás"), isolado para facilitar testes.

### 8.5. `metricas.py` — observabilidade

Papel: coletar e agregar os números que **provam** o comportamento do sistema.

- `MetricasConexao` (dataclass) → os contadores de **uma** conexão/gateway:
  `publicadas`, `falhas`, `backpressure`, `reconexoes`, `conectado` e um buffer
  de latências. **Decisão de desempenho:** cada gateway tem o seu; no caminho
  quente só há incrementos locais, **sem lock compartilhado**.
  - `registrar_latencia(ms)` → chamado pela thread de rede; guarda a amostra
    (com limite de memória) sob um pequeno lock (o único do caminho quente).
  - `coletar_latencias()` → retira e devolve as latências acumuladas (esvazia o
    buffer). O coordenador chama isso a cada tick do painel.
- `percentil(ordenada, pct)` → calcula um percentil por interpolação linear
  (p50/p95/p99). Espera a lista já ordenada.
- `SnapshotAgregado` (dataclass) → uma "fotografia" somada de todas as conexões
  em um instante (publicadas, falhas, conectados, percentis). `como_dict()`
  serializa para relatório.
- `agregar(conexoes, latencias_janela)` → soma os contadores de todas as
  conexões e calcula os percentis da janela. É como o painel vira um número só.

### 8.6. `config.py` — configuração imutável e transportável

- `ConfigCarga` (dataclass) → carrega **tudo** que o coordenador precisa, só com
  tipos primitivos. Por ser de primitivos, é **picklável** — requisito para
  enviá-la aos processos filhos no modo multiprocessos.
  - `params_base()` → devolve o dicionário de parâmetros de conexão comuns a
    todos os gateways (sem o `client_id`, que é individual).

### 8.7. `coordenador.py` — o plano de controle

Papel: **orquestrar** o experimento. Ele não publica nada; coordena quem
publica. Tem os dois modos de paralelismo.

**Funções de topologia:**
- `dispositivos_do_gateway(cfg, gid)` → devolve, de forma **determinística**, os
  sensores do gateway `gid` (mesmos device_ids e seeds sempre, em threads ou
  processos). Reparte os sensores em blocos contíguos; cada gateway é um site.
- `criar_gateways(cfg, parar, inicio_janela, filtro=None)` → cria os objetos
  `Gateway` cujo id passa pelo `filtro` (usado no sharding por processo).
- `_iniciar_com_rampa(gateways)` → sobe os gateways **escalonadamente** (evita
  abrir todas as conexões no mesmo instante).

**Painel:**
- `_imprimir_cabecalho()`, `_fmt(n)`, `_imprimir_linha(...)` → formatam a tabela
  ao vivo (tempo, conexões, enviadas, msg/s, falhas, backpressure, p50/p95/p99).

**Modo threads:**
- `Coordenador` (classe) → orquestra os gateways **deste** processo.
  - `__init__(cfg)` → guarda a config e cria o evento de parada.
  - `_instalar_sinais()` → faz `Ctrl+C`/`SIGTERM` pedirem parada graciosa.
  - `rodar_local()` → monta os gateways, sobe com rampa, e roda o **laço do
    reporter**: a cada período agrega métricas, calcula a vazão da janela,
    imprime a linha e checa o prazo. Ao fim, junta as threads e emite o
    relatório final.

**Modo multiprocessos:**
- `rodar_shard_processo(cfg, indice, fila, parar_mp)` → o alvo de **cada
  processo filho**. Roda os gateways cujo `gid % processos == indice` (sharding
  por site) e **empurra snapshots** de métricas para a `fila` (comunicação
  entre processos). Ignora `Ctrl+C` (quem coordena o fim é o pai). No final,
  envia um snapshot marcado como `final`.
- `rodar_multiprocessos(cfg)` → o **processo pai**. Cria a fila e o evento
  compartilhado, dispara P processos (contexto `spawn`, compatível com
  Windows), e roda o laço que **drena a fila**, agrega os snapshots de todos os
  shards e imprime o painel unificado. Ao fim, aguarda os relatórios finais e
  soma tudo.

**Relatório e dispatcher:**
- `relatorio_final(cfg, conexoes, decorrido, latencias)` → soma os contadores
  das conexões locais e chama o formatador.
- `_relatorio_final_valores(cfg, total, falhas, bp, decorrido, latencias)` →
  imprime o resumo final (modo, duração, publicadas, vazão, falhas,
  backpressure, latências) e, se pedido, salva um **relatório JSON**.
- `executar(cfg)` → o **ponto de entrada**: valida o paho, imprime o resumo e
  escolhe o modo (threads ou multiprocessos).
- `_imprimir_resumo(cfg)` → o cabeçalho com destino, sensores, gateways,
  paralelismo, intervalo, QoS e **taxa alvo**.

### 8.8. `sink.py` — o ingestor/validador

Papel: assinar a telemetria e fazer, localmente, o papel da **Lambda de
validação**: conferir o contrato, **detectar lacunas** e medir latência.

- `EstadoSink` (dataclass) → o estado observado: `recebidas`, `invalidas`,
  `lacunas`, `reordenadas`, `duplicadas`, `bytes_total`, amostras de latência,
  a **última `sequence` por dispositivo** (para achar lacunas), o conjunto de
  `message_id` já vistos (para achar duplicatas) e um lock.
- `ConfigSink` (dataclass) → configuração do consumidor (host, tópico, qos, tls,
  duração...).
- `Ingestor` (classe):
  - `__init__(cfg)` → prepara o estado e o evento de parada.
  - `_on_connect(...)` → ao conectar, **assina** o tópico e avisa no console.
  - `_on_message(...)` → o coração do sink. Para cada mensagem: desserializa;
    **valida o contrato** (via `contrato.validar_contrato`); calcula a latência
    fim-a-fim; detecta **duplicata** (`message_id` repetido); e detecta
    **lacuna/reordenação** comparando a `sequence` com a última vista daquele
    dispositivo (se pulou de 5 para 8, faltaram 6 e 7). Tudo sob o lock, com
    janelas deslizantes para limitar memória.
  - `executar()` → conecta, assina, roda o painel e imprime o resumo.
  - `_painel()` → a tabela ao vivo (recebidas, msg/s, dispositivos, lacunas,
    duplicadas, inválidas, latência média).
  - `_resumo()` → o quadro final, incluindo a **perda estimada em %** e os
    percentis de latência. É a evidência principal de "não há perda".

---

## 9. Os entrypoints de linha de comando

Os dois scripts na raiz de `poc/` são apenas **cascas finas**: fazem o
*parsing* dos argumentos e chamam o pacote. Toda a lógica está em `qar_poc`.

### `ingestao_teste.py`
- `parse_args(argv)` → define e lê todas as flags e monta um `ConfigCarga`.
  Regras importantes: `--cenario` sobrepõe `--sensores`; `--conexoes` é um
  **apelido retrocompatível** de `--gateways`; nunca há mais gateways que
  sensores; `--processos` é limitado ao número de gateways.
- `main(argv)` → chama `qar_poc.coordenador.executar(cfg)`.

Flags principais:

| Flag | Padrão | Função |
|---|---|---|
| `--sensores` | 1000 | dispositivos virtuais (volumetria) |
| `--cenario` | — | preset 5000/10000/50000/100000 |
| `--gateways` | 100 | concentradores = sites = conexões MQTT |
| `--processos` | 1 | processos paralelos (sharding de gateways) |
| `--intervalo` | 60 | segundos entre leituras de cada sensor |
| `--qos` | 1 | qualidade de serviço MQTT |
| `--duracao` | 0 | duração (0 = contínuo) |
| `--tls` / `--tls-inseguro` | off | MQTT sobre TLS |
| `--dry-run` | off | não conecta; mede só a geração |
| `--relatorio` | — | salva o resultado em JSON |

### `consumidor_metricas.py`
- `parse_args(argv)` → lê as flags do sink (host, tópico, qos, tls, duração) e
  monta um `ConfigSink`. O tópico padrão vem de `contrato.topico_assinatura()`.
- `main(argv)` → cria e executa um `Ingestor`.

---

## 10. A infraestrutura em detalhe

Tudo em `infra/server_config/`. Reproduz localmente a **borda + ingestão**:
onde a nuvem usa AWS IoT Core, aqui usamos Mosquitto; onde usa dashboards,
usamos ThingsBoard + PostgreSQL.

### 10.1. `docker-compose.yml`

Sobe o ambiente com **perfis** (para controlar custo/recursos):

| Serviço | Imagem | Papel | Perfil |
|---|---|---|---|
| `mosquitto` | `eclipse-mosquitto:2.0` | broker MQTT (alvo da carga) | núcleo |
| `sink` | build de `poc/` | validador **sempre ativo** (assina e mede) | núcleo |
| `gerador` | build de `poc/` | teste de carga **sob demanda** | `carga` |
| `postgres` | `postgres:16-alpine` | banco do ThingsBoard | `plataforma` |
| `thingsboard` | `thingsboard/tb-node:3.8.1CE` | dashboards/alertas | `plataforma` |

Detalhes importantes:
- O `mosquitto` monta a config como **somente leitura**, tem `ulimits.nofile`
  elevado (cada conexão gasta um descritor) e um **healthcheck** que publica uma
  mensagem de teste.
- O `sink` e o `gerador` usam a **mesma imagem** (`Dockerfile` do `poc/`) e só
  sobem depois que o Mosquitto está **saudável** (`depends_on: condition:
  service_healthy`).
- O `sink` é **núcleo**: subir o ambiente já o deixa observando a ingestão.
- O `thingsboard` usa `postgres` como banco separado (fiel à Atividade 1); na
  primeira subida instala o schema (`INSTALL_TB=true`).

**Modos de uso:**
```bash
docker compose up -d mosquitto sink      # ingestão pronta (broker + validador)
docker compose --profile carga run --rm gerador \
  ingestao_teste.py --host mosquitto --cenario 10000 --gateways 100 --duracao 120
docker compose --profile plataforma up -d   # + ThingsBoard e PostgreSQL
```

### 10.2. `mosquitto/config/mosquitto.conf`

Configuração **tunada para milhares de conexões**. Parâmetros e o porquê:

| Parâmetro | Valor | Motivo |
|---|---|---|
| `persistence` | true | não perde sessões/retidas ao reiniciar |
| `max_connections` | -1 | sem teto artificial; o limite real é o SO |
| `max_inflight_messages` | 100 | vazão sob rajada mantendo QoS 1 |
| `max_queued_messages` | 2000 | protege a memória quando um cliente atrasa |
| `queue_qos0_messages` | false | descarta o mais antigo, preservando o recente |
| `max_packet_size` | 8192 | contrato ocupa ~420 B; barra pacotes anômalos |
| `sys_interval` | 10 | publica métricas internas em `$SYS` a cada 10 s |

O listener `1883` aceita conexão **anônima** (apenas para a PoC em rede
isolada); há um bloco comentado para o listener **8883 (TLS)** e para
autenticação por senha + ACL.

### 10.3. `mosquitto/config/aclfile.example`

Modelo de **autorização por menor privilégio**: cada dispositivo só publica no
**seu** tópico (`pattern write qualidade-ar/+/%u/telemetria`); o `ingestor` só
lê; o `operador` só vê as métricas `$SYS`. É o mesmo princípio das políticas IoT
por `device_id` no plano da AWS.

### 10.4. `mosquitto/config/bridge.conf.example`

Modelo de **bridge** (ponte) borda→nuvem — uma **estratégia de comunicação**
distribuída clássica: o broker local encaminha `qualidade-ar/#` para um broker
superior (regional ou **AWS IoT Core**). Com `cleansession false`, a borda
continua recebendo mesmo se o enlace com a nuvem cair, e reenvia depois
(resiliência). É o caminho natural para plugar esta PoC no plano do Wilson.

### 10.5. `setup_ubuntu_broker.sh`

Provisiona um broker Mosquitto **endurecido e ajustado** numa VM Ubuntu, de
forma **idempotente**. Funções:
- `instalar_pacotes()` → instala `mosquitto`, clientes e `openssl`.
- `ajustar_kernel()` → o ajuste central de **concorrência**: eleva
  `fs.file-max`, `somaxconn`, `tcp_max_syn_backlog`, a faixa de portas efêmeras,
  e o `LimitNOFILE` do serviço (padrão 200000). Cada conexão MQTT gasta um
  descritor, então esse teto define quantos sensores cabem.
- `instalar_config()` → escreve a config tunada em
  `/etc/mosquitto/conf.d/qar-broker.conf` (mesmos parâmetros do
  `mosquitto.conf`), com ou sem autenticação.
- `configurar_auth()` → (com `--auth`) cria usuário via `mosquitto_passwd` e uma
  **ACL de menor privilégio**.
- `configurar_tls()` → (com `--tls`) gera uma **CA de teste** e habilita o
  listener 8883.
- `ativar_servico()` → valida, reinicia e confirma que o serviço subiu.
- `main()` → encadeia tudo e imprime um resumo com um teste rápido.

### 10.6. `gerar_certs.sh`

Gera uma **CA e um certificado de servidor de teste** para habilitar o listener
TLS 8883 no ambiente Docker, sem precisar da VM. Deixa claro que é uma CA de
**teste** (produção usa autoridade real e, idealmente, mTLS por dispositivo).

### 10.7. `poc/Dockerfile`

Empacota o `qar_poc` e os dois entrypoints numa imagem Python enxuta
(`python:3.12-slim`), instala as dependências em camada separada (aproveita
cache), roda como **usuário não-root** e deixa o comando concreto (sink ou
gerador) por conta do compose. É o que permite o ambiente já subir "pronto".

---

## 11. Concorrência, paralelismo e comunicação

Esta seção reúne as estratégias que o trabalho aplica para **escalar, reduzir
latência e não perder mensagens** — os pontos que a Atividade 3 mais valoriza.

### 11.1. Sensores virtuais × conexões reais
Uma máquina não sustenta 100.000 conexões TCP reais, e não é isso que importa:
o que dimensiona a nuvem é a **taxa de mensagens** e o **formato**. Por isso
separamos `--sensores` (volumetria) de `--gateways` (conexões reais que os
multiplexam). A taxa é reproduzida fielmente; a contagem de conexões é limitada
pela máquina, não pela arquitetura.

### 11.2. Espalhamento de fase (latência)
Se todos os sensores publicassem em `t=0`, haveria um pico enorme a cada
intervalo. Cada gateway dá a seus sensores um **deslocamento de fase** fixo,
espalhando as publicações ao longo da janela. Isso **achata o pico** e mantém a
latência de PUBACK baixa. É a técnica de maior impacto no desempenho.

### 11.3. Concorrência com threads (I/O)
Cada gateway roda em uma thread com **uma conexão persistente**. Como MQTT é
I/O-bound, as threads passam a maior parte do tempo esperando a rede (o GIL do
Python é liberado nesse momento), então muitas conexões progridem de fato em
paralelo. No caminho quente **não há lock compartilhado**: cada gateway tem suas
próprias métricas.

### 11.4. Paralelismo com processos (CPU + distribuição)
Com `--processos P`, os gateways são **repartidos (sharding) por site** entre P
processos independentes (contexto `spawn`, compatível com Windows). Isso usa
**vários núcleos** para gerar payload e distribui as conexões. É a demonstração
de **escala horizontal**: mais processos = mais capacidade, como adicionar mais
instâncias de Lambda/worker na nuvem.

### 11.5. Comunicação entre processos
No modo multiprocessos, cada filho **empurra snapshots de métricas** para o pai
por uma `multiprocessing.Queue`, e o pai **agrega e imprime** um painel
unificado. O encerramento é coordenado por um `Event` compartilhado. É uma
estratégia de comunicação clara: os workers produzem, o coordenador consome.

### 11.6. Backpressure (não estourar sob pico)
Cada conexão tem limites de mensagens **em trânsito** (`max_inflight`) e
**enfileiradas** (`max_queued`). Quando a fila enche, `publish()` recusa e o
sistema conta *backpressure* em vez de consumir memória sem limite — o mesmo
princípio de amortecimento que a fila **SQS** oferece na nuvem.

### 11.7. Sem perda + idempotência
`QoS 1` garante entrega "pelo menos uma vez"; o `message_id` (ULID) permite
**deduplicar** as eventuais repetições; e a `sequence` crescente por
dispositivo permite ao sink **detectar lacunas**. Juntos, dão entrega confiável
sem duplicar o efeito.

### 11.8. Particionamento por site
Agrupar dispositivos por `site_id` (um gateway por site) espelha a **chave de
partição do S3** (`year/month/day/hour/site_id`) do plano de armazenamento.
Distribui a escrita e facilita consultas por local.

---

## 12. Segurança

- **Transporte:** a PoC local usa `1883` anônimo (rede isolada). Para expor,
  habilita-se o listener `8883` (TLS) e a autenticação por senha + ACL. O
  `setup_ubuntu_broker.sh --auth --tls` e o `gerar_certs.sh` automatizam isso.
- **Menor privilégio:** o `aclfile.example` restringe cada dispositivo ao seu
  tópico, espelhando as políticas IoT por `device_id` da AWS.
- **Produção:** o padrão é **mTLS** (certificado por dispositivo). A bridge e o
  plano da AWS já preveem isso.
- **Sem segredos no repositório:** o `.gitignore` ignora `*.env`, `*.key`,
  `*.crt`, `*.pem`. As credenciais vêm de variáveis de ambiente
  (`MQTT_USER`/`MQTT_PASSWORD`), nunca do código.
- **Contrato:** o payload não transporta credenciais, chaves nem dados pessoais
  — regra explícita da modelagem.

---

## 13. Como executar tudo (passo a passo)

**Pré-requisitos:** Docker Desktop e Python 3.10+.

```bash
# 1) Subir o broker + o validador (ambiente de ingestão pronto)
cd infra/server_config
cp .env.example .env
docker compose up -d mosquitto sink
docker compose logs -f sink      # acompanhe a ingestão em tempo real

# 2) (Opcional) Rodar a PoC direto do host, em outro terminal
cd ../../poc
pip install -r requirements.txt
python consumidor_metricas.py --host localhost         # sink no host
python ingestao_teste.py --host localhost --sensores 5000 --duracao 120

# 3) Ou rodar o gerador conteinerizado (sob demanda)
cd ../infra/server_config
docker compose --profile carga run --rm gerador \
  ingestao_teste.py --host mosquitto --cenario 10000 --gateways 100 --duracao 120

# 4) Paralelismo real (multiprocessos)
python ../../poc/ingestao_teste.py --host localhost --cenario 100000 \
  --gateways 300 --processos 4 --duracao 120 --relatorio relatorio_100k.json

# 5) Plataforma completa (ThingsBoard + PostgreSQL)
INSTALL_TB=true docker compose --profile plataforma up -d   # 1ª vez
#   UI em http://localhost:8080

# 6) Encerrar
docker compose --profile plataforma --profile carga down
```

**Sem broker** (só validar a geração):
```bash
python poc/ingestao_teste.py --dry-run --sensores 10000 --duracao 10
```

---

## 14. Resultados validados

Execuções reais contra o Mosquitto conteinerizado (Docker), QoS 1:

| Cenário de teste | Publicadas | Recebidas | Lacunas | Duplicadas | Inválidas | Vazão |
|---|---:|---:|---:|---:|---:|---:|
| Threads · 1.000 sensores · 20 gateways | 4.720 | 4.720 | **0** | 0 | 0 | ~470 msg/s |
| **Multiprocessos (4)** · 2.000 sensores · 24 gateways | 11.788 | 11.788 | **0** | 0 | 0 | ~1.000 msg/s |
| Conteinerizado · 3.000 sensores · 30 gateways | 16.170 | 16.170 | **0** | 0 | 0 | ~1.470 msg/s |

Observações:
- **Perda zero** em todos os cenários, sob QoS 1 — valida a escolha de QoS do
  contrato e a detecção de lacunas por `sequence`.
- **Tamanho medido: 419 bytes/mensagem**, batendo **exatamente** com a premissa
  de serialização da `docs/estimativa_carga.md` do Wilson — uma checagem de
  coesão entre a PoC e o planejamento.
- O modo multiprocessos agregou corretamente as métricas de 4 processos via
  fila, demonstrando a distribuição.

---

## 15. Respostas às Questões para Discussão

| Questão | Resposta (local + nuvem) |
|---|---|
| **Como garantir escalabilidade?** | Borda: mais `--gateways` e `--processos` (sharding por site), com espalhamento de fase. Nuvem: IoT Core gerenciado, SQS amortecendo picos, Lambda com concorrência elástica. |
| **Como evitar perda de mensagens?** | QoS 1 + `message_id` (idempotência) + `sequence` (detecção de lacunas, validada em **0**). Nuvem: SQS + DLQ + escrita idempotente. |
| **Como armazenar grandes volumes?** | Estado atual no DynamoDB; histórico bruto/Parquet no S3, particionado por `site_id`, com lifecycle (Standard→Glacier→expiração). |
| **Qual banco e por quê?** | DynamoDB (baixa latência, escala gerenciada) para estado/agregados; S3 (barato, ilimitado) como data lake. Localmente, ThingsBoard + PostgreSQL para dashboards. |
| **Como monitorar?** | Local: o **sink** (vazão, lacunas, latência) + métricas `$SYS` do broker. Nuvem: CloudWatch (fila, erros, throttling, DLQ). |
| **Como reduzir custos?** | Perfis do compose (subir só o necessário); fila in-memory no dev; retenção/lifecycle no S3; DynamoDB só com estado, não com a série bruta. |
| **Como garantir segurança?** | TLS/mTLS, ACL por dispositivo, IAM de menor privilégio, sem segredos no repo, criptografia em repouso. |

---

## 16. Da PoC local para a produção na AWS

A transição é direta porque a PoC já fala o contrato e os papéis certos:

1. Trocar o **Mosquitto** pelo **AWS IoT Core** (broker gerenciado). O
   `--host`/`--porta`/`--tls` do gerador apontam para o endpoint do IoT Core; a
   bridge (`bridge.conf.example`) faz a ponte se houver um broker de borda.
2. Cadastrar cada dispositivo com **certificado X.509** (mTLS) e política por
   `device_id` — o mesmo modelo do `aclfile.example`.
3. Uma **regra do IoT Core** encaminha `qualidade-ar/#` para a **SQS**.
4. A **Lambda** faz o que o **sink** faz na PoC (validar via contrato,
   deduplicar por `message_id`), e ainda grava no **DynamoDB** e no **S3**.
5. **CloudWatch** assume o papel de observabilidade do sink.

Ou seja: cada entidade da PoC tem um correspondente direto na nuvem, o que torna
o plano do Wilson **verificável** já na fase local.

---

## 17. Limitações e trabalhos futuros

- Os sensores são **virtuais e multiplexados**; a contagem de conexões TCP reais
  é limitada pela máquina de teste, não representa 1 conexão por sensor.
- Os dados de medição são **fictícios** (random walk em faixas plausíveis), não
  leituras reais de SCD41/ENS160/PMS5003.
- A latência fim-a-fim só é confiável quando publicador e consumidor
  compartilham relógio (na PoC, a mesma máquina).
- A PoC exercita a **ingestão** (borda → broker → sink). O processamento,
  DynamoDB, S3 e a deduplicação do plano da AWS **não** são executados aqui — mas
  o `message_id` e a `sequence` já estão prontos para suportá-los.
- **Futuro:** gravar a telemetria num banco de séries temporais local; medir a
  latência com relógio do broker; e conectar de fato a bridge a um IoT Core de
  teste.

---

## 18. Glossário

- **ACL** — lista de controle de acesso (quem pode publicar/assinar o quê).
- **Broker** — servidor MQTT que roteia mensagens entre publicadores e
  assinantes.
- **DLQ** — *Dead Letter Queue*, fila para mensagens que falharam o
  processamento.
- **Gateway** — concentrador de borda que agrega sensores e mantém o uplink.
- **Idempotência** — processar duas vezes tem o mesmo efeito de processar uma.
- **mTLS** — TLS mútuo; cliente e servidor apresentam certificados.
- **PUBACK** — o "recibo" que o broker envia ao confirmar uma mensagem QoS 1.
- **QoS** — nível de garantia de entrega do MQTT (0/1/2).
- **Sharding** — repartir a carga em fatias independentes (aqui, por site).
- **Sink** — o consumidor final que valida e mede a ingestão.
- **ULID** — identificador único ordenável por tempo (usado como `message_id`).
- **Volumetria** — o volume de dados/mensagens esperado (a estimativa de carga).

---

> **Autoria desta entrega (Atividade 3):** a prova de conceito (`poc/`) e a
> infraestrutura local (`infra/server_config/`) são contribuição do **Higor**,
> em coesão com a modelagem e o plano de nuvem do **Wilson** e com os diagramas
> e a compilação do **Lourenço**.
