# Backend — Ingestão + API (Fase 2, scaffold)

Serviço que faz, em produção, o que o `sink` da PoC faz em teste: **assina o
broker, valida o contrato v1.1, persiste série temporal e serve os dashboards**.

## Stack (espelha o backend do Painel_UFG)

- **Fastify** (Node/TypeScript) — API HTTP performática, com plugins.
- **Prisma** — ORM e migrações.
- **Banco de série temporal** — começar com **SQLite** (protótipo de 1
  dispositivo) e evoluir para **PostgreSQL + TimescaleDB** (hypertables) quando
  crescer.
- **MQTT** — `mqtt.js` assinando `qualidade-ar/#`.
- **WebSocket/SSE** — empurra telemetria em tempo real ao front.
- Plugins de **métricas** (`/metrics` estilo Prometheus — herdado do simulador
  do IoT-IDEA), **segurança** e **observabilidade** (padrão do Painel_UFG).

## Responsabilidades

1. **Assinar** o broker e receber a telemetria.
2. **Validar** cada mensagem contra o contrato v1.1 (mesma regra do
   `poc/qar_poc/contrato.py`); rejeitadas vão para uma tabela de quarentena.
3. **Deduplicar** por `message_id` e **detectar lacunas** por `sequence`.
4. **Persistir** a série temporal e manter o **estado atual** por dispositivo.
5. **Servir** os dashboards.

## API (rascunho)

| Método | Rota | Uso |
|---|---|---|
| GET | `/dispositivos` | lista dispositivos e último status |
| GET | `/dispositivos/:id/atual` | leitura mais recente |
| GET | `/dispositivos/:id/serie?de=&ate=&campo=` | série histórica (gráficos) |
| GET | `/alertas` | eventos de limiar (UNSAFE) |
| GET | `/metricas` | métricas operacionais (Prometheus) |
| WS | `/stream` | telemetria em tempo real |

## Estrutura sugerida

```text
backend/
├── src/
│   ├── server.ts           # bootstrap Fastify + plugins
│   ├── mqtt/ingestor.ts     # assina o broker, valida, persiste
│   ├── contrato.ts          # espelho do contrato v1.1 (validação)
│   ├── db/                   # Prisma schema + repositórios
│   ├── rotas/               # dispositivos, série, alertas, métricas
│   └── ws/stream.ts          # WebSocket de tempo real
├── prisma/schema.prisma
├── Dockerfile
└── package.json
```

## Princípios (redes / distribuídos)

- **Idempotência** por `message_id`; **detecção de perda** por `sequence`.
- **Retenção**: bruto por N dias, agregados por hora com TTL (alinhado à política
  do Wilson em `docs/modelagem_dados.json`).
- **Desacoplamento**: o broker separa dispositivos de consumidores; a ingestão
  escala independente.
