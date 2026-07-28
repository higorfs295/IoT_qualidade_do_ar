# Prova de Conceito — Gerador de Carga de Ingestão

Prova de conceito da **Atividade 3** que demonstra e mede, localmente, o fluxo
de ingestão planejado para milhares de sensores de qualidade do ar. Ela evolui
a comunicação MQTT da Atividade 2 (um ESP32 publicando a cada 5 s) para o
cenário de produção: **milhares de dispositivos publicando uma leitura
consolidada a cada 60 s**, exatamente no contrato de dados definido em
[`docs/modelagem_dados.json`](../docs/modelagem_dados.json).

O foco da atividade é o **planejamento**; esta PoC é o complemento opcional que
torna o planejamento verificável. Em vez de descrever a volumetria apenas no
papel, o gerador reproduz a taxa de mensagens e permite observar, com números,
como a arquitetura se comporta sob carga.

> 📘 Para a explicação completa da arquitetura — cada pasta, arquivo, classe,
> método e função, além das estratégias de concorrência/paralelismo/comunicação
> — veja [`../ARQUITETURA.md`](../ARQUITETURA.md).

## Relação com as atividades anteriores

| Aspecto | Atividade 2 (POC MQTT) | Atividade 3 (esta PoC de carga) |
|---|---|---|
| Emissor | 1 ESP32 no Wokwi | milhares de sensores virtuais em software |
| Frequência | 5 s (para facilitar a demo) | 60 s (operação planejada) |
| Payload | 3 mensagens de texto (`temp`, `umid`, `co2`) | 1 JSON consolidado no schema v1.0 |
| Tópico | `INF01/temp`, `INF01/umid`, `INF01/co2` | `qualidade-ar/{site_id}/{device_id}/telemetria` |
| QoS | 0 | 1 (idempotência por `message_id`) |
| Broker | HiveMQ Cloud | Mosquitto local ([`../infra/server_config`](../infra/server_config)) |
| Objetivo | provar a comunicação | medir escalabilidade, perda e latência |

O contrato de payload, a política de retenção e a volumetria são de autoria do
Wilson ([`docs/modelagem_dados.json`](../docs/modelagem_dados.json),
[`docs/estimativa_carga.md`](../docs/estimativa_carga.md)) e o plano de nuvem
está em [`infra/aws/planejamento_servicos.md`](../infra/aws/planejamento_servicos.md).
Esta PoC **consome** essas definições em vez de recriá-las — o gerador emite
precisamente o schema v1.0, e o Mosquitto local faz o papel que o **AWS IoT
Core** exerce na arquitetura de produção.

## Conteúdo

A PoC é organizada por **papéis (entidades)**, cada um em seu módulo do pacote
`qar_poc`. Os dois scripts na raiz são apenas cascas de linha de comando.

```text
poc/
├── ingestao_teste.py        # CLI do gerador de carga (casca)
├── consumidor_metricas.py   # CLI do sink de métricas (casca)
├── payload_exemplo.json     # exemplo canônico do contrato v1.0
├── requirements.txt         # paho-mqtt >= 2.0
├── Dockerfile               # imagem do gerador/sink para o docker-compose
├── .dockerignore
├── .env.example             # modelo de variáveis de ambiente
├── README.md
└── qar_poc/                 # o pacote com as entidades (o "cérebro")
    ├── contrato.py          # schema v1.0, tópico, validação, ULID (fonte única)
    ├── sensor.py            # Dispositivo — a "Coisa" que mede
    ├── transporte.py        # ClienteMQTT — camada de comunicação (paho)
    ├── gateway.py           # Gateway — concentrador de um site (1 conexão)
    ├── metricas.py          # observabilidade (contadores, percentis)
    ├── config.py            # ConfigCarga — configuração picklável
    ├── coordenador.py       # plano de controle (threads e multiprocessos)
    └── sink.py              # Ingestor — valida e detecta perdas
```

Cada entidade tem um papel único: o **Sensor** só mede; o **Gateway** concentra
os sensores de um site e transporta; o **Coordenador** orquestra; o **Sink**
valida. Detalhe função a função em [`../ARQUITETURA.md`](../ARQUITETURA.md) §8.

## Como o gerador trata concorrência, paralelismo e latência

Uma única máquina não sustenta 100.000 conexões TCP reais, e não é isso que
precisa ser reproduzido: o que importa é a **taxa de mensagens por segundo** e o
**formato**. Por isso o gerador separa três conceitos:

- `--sensores` — quantos dispositivos virtuais existem (a volumetria);
- `--gateways` — quantos concentradores de borda os multiplexam
  (**1 gateway = 1 site = 1 conexão MQTT**);
- `--processos` — quantos processos paralelos repartem os gateways (sharding).

Cada **gateway** roda em sua própria *thread*, dono de **uma** conexão paho
persistente (reaproveitada, sem reconectar por mensagem) e dos sensores do seu
site. A técnica central é o **espalhamento de fase**: cada sensor recebe um
deslocamento fixo dentro da janela de envio, de modo que os N sensores **não
disparam todos em `t=0`**. Espalhar as publicações ao longo da janela reduz o
pico instantâneo no broker, mantém a latência de PUBACK baixa e evita filas.

```text
Janela de 60 s, 6 sensores em um gateway:
t:  0s     10s    20s    30s    40s    50s    60s
    s0     s1     s2     s3     s4     s5     s0 → ...

gateways (threads):        heap por vencimento          métricas locais
  gw0 [site-0] ── publica no próximo devido ──▶ paho client ──▶ broker
  gw1 [site-1] ── (dorme até o próximo)      ──▶ paho client ──▶ broker
  gw2 [site-2] ──                            ──▶ paho client ──▶ broker

com --processos 4: os gateways são repartidos entre 4 processos (sharding por
site); cada processo reporta métricas ao pai por uma fila.
```

Outras decisões de desempenho e robustez:

- **Sem lock no caminho quente.** Cada gateway tem métricas locais; o *reporter*
  agrega por soma de *snapshots*. Cada sensor tem seu próprio RNG.
- **Paralelismo real (`--processos`).** Os gateways são distribuídos entre
  processos independentes (contexto `spawn`, compatível com Windows), usando
  vários núcleos — demonstra escala horizontal, com comunicação por fila.
- **Backpressure explícito.** `max_inflight` e `max_fila` limitam mensagens em
  trânsito e enfileiradas por conexão. Quando a fila enche, `publish()` retorna
  `MQTT_ERR_QUEUE_SIZE`, contado como *backpressure* em vez de estourar a
  memória — o mesmo princípio da fila SQS na nuvem.
- **Latência real.** A latência medida é a de **PUBACK** (`publish` → `on_publish`
  via `mid`), não o tempo de enfileirar. É a métrica que reflete o broker.
- **Reconexão automática** com recuo exponencial e **rampa de conexão**
  escalonada na subida.
- **Encerramento gracioso.** `Ctrl+C`/`SIGTERM` para os gateways, fecha as
  conexões e imprime o relatório final.
- **`--dry-run`.** Funciona sem broker: exercita apenas a geração de payload e
  mede a vazão do gerador — útil para validar a máquina antes do teste real.

## Instalação

```bash
cd poc
python -m venv .venv && source .venv/bin/activate    # opcional
pip install -r requirements.txt
```

## Uso

```bash
# 1) Validar geração de payload sem broker (mede a vazão do gerador)
python ingestao_teste.py --dry-run --sensores 10000 --duracao 10

# 2) Subir o broker local (em outro terminal)
cd ../infra/server_config && docker compose up -d mosquitto

# 3) Observar a ingestão (sink de métricas)
python consumidor_metricas.py --host localhost

# 4) Gerar carga contra o broker (schema v1.0, QoS 1)
python ingestao_teste.py --host localhost --sensores 5000 --duracao 120

# Presets de volumetria alinhados a docs/estimativa_carga.md
python ingestao_teste.py --host localhost --cenario 50000 --gateways 200

# Paralelismo real: 4 processos repartindo os gateways
python ingestao_teste.py --host localhost --cenario 100000 --gateways 300 \
    --processos 4 --relatorio relatorio_100k.json
```

Ou, sem instalar nada no host, tudo conteinerizado (ver
[`../infra/server_config/README.md`](../infra/server_config/README.md)):

```bash
cd ../infra/server_config
docker compose up -d mosquitto sink          # broker + validador prontos
docker compose --profile carga run --rm gerador \
  ingestao_teste.py --host mosquitto --cenario 10000 --gateways 100 --duracao 120
```

Parâmetros principais (`--help` lista todos):

| Flag | Padrão | Função |
|---|---|---|
| `--sensores` | 1000 | número de dispositivos virtuais |
| `--cenario` | — | preset 5000 / 10000 / 50000 / 100000 |
| `--gateways` | 100 | concentradores de borda (1 gateway = 1 site = 1 conexão) |
| `--processos` | 1 | processos paralelos que repartem os gateways (sharding) |
| `--intervalo` | 60 | segundos entre leituras de cada sensor |
| `--qos` | 1 | QoS MQTT (1 = contrato) |
| `--duracao` | 0 | duração do teste (0 = contínuo) |
| `--tls` / `--tls-inseguro` | off | MQTT sobre TLS |
| `--dry-run` | off | não conecta; mede geração |
| `--relatorio` | — | salva o resultado final em JSON |

> `--conexoes` continua funcionando como **apelido** de `--gateways` (retrocompatível).

## Cenários de volumetria

Taxas derivadas de uma leitura por sensor a cada 60 s, coerentes com
[`docs/estimativa_carga.md`](../docs/estimativa_carga.md):

| Sensores | Média (msg/s) | Pico planejado 2× (msg/s) | Gateways sugeridos | Processos |
|---:|---:|---:|---:|---:|
| 5.000 | 83 | 167 | 50 | 1 |
| 10.000 | 167 | 333 | 100 | 1–2 |
| 50.000 | 833 | 1.667 | 200 | 2–4 |
| 100.000 | 1.667 | 3.333 | 300 | 4+ |

O número de gateways (conexões) é limitado pela máquina de teste, não pela
arquitetura: os sensores são virtuais e multiplexados. A taxa de mensagens, que
é o que dimensiona a nuvem, é reproduzida fielmente.

## Métricas do consumidor e as Questões para Discussão

O `consumidor_metricas.py` fecha o laço e transforma cada questão da atividade em
um número observável:

| Questão da atividade | Como a PoC evidencia |
|---|---|
| Como **evitar perda de mensagens**? | detecção de lacunas por `sequence` por dispositivo; sob QoS 1 as lacunas ficam em zero, sob QoS 0 aparecem |
| Como garantir **escalabilidade**? | aumentar `--sensores`/`--gateways`/`--processos` e observar vazão e latência estáveis |
| Como **monitorar** a solução? | painel ao vivo: vazão, dispositivos ativos, latência, inválidas |
| **Modelagem dos dados** | o consumidor valida o contrato v1.0 campo a campo e conta inválidas |

## Resultados de referência (execuções reais)

Validações contra o Mosquitto conteinerizado (Docker), QoS 1:

| Cenário | Publicadas | Recebidas | Lacunas | Dup. | Inval. | Vazão |
|---|---:|---:|---:|---:|---:|---:|
| Threads · 1.000 sensores · 20 gateways | 4.720 | 4.720 | **0** | 0 | 0 | ~470 msg/s |
| **Multiprocessos (4)** · 2.000 · 24 gateways | 11.788 | 11.788 | **0** | 0 | 0 | ~1.000 msg/s |
| Conteinerizado · 3.000 · 30 gateways | 16.170 | 16.170 | **0** | 0 | 0 | ~1.470 msg/s |

- **Tamanho medido: 419 bytes/mensagem** — bate **exatamente** com a premissa de
  serialização de `docs/estimativa_carga.md` (os 470 bytes de planejamento
  incluem margem para evolução do contrato).
- **Perda zero** sob QoS 1 em todos os cenários valida a escolha de QoS do
  contrato e a detecção de lacunas por `sequence`.
- O modo multiprocessos agregou corretamente as métricas dos 4 processos via
  fila, comprovando a distribuição.

## Limitações

- Os sensores são virtuais e multiplexados; o número de conexões TCP reais é
  limitado pela máquina de teste, não representa 1 conexão por sensor.
- Dados de medição são fictícios, gerados por passeio aleatório dentro de faixas
  plausíveis de ambiente interno; não são leituras reais de SCD41/ENS160/PMS5003.
- A latência fim-a-fim só é confiável quando publicador e consumidor compartilham
  o mesmo relógio (na PoC, a mesma máquina).
- A PoC exercita a **ingestão** (broker → sink). O processamento, a persistência
  em DynamoDB/S3 e a deduplicação descritos no plano da AWS não são executados
  aqui — o `message_id` e a `sequence` já estão presentes para suportá-los.

## Segurança

- A PoC local usa listener anônimo em texto (1883). É adequado somente para rede
  isolada. Para expor o broker, habilite TLS e autenticação — ver
  [`../infra/server_config/README.md`](../infra/server_config/README.md).
- Nenhuma credencial vai para o repositório: use variáveis de ambiente
  (`--usuario`/`--senha` leem `MQTT_USER`/`MQTT_PASSWORD`). O `.gitignore` ignora
  `*.env`, `*.key`, `*.crt` e `*.pem`.
- O payload não transporta credenciais, chaves nem dados pessoais, conforme a
  regra do contrato de dados.
