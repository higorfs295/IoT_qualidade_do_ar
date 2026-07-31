# Backend — Ingestão + API (MVP funcional)

Serviço MVP que faz o papel local do `sink`: **assina o broker, valida o
contrato v1.1, mantém uma série curta em memória e serve o dashboard**.

## Stack atual

- **Node.js HTTP** — servidor enxuto sem framework.
- **Armazenamento em memória** — estado e ring buffer; reinício apaga dados.
- **MQTT** — `mqtt.js` assinando apenas `qualidade-ar/+/+/telemetria`.
- **WebSocket** — empurra telemetria em tempo real ao front.

Fastify/TypeScript/PostgreSQL são a evolução B1, não o estado atual. Veja
[`../../docs/ROADMAP_SOFTWARE.md`](../../docs/ROADMAP_SOFTWARE.md).

## Responsabilidades

1. **Assinar** o broker e receber a telemetria.
2. **Validar** cada mensagem contra o contrato v1.1 (mesma regra do
   `poc/qar_poc/contrato.py`); rejeitadas incrementam métricas. Quarentena
   persistente é parte do roadmap.
3. **Deduplicar** por `message_id` e **detectar lacunas** por `sequence`.
4. **Reter em memória** uma série limitada e o **estado atual** por dispositivo.
5. **Servir** os dashboards.

## API atual

| Método | Rota | Uso |
|---|---|---|
| GET | `/api/dispositivos` | lista dispositivos e último status |
| GET | `/api/dispositivos/:id/atual` | leitura mais recente |
| GET | `/api/dispositivos/:id/serie?campo=&n=` | ring buffer de uma grandeza |
| GET | `/api/metricas` | contadores JSON |
| POST | `/api/ingest` | ingestão de desenvolvimento |
| WS | `/ws` | telemetria em tempo real |

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

## Estrutura atual

```text
backend/src/server.js
backend/src/contrato.js
backend/test/contrato.test.js
```

## Princípios (redes / distribuídos)

- **Idempotência** por `message_id`; **detecção de perda** por `sequence`.
- **Retenção atual:** somente memória. A política proposta está em
  `docs/modelagem_dados.json`.
- **Desacoplamento**: o broker separa dispositivos de consumidores; a ingestão
  escala independente.
