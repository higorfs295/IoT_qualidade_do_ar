# Roadmap de backend, web, mobile e nuvem

## Backend — do MVP para serviço persistente

### B0 — base atual

MVP Node com MQTT.js, REST, WebSocket, deduplicação limitada e série em memória.
É adequado para demonstração local; reiniciar o processo apaga o histórico.

### B1 — modularização e persistência

- Separar bootstrap, configuração, domínio, ingestor MQTT, repositórios e rotas.
- Adotar Fastify + TypeScript e validação gerada do JSON Schema.
- PostgreSQL com tabelas `device`, `telemetry`, `alert_event`, `ingest_reject`.
- Chaves: `message_id` único; índice `(device_id, sent_at)`; estado atual por
  `(site_id, device_id)`; política explícita para `boot_id`/`sequence`.
- Migrações, seed e teste de restauração de backup.

Gate: reiniciar o backend sem perder histórico nem duplicar mensagens QoS 1.

### B2 — API e observabilidade

- Paginação, filtros `from/to`, agregações temporais e limites de consulta.
- OpenAPI, erros estáveis e testes de contrato.
- Métricas Prometheus: ingestão, rejeição, duplicação, lacuna, atraso, conexões.
- Logs JSON com correlação por `message_id` sem registrar segredos.
- Health/readiness separados; graceful shutdown do MQTT/HTTP/banco.

Gate: teste de carga cumpre SLO documentado e não cresce memória sem limite.

### B3 — segurança

- TLS/mTLS no broker, ACL por dispositivo e rotação de credenciais.
- OIDC para usuários; RBAC por site; trilha de auditoria.
- Ingestão HTTP desabilitada em produção ou protegida por token rotacionável.
- Rate limit, limites de payload, dependências auditadas e threat model.

Gate: checklist OWASP/API e teste de restauração/rotação aprovados.

## Web

### W1 — estabilizar o MVP

- Testes de funções de classificação e reconexão.
- Estado “desatualizado” por idade de recepção, não só `sent_at` do dispositivo.
- Explicar que faixas de PM com média temporal não equivalem a uma leitura
  instantânea; manter aviso de protótipo sempre visível.
- Não depender apenas de cores; preservar texto, ícones e contraste.

### W2 — aplicação de produto

- Next.js/TypeScript ou SPA equivalente consumindo OpenAPI.
- Páginas Agora, Histórico, Eventos e Dispositivo.
- Gráficos com lacunas visíveis, fuso configurável e agregação coerente.
- PWA, cache somente de leitura e comportamento offline explícito.

Gate: Lighthouse/acessibilidade, testes e2e e teste com usuário leigo.

## Alertas

- Centralizar regras no backend; web/mobile apenas exibem o resultado.
- Aplicar duração mínima, histerese, cooldown e estado de reconhecimento.
- Separar “dado indisponível”, “faixa operacional excedida” e “alarme externo”.
- Nunca emitir instrução de emergência baseada apenas no sensor experimental.
- Registrar versão da regra, valores, janela, origem e quem reconheceu.

## Mobile Flutter

1. Criar `mobile/pubspec.yaml` e estrutura feature-first.
2. Gerar modelos do OpenAPI/JSON Schema; não copiar manualmente o contrato.
3. Riverpod, Dio e `web_socket_channel`, com reconexão/backoff.
4. Telas Agora/Histórico/Eventos/Dispositivos e acessibilidade.
5. Push pelo backend; tokens protegidos e revogáveis.
6. Testes unitários, widget e integração em Android/iOS.

Gate: paridade de regra e estado com o web usando os mesmos fixtures.

## Nuvem

- Começar com um único ambiente pequeno e infraestrutura como código.
- AWS IoT Core -> regra -> SQS/DLQ -> consumidor idempotente -> banco/data lake.
- A base executável está em [`../infra/aws/`](../infra/aws/): template
  CloudFormation do sandbox, política por Thing, regra de roteamento e consumidor
  Lambda de referência.
- Para conexão direta, compilar `esp32-aws` com mTLS e limitar buffers/telemetria;
  para uma frota local, avaliar Mosquitto de borda como concentrador antes de
  impor TLS e certificados a cada nó.
- Orçamento e alarmes de custo antes do benchmark.
- Retenção por classe, criptografia, IAM mínimo e logs de auditoria.
- Testar reprocessamento da DLQ e recuperação regional antes do piloto.

Não ligar uma bridge de produção apenas copiando o exemplo Mosquitto: endpoint,
SNI, cadeia de CA, certificados, política IoT e semântica de sessão precisam ser
validados especificamente para o ambiente.
