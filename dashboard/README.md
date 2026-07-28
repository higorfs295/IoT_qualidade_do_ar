# Dashboard — Ingestão + Web (Fase 2)

O ecossistema de visualização da estação: um **serviço de ingestão** que assina
o broker MQTT, valida o contrato v1.1, persiste série temporal e expõe uma API
REST + WebSocket; e um **dashboard web** legível por um **usuário leigo**.

> Status nesta branch: **scaffold documentado** (plano + estrutura + reuso). A
> implementação é a Fase 2 do roadmap em [`../BASE_FINAL.md`](../BASE_FINAL.md).

```text
dashboard/
├── backend/    ingestão + API (Fastify + série temporal + WebSocket)
└── web/        painel Next.js (cartões por cor, gráficos, linguagem simples)
```

## Fluxo

```text
ESP32 ─MQTT─▶ Broker ─▶ [backend: assina, valida, persiste] ─REST/WebSocket─▶ [web] e [mobile]
```

- **backend** e **web** seguem a arquitetura do **Painel_UFG** (o seu projeto de
  referência): Fastify + Prisma + PostgreSQL no backend; Next.js + Tailwind +
  TanStack Query no front. Reaproveitam plugins de métricas/segurança, Docker,
  testes e a organização de `docs/`.
- Para gráficos imediatos e sem build, o front pode começar com o `charts.js`
  (SVG puro, sem dependências) do **IoT-IDEA**, evoluindo para componentes React.
- A **legibilidade para leigos** é requisito de projeto: ver `web/README.md`.

Detalhes de cada parte nos READMEs de [`backend/`](backend/) e [`web/`](web/).
