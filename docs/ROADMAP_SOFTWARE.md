# Roadmap de backend, web, mobile e nuvem

Este roadmap parte da versão local já executável. Itens concluídos não devem ser
reabertos sem evidência de regressão; os próximos gates tratam de escala,
segurança multiusuário e operação real.

## Backend

### B0 — base local concluída

- [x] MQTT.js, REST e WebSocket com contrato v1.1 compartilhado.
- [x] Deduplicação, lacunas, reinícios e séries com limites explícitos.
- [x] Snapshot JSON versionado e atômico, restaurado após reinício.
- [x] Health/readiness, métricas JSON/Prometheus e graceful shutdown.
- [x] OpenAPI e testes de contrato, persistência e processo HTTP real.
- [x] Imagem não-root, volume de dados e healthcheck no Compose.

Gate cumprido: a instalação local reinicia sem perder o estado limitado e sem
duplicar mensagens conhecidas na janela persistida.

### B1 — histórico longo e consultas de produto

- [ ] Separar domínio, transporte e repositórios em módulos TypeScript.
- [ ] PostgreSQL/TimescaleDB com `device`, `telemetry`, `alert_event` e
  `ingest_reject`; `message_id` único e índices por dispositivo/tempo.
- [ ] Migrações, retenção, agregações, paginação e filtros `from/to`.
- [ ] Backup/restauração automatizado e migração importando o snapshot local.
- [ ] Teste de carga com SLO de latência, vazão e uso de memória documentado.

Gate: retenção e recuperação aprovadas com volume representativo e sem memória
proporcional ao histórico.

### B2 — segurança e operação compartilhada

- [ ] TLS/mTLS no broker, ACL por dispositivo e rotação de certificados.
- [ ] OIDC para usuários, RBAC por site e trilha de auditoria.
- [ ] Rate limit, política de CORS, logs JSON correlacionados e alertas de SLO.
- [ ] Segredos externos, SBOM, varredura de dependências e threat model.
- [ ] Alta disponibilidade apenas após teste explícito de failover.

Gate: checklist OWASP/API, rotação, restauração e isolamento entre sites
aprovados. A ingestão HTTP continua desabilitada no Compose de produção local.

## Web/PWA

### W0 — painel instalável concluído

- [x] Estado atual, histórico curto, métricas, WebSocket e reconexão.
- [x] Layout responsivo, texto além de cor e aviso de uso experimental.
- [x] Manifest, ícone, service worker e fallback do shell offline.
- [x] Conteúdo estático com CSP e sem injeção por identificadores.

### W1 — experiência de produto

- [ ] Testes e2e em Chromium/Firefox/WebKit e auditoria WCAG/Lighthouse.
- [ ] Páginas dedicadas de histórico, eventos e inventário de dispositivos.
- [ ] Fuso configurável, agregações temporais e lacunas visíveis nos gráficos.
- [ ] Autenticação integrada ao backend B2.
- [ ] Push opcional somente depois de regras de alerta validadas.

Gate: tarefas críticas concluídas por usuário leigo e comportamento offline
documentado sem sugerir que dados antigos são atuais.

## Alertas

1. Definir uso pretendido, responsáveis e linguagem que não sugira certificação.
2. Centralizar regras versionadas no backend, nunca duplicar limiares na UI.
3. Aplicar janela mínima, histerese, cooldown e reconhecimento.
4. Separar dado indisponível, faixa operacional e alarme externo certificado.
5. Persistir valores, regra, janela, origem, envio e reconhecimento.
6. Testar falsos positivos/negativos antes de habilitar notificações.

## Mobile

O cliente Flutter em [`../mobile/`](../mobile/) está implementado com poucas
dependências, estado testável, REST, WebSocket com backoff, gráficos leves,
histórico, alertas da sessão e diagnóstico do ESP-WROOM-32.

1. [x] Criar projeto Android/iOS/Web e identidade alinhada à web.
2. [x] Integrar contrato v1.1, endpoints reais e modo demonstração explícito.
3. [x] Limitar séries/alertas em memória e adicionar testes automatizados.
4. [ ] Validar em aparelhos físicos, acessibilidade e sessão contínua de 24 h.
5. [ ] Centralizar alertas persistentes no backend com autenticação e auditoria.
6. [ ] Adicionar Cognito/OIDC e push FCM/APNs no marco AWS.

Gate atual: piloto em aparelhos físicos. Roadmap detalhado em
[`../mobile/docs/ROADMAP_MOBILE.md`](../mobile/docs/ROADMAP_MOBILE.md).

## AWS

### C0 — base reproduzível concluída localmente

- [x] Perfil `esp32-aws` com mTLS e buffers compatíveis com ESP-WROOM-32.
- [x] CloudFormation para IoT Rule, SQS/DLQ, S3, Lambda e DynamoDB.
- [x] Política de Thing mínima e consumidor idempotente com resposta parcial.
- [x] Roteiros de implantação, custo, teardown e validação.

### C1 — sandbox autorizado

- [ ] Criar orçamento/alarmes antes dos recursos.
- [ ] Aplicar o template em conta sandbox e registrar outputs.
- [ ] Emitir um certificado por unidade; nunca versionar chaves privadas.
- [ ] Validar QoS 1, SQS/DLQ, objeto S3, estado DynamoDB e observabilidade.
- [ ] Exercitar revogação, reprocessamento e remoção completa dos recursos.

### C2 — frota

- [ ] Provisioning automatizado, inventário e rotação por dispositivo.
- [ ] OTA assinada, staged rollout, rollback e métricas de campanha.
- [ ] Retenção por classe, criptografia, auditoria e recuperação regional.
- [ ] Comparar IoT Core direto com gateway Mosquitto de borda por custo e RAM.

Não usar a configuração Mosquitto local como bridge de produção sem validar
endpoint, SNI, cadeia CA, certificados, política IoT e sessão no ambiente real.
