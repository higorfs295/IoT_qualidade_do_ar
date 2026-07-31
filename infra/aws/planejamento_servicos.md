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

## Decisões por serviço

### IoT Core

- Certificado individual e política limitada ao `clientId`/tópico do dispositivo.
- Tópicos mantêm o contrato v1.1; regra valida os campos mínimos e encaminha.
- Definir comportamento de certificados revogados e rotação.
- Medir limite de conexão/publicação e custo na região escolhida.

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
