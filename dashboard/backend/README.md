# Backend — ingestão, persistência e API

Serviço local que faz o papel do `sink`: **assina o broker, valida o
contrato v1.1, mantém uma série limitada, persiste o estado e serve o dashboard**.

## Stack atual

- **Node.js HTTP** — servidor enxuto sem framework.
- **Persistência atômica em JSON** — estado, séries e deduplicação sobrevivem a
  reinícios sem dependência nativa; o Compose monta `/data` em volume nomeado.
- **MQTT** — `mqtt.js` assinando apenas `qualidade-ar/+/+/telemetria`.
- **WebSocket** — empurra telemetria em tempo real ao front.

PostgreSQL/TimescaleDB continua sendo a evolução para histórico longo e múltiplas
instâncias. A instalação padrão já é persistente em nó único. Veja
[`../../docs/ROADMAP_SOFTWARE.md`](../../docs/ROADMAP_SOFTWARE.md).

## Responsabilidades

1. **Assinar** o broker e receber a telemetria.
2. **Validar** cada mensagem contra o contrato v1.1 (mesma regra do
   `poc/qar_poc/contrato.py`); rejeitadas incrementam métricas.
3. **Deduplicar** por `message_id` e **detectar lacunas** por `sequence`.
4. **Reter e persistir** uma série limitada e o estado atual por dispositivo.
5. **Servir** os dashboards.

## API atual

| Método | Rota | Uso |
|---|---|---|
| GET | `/api/dispositivos` | lista dispositivos e último status |
| GET | `/api/info` | versão, schemas, campos de série e capacidades |
| GET | `/api/dispositivos/:id/atual` | leitura mais recente |
| GET | `/api/dispositivos/:id/serie?campo=&n=` | ring buffer de uma grandeza |
| GET | `/api/metricas` | contadores JSON |
| GET | `/api/health` | liveness, MQTT, persistência e readiness |
| GET | `/metrics` | métricas no formato Prometheus |
| POST | `/api/ingest` | ingestão de desenvolvimento |
| WS | `/ws` | telemetria em tempo real |

Contrato de API: [`../../docs/openapi.yaml`](../../docs/openapi.yaml).

Em `NODE_ENV=production`, a ingestão HTTP fica desabilitada por padrão. Use
`ENABLE_HTTP_INGEST=true` e `HTTP_INGEST_TOKEN` somente quando necessário.

| Variável | Padrão | Limite/uso |
|---|---:|---|
| `PORT` | 3001 | porta HTTP válida |
| `SERIE_MAX` | 500 | pontos por dispositivo |
| `DEVICES_MAX` | 10.000 | dispositivos mantidos em memória |
| `IDS_MAX` | 200.000 | janela de deduplicação |
| `BODY_MAX` | 65.536 | bytes por ingestão HTTP |
| `ONLINE_TIMEOUT_MS` | 120.000 | janela de presença |
| `DATA_DIR` | vazio | diretório persistente; `/data` no container |
| `STATE_FILE` | `$DATA_DIR/state.json` | caminho opcional explícito |
| `PERSIST_INTERVAL_MS` | 5.000 | intervalo mínimo entre snapshots |
| `MQTT_ENABLED` | true | permite execução isolada sem broker |
| `CORS_ORIGINS` | vazio | lista explícita, separada por vírgulas |
| `HTTP_INGEST_TOKEN` | vazio | Bearer opcional para ingestão de desenvolvimento |

`ready` só é verdadeiro quando MQTT está conectado **e a assinatura do tópico
foi confirmada**; consulte `mqtt_subscribed`. Requisições a métodos não
permitidos retornam `405`, campos históricos desconhecidos retornam `400` e URLs
malformadas não derrubam o processo.

## Container

O contexto de build é `dashboard/`, pois a imagem inclui backend e arquivos
estáticos da PWA:

```bash
docker build -f dashboard/backend/Dockerfile -t qar-backend dashboard
```

Na raiz do projeto, `docker compose up -d --build` é o caminho recomendado.
O encerramento por `SIGTERM` aguarda a gravação final antes de fechar HTTP/MQTT.

## Estrutura atual

```text
backend/src/server.js
backend/src/contrato.js
backend/src/persistence.js
backend/test/contrato.test.js
backend/test/persistence.test.js
```

## Princípios (redes / distribuídos)

- **Idempotência** por `message_id`; **detecção de perda** por `sequence`.
- **Retenção local:** ring buffer persistido; histórico longo segue a política
  de `docs/modelagem_dados.json`.
- **Desacoplamento**: o broker separa dispositivos de consumidores; a ingestão
  escala independente.
