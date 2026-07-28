# Dashboard — Ingestão + Web (Fase 2)

O ecossistema de visualização da estação: um **serviço de ingestão** que assina
o broker MQTT, valida o contrato v1.1, guarda série temporal e expõe uma API
REST + WebSocket; e um **dashboard web** legível por um **usuário leigo**.

> Status nesta branch: **MVP funcional** (Fase 2). O backend Node e o dashboard
> web já rodam e foram validados de ponta a ponta (broker → gerador → backend →
> WebSocket → painel), com verdito por cor, cartões por grandeza e detecção de
> perdas. A evolução para o padrão de produção (Fastify + Prisma + Next.js, como
> o Painel_UFG) está descrita nos READMEs de cada parte.

```text
dashboard/
├── backend/    ingestão + API (Node: MQTT + REST + WebSocket + série em memória)
│   └── src/{server.js, contrato.js}
└── web/        painel web (verdito por cor, cartões, sparklines, tempo real)
    └── public/{index.html, style.css, app.js, charts.js, config.js}
```

## Como rodar o MVP

```bash
# 1) Broker + (opcional) dados: suba o Mosquitto e gere telemetria v1.1
cd ../infra/server_config && docker compose up -d mosquitto
python ../../poc/ingestao_teste.py --host localhost --sensores 2 --gateways 2 --intervalo 3

# 2) Backend de ingestão (assina o broker, serve o painel)
cd ../../dashboard/backend && npm install && npm start
#    -> abra http://localhost:3001

# Sem broker/backend, o painel abre em "modo demonstração" (dados simulados
# no navegador) — basta abrir dashboard/web/public/index.html.
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
