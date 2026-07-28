# Planejamento dos servicos AWS

## 1. Premissas

Este planejamento evolui a prova de conceito da Atividade 2. Nela, um ESP32 publicava temperatura, umidade e o estado de gas em topicos MQTT a cada cinco segundos para facilitar a demonstracao. Para a operacao planejada, o dispositivo passa a enviar uma leitura consolidada de qualidade do ar a cada **60 segundos**, com MQTT sobre TLS e QoS 1.

O payload e o contrato de dados estao em [`docs/modelagem_dados.json`](../../docs/modelagem_dados.json). A consolidacao de todas as medidas em uma unica mensagem evita que uma mesma leitura gere varios eventos independentes e preserva a correlacao entre CO2, TVOC, particulados, temperatura e umidade.

## 2. Fluxo proposto

```text
ESP32 + SCD41 / ENS160 / PMS5003
          | MQTT mTLS, QoS 1
          v
     AWS IoT Core
          | regra MQTT: valida e encaminha
          v
       Amazon SQS --------------> DLQ
          |
          | lote de ate 100 mensagens
          v
     AWS Lambda (normaliza, valida e deduplica)
          |                         |
          |                         +--> DynamoDB: estado atual e agregados horarios
          v
      Amazon S3: bruto/Parquet -> consultas analiticas futuras

CloudWatch observa IoT Core, SQS, Lambda e DynamoDB.
IAM aplica permissoes minimas a dispositivos e servicos.
```

O dispositivo publica em `qualidade-ar/{site_id}/{device_id}/telemetria`. Uma regra do IoT Core encaminha apenas esse topico para a fila. A Lambda recebe lotes, verifica o contrato, grava mensagens invalidas na area de quarentena do S3 e executa gravacoes idempotentes usando `message_id`; portanto, uma nova entrega por MQTT QoS 1 ou por SQS nao duplica a leitura logica.

## 3. Servicos e justificativas

| Servico | Papel na arquitetura | Justificativa |
|---|---|---|
| AWS IoT Core | Broker MQTT gerenciado, identidade de dispositivos e regras de roteamento | Elimina a administracao de broker proprio, suporta conexoes MQTT seguras em escala e integra a telemetria a servicos AWS. Cada ESP32 usa certificado X.509 proprio e TLS mutuo. |
| Amazon SQS Standard + DLQ | Buffer duravel entre entrada e processamento | Desacopla a taxa de chegada da capacidade da Lambda, absorve picos e permite reprocessamento. A aplicacao e idempotente porque a fila Standard pode entregar mais de uma vez. |
| AWS Lambda | Validacao, normalizacao, deduplicacao, calculo de agregados e roteamento | Processamento sem servidor acionado por lotes da fila. O lote reduz invocacoes e o retry controlado evita perda silenciosa. |
| Amazon DynamoDB | Estado atual por sensor e agregados horarios para o dashboard/API | Baixa latencia e escalabilidade gerenciada. A chave por dispositivo distribui as escritas; TTL remove agregados antigos automaticamente. Nao e usado como arquivo completo de telemetria bruta. |
| Amazon S3 | Data lake de telemetria bruta, quarentena e historico Parquet | Armazenamento de grande volume e baixo custo. Prefixos por data/hora e site facilitam consulta posterior com Athena; lifecycle reduz custo sem apagar dados necessarios prematuramente. |
| Amazon API Gateway (opcional para o dashboard) | API HTTPS para leitura do estado e agregados | Evita acesso direto do cliente ao DynamoDB e permite autenticacao, limitacao de taxa e versionamento da API. |
| Amazon CloudWatch | Logs, metricas, dashboards e alarmes | Centraliza visibilidade: desconexoes, mensagens rejeitadas, idade da fila, erros/throttling da Lambda e consumo do DynamoDB. Alarmes notificam o time antes que a DLQ acumule mensagens. |
| AWS IAM | Identidades e politicas de menor privilegio | Separa permissoes de dispositivos, regra do IoT, Lambda, SQS, DynamoDB, S3 e observabilidade. Nenhum dispositivo recebe credencial AWS generica. |

## 4. Capacidade e volumetria

As contas detalhadas estao em [`docs/estimativa_carga.md`](../../docs/estimativa_carga.md) e devem ser refletidas em `docs/estimativa_carga.xlsx`. Elas usam uma mensagem por sensor a cada minuto, payload JSON de 470 bytes e 70 bytes de cabecalhos/protocolo estimados: 540 bytes trafegados por leitura. O exemplo JSON atual ocupa 419 bytes; os 470 bytes incluem margem para evolucao do contrato.

No maior cenario, 100.000 sensores produzem 1.666,67 mensagens por segundo em media, 144.000.000 mensagens por dia e aproximadamente 77,76 GB/dia de trafego de entrada. A capacidade inicial deve considerar pico de 2x: 3.333,33 mensagens por segundo. Com lote Lambda de 100 mensagens, isso equivale a aproximadamente 34 invocacoes por segundo no pico, antes de eventuais retries.

O volume bruto nao deve ser armazenado individualmente no S3 por objeto. A Lambda deve enviar registros a um buffer/gravador em lote - por exemplo, Amazon Data Firehose em uma evolucao posterior - ou acumular arquivos por janela curta, para gerar objetos maiores e Parquet comprimido. Firehose e complementar; os componentes obrigatorios do fluxo continuam IoT Core, SQS, Lambda, DynamoDB e S3.

## 5. Armazenamento e retencao

- **DynamoDB:** item `LATEST` por dispositivo, sobrescrito a cada leitura; agregados horarios com TTL de 90 dias. Esse desenho evita reter 4,32 bilhoes de leituras brutas por mes no banco transacional no maior cenario.
- **S3:** JSON bruto por 30 dias; historico convertido para Parquet e particionado por `year/month/day/hour/site_id`. Depois de um ano, mover para Glacier Flexible Retrieval; expirar em cinco anos.
- **Quarentena e DLQ:** mensagens com contrato invalido ficam 30 dias no S3; a DLQ retém mensagens por 14 dias para investigacao e reprocessamento.
- **CloudWatch Logs:** 30 dias em desenvolvimento e 90 dias em producao.

As regras detalhadas estao no arquivo de modelagem para manter o contrato e a politica de dados juntos.

## 6. Confiabilidade, seguranca e monitoramento

### Entrega e recuperacao

- Configurar MQTT QoS 1 e `clean session`/sessao persistente conforme a biblioteca do ESP32 permitir.
- Usar `message_id` e escrita condicional para deduplicar mensagens em reentregas.
- Configurar visibility timeout da SQS maior que o timeout maximo da Lambda e `maxReceiveCount` antes de enviar a mensagem para a DLQ.
- Criar alarme para `ApproximateAgeOfOldestMessage`, numero de mensagens na DLQ, erros da Lambda e mensagens rejeitadas pela regra IoT.

### Seguranca

- Um certificado X.509 exclusivo por dispositivo, politicas IoT limitadas ao topico do proprio `device_id` e revogacao imediata de certificados comprometidos.
- Remover o uso de `setInsecure()` existente na POC e validar a cadeia de certificados no firmware.
- Criptografar S3, SQS e DynamoDB em repouso com chaves gerenciadas; exigir TLS em transito.
- Separar contas ou, no minimo, ambientes `dev`, `staging` e `prod`; nunca reutilizar certificados ou filas entre eles.
- Criar roles distintos: regra IoT somente envia para SQS; Lambda somente consome a fila e escreve nos prefixos/tabelas necessarios; dashboard somente le a API.

### Observabilidade

Dashboard CloudWatch com: conexoes e mensagens do IoT Core, taxa de rejeicao por schema, profundidade e idade da SQS/DLQ, duracao/erros/throttles da Lambda, latencia e consumo do DynamoDB. Logs devem registrar `message_id`, `device_id` e codigo de falha, sem credenciais nem payloads sensiveis completos.

## 7. Implantacao incremental

1. Criar ambiente de desenvolvimento com poucos dispositivos simulados e o contrato JSON.
2. Configurar certificados, politicas IoT, SQS/DLQ, Lambda e os buckets/tabelas com lifecycle e TTL.
3. Executar teste de carga gradual: 5.000, 10.000, 50.000 e 100.000 sensores simulados, comparando metricas reais com a planilha.
4. Ajustar tamanho de lote, concorrencia reservada da Lambda e alarmes antes de liberar producao.
5. Publicar API/dashboard apenas apos validar deduplicacao, reprocessamento via DLQ e a recuperacao de mensagens invalidas.

## Referencias AWS

- AWS IoT Core e regras: https://docs.aws.amazon.com/iot/latest/developerguide/iot-rules.html
- Amazon SQS: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/welcome.html
- Amazon DynamoDB e TTL: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/TTL.html
- Amazon S3 Lifecycle: https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html
- Amazon CloudWatch: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/WhatIsCloudWatch.html
- AWS IAM: https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction.html
