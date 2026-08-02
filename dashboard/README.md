# Dashboard — Ingestão + Web (Fase 2)

O ecossistema de visualização da estação: um **serviço de ingestão** que assina
o broker MQTT, valida o contrato v1.1, guarda série temporal e expõe uma API
REST + WebSocket; e um **dashboard web** legível por um **usuário leigo**.

> Status: **aplicação local funcional**. A instalação padrão inclui MQTT,
> persistência, healthcheck, métricas, dados de demonstração e painel PWA.

```text
dashboard/
├── backend/    ingestão + API (Node: MQTT + REST + WebSocket + persistência)
│   └── src/{server.js, contrato.js}
└── web/        painel web (verdito por cor, cartões, sparklines, tempo real)
    └── public/{index.html, style.css, app.js, charts.js, config.js}
```

## Como rodar

```bash
cd ..
docker compose up -d --build
# abra http://localhost:3001
```

## Fluxo

```text
ESP32 ─MQTT─▶ Broker ─▶ [backend: assina, valida, persiste] ─REST/WebSocket─▶ [web] e [mobile]
```

- **backend** e **web** são implementações deliberadamente pequenas em Node e
  JavaScript puro. O banco local é um snapshot atômico; PostgreSQL/TimescaleDB é
  indicado quando histórico longo, consultas complexas ou alta disponibilidade
  forem necessários.
- Para gráficos imediatos e sem build, o front pode começar com o `charts.js`
  (SVG puro, sem dependências) do **IoT-IDEA**, evoluindo para componentes React.
- A **legibilidade para leigos** é requisito de projeto: ver `web/README.md`.

Detalhes de cada parte nos READMEs de [`backend/`](backend/) e [`web/`](web/).
