# Planejamento de serviços AWS

Este é um caminho de evolução, não infraestrutura implantada. Antes de criar
recursos: definir conta/sandbox, orçamento mensal, tags, região, responsáveis,
política de retenção e procedimento de destruição segura.

## Fluxo proposto

```text
dispositivo mTLS -> AWS IoT Core -> IoT Rule -> SQS Standard -> consumidor
                                              |                 |-- estado atual
                                              |                 |-- histórico
                                              +-> DLQ            +-- eventos

histórico -> S3 particionado -> Glue Catalog/Athena
estado/API -> DynamoDB ou PostgreSQL, decidido por padrões de consulta
observabilidade -> CloudWatch + alarmes + painel de custo
```

Arquivos executáveis de referência desta revisão:

- [`sandbox.template.json`](sandbox.template.json): CloudFormation para
  IoT Rule, SQS/DLQ, S3 bruto, DynamoDB de estado e alarme de DLQ;
- [`iot-policy-device.example.json`](iot-policy-device.example.json): política
  mínima por Thing/atributo `siteId`;
- [`iot-rule-sqs.example.json`](iot-rule-sqs.example.json): payload para criar a
  regra isoladamente;
- [`lambda_ingest/handler.py`](lambda_ingest/handler.py): validação em lote e
  atualização idempotente do estado atual.

Esses arquivos são templates: não contêm conta, região, endpoint, certificado
ou chave e não foram aplicados a uma conta AWS nesta revisão.

## Dois modos de conexão

### Direto do ESP32 para o IoT Core

Use o ambiente `esp32-aws`. Configure endpoint ATS, porta 8883, Amazon Root CA,
certificado e chave exclusivos no `secrets.h`. O `DEVICE_ID` deve coincidir com
Thing Name/MQTT client ID; o Thing precisa do atributo `siteId` igual a
`SITE_ID`. Vantagem: menos infraestrutura local. Custo: TLS/certificados ocupam
mais flash e heap, por isso o gate de memória é obrigatório.

### Via Mosquitto de borda

O ESP32 publica localmente e um gateway Linux mantém a conexão mTLS com a AWS.
Isso centraliza certificados e fila offline, mas o gateway vira componente
crítico e precisa de disco, backup de configuração, métricas e atualização. Não
usar o mesmo certificado para vários gateways/dispositivos.

## Decisões por serviço

### IoT Core

- Certificado individual e política limitada ao `clientId`/tópico do dispositivo.
- Tópicos mantêm o contrato v1.1; regra valida os campos mínimos e encaminha.
- Definir comportamento de certificados revogados e rotação.
- Medir limite de conexão/publicação e custo na região escolhida.
- Não usar Device Shadow como histórico de telemetria. Shadow serve para estado
  desejado/reportado e configuração; o fluxo S3/SQS preserva eventos.
- O payload do ESP32 é limitado a 896 bytes por decisão de memória, embora o
  serviço aceite mensagens maiores. Essa margem deve ser medida com o PEM real.

### SQS e DLQ

- Standard é compatível com QoS 1: consumidor precisa ser idempotente por
  `message_id`; ordem global não é presumida.
- Visibility timeout maior que o pior tempo de processamento.
- `maxReceiveCount` e retenção da DLQ documentados.
- Runbook para inspecionar/corrigir/reprocessar DLQ sem duplicação.

### Consumidor

- Lambda para carga intermitente ou serviço em contêiner para fluxo contínuo;
  comparar custo/latência antes de escolher.
- Validação do JSON Schema e tópico, deduplicação condicional, lote com falha
  parcial e métricas por motivo de rejeição.
- Nenhum payload inválido deve desaparecer: registrar quarentena sem segredos.
- Ativar resposta parcial de lote SQS; um registro inválido não deve repetir o
  lote inteiro.

### Persistência

- Estado atual: acesso por site/dispositivo e atualização condicional por
  `boot_id/sequence`.
- Histórico operacional: PostgreSQL/Timescale se consultas e joins dominarem;
  DynamoDB se os padrões chave/tempo forem simples e bem definidos.
- Data lake: S3 em formato colunar, particionado por data/site, compactação para
  evitar arquivos pequenos e lifecycle para classes frias/expiração.
- Criptografia com chaves gerenciadas conforme necessidade; backups testados.

### API/dashboard

- API Gateway + serviço autenticado, ou ALB + contêiner, conforme arquitetura.
- OIDC, RBAC por site, rate limit, WAF se exposição pública e logs de auditoria.
- WebSocket gerenciado só após medir necessidade/custo; polling/SSE podem bastar.

## Infraestrutura como código

Escolher CDK, Terraform ou CloudFormation e manter ambientes separados
`dev/stage/prod`. Módulos mínimos:

1. orçamento/tags/logs;
2. IoT policies/cert enrollment;
3. regra + SQS/DLQ;
4. consumidor + persistência;
5. API/autenticação;
6. observabilidade/backups.

CI deve executar lint, synth/plan e análise de segurança. Apply de produção
exige revisão humana e plano de rollback. Estado remoto e segredos não ficam no
repositório.

### Sequência segura do sandbox

1. Selecionar região e configurar orçamento/alerta antes dos recursos.
2. Validar o template e revisar o change set; criar a stack `dev`.
3. Criar um Thing, atributo `siteId`, certificado exclusivo e anexar a política.
4. Obter o endpoint ATS da conta e configurar `secrets.h` local.
5. Compilar `pio run -e esp32-aws`; confirmar flash de 4 MB e margem OTA.
6. Publicar uma fixture pelo cliente de teste AWS antes de ligar o ESP32.
7. Verificar S3, SQS, consumidor, DynamoDB e CloudWatch de ponta a ponta.
8. Revogar o certificado de teste e destruir a stack quando o experimento acabar
   (o bucket tem `Retain`, portanto deve ser esvaziado/removido conscientemente).

Não executar `cloudformation deploy` automaticamente em conta real: criação de
recursos gera custo e requer escolha explícita de conta, região e responsável.

## Gates

- **N0:** calculadora de custo preenchida com `docs/estimativa_carga.xlsx` e
  alarmes de orçamento criados.
- **N1:** um dispositivo em sandbox, mTLS e política mínima.
- **N2:** reentrega/duplicação/DLQ testadas com fixtures.
- **N3:** carga de 1% e depois 10% do cenário, sem erro silencioso.
- **N4:** backup/restore, rotação/revogação e indisponibilidade simulados.
- **N5:** revisão de segurança/custo antes do piloto.

## O que não assumir

- Bridge Mosquitto para AWS IoT Core não funciona só trocando hostname; precisa
  de certificados, SNI, CA, client ID e política coerentes.
- SQS Standard não entrega exatamente uma vez nem ordem global.
- S3 barato não elimina custo de requisição, catálogo, consulta e muitos arquivos.
- Taxa de payload não inclui overhead, replicação, índices ou tráfego de saída.
