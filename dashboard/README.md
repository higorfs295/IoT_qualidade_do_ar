# Dashboard Air Sense

Aplicação local completa de ingestão e visualização: o backend assina MQTT,
valida o contrato v1.1, mantém estado/série curta persistentes e atende a Web/PWA
e o app Flutter por REST e WebSocket.

```text
ESP32/demo -> MQTT QoS 1 -> backend -> REST/WS -> Web/PWA
                                      └───────> Flutter
```

## Executar

Na raiz:

```bash
docker compose up -d --build
```

Abra `http://localhost:3001`. A demonstração identificada cria três dispositivos
por padrão. Para desenvolvimento sem broker:

```bash
cd dashboard/backend
npm ci
MQTT_ENABLED=false ENABLE_HTTP_INGEST=true DATA_DIR=./data npm start
```

## Entregue

- validação, deduplicação, lacunas, limites e snapshot atômico;
- health/readiness, métricas JSON/Prometheus e graceful shutdown;
- API REST documentada e WebSocket com heartbeat/limite de payload;
- cabeçalhos de segurança e CORS somente para origens explícitas;
- PWA responsiva com Agora, Histórico, Alertas e Dispositivo;
- atualização live, reconexão, shell offline e modo demo sempre sinalizado.

O snapshot JSON é adequado a nó único e histórico curto. Para retenção longa,
HA e consultas multiusuário, siga o marco B1 em
[`../docs/ROADMAP_SOFTWARE.md`](../docs/ROADMAP_SOFTWARE.md).

Detalhes: [`backend/README.md`](backend/README.md) e
[`web/README.md`](web/README.md).
