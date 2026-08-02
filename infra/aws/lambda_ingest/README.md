# Lambda de ingestão AWS

Consumidor parcial de lotes SQS para o contrato de telemetria v1.1. Cada
registro é validado contra payload/tópico; o estado atual no DynamoDB só avança
quando o ULID é mais novo. Erros retornam em `batchItemFailures`, permitindo
repetição individual e DLQ sem reprovar o lote inteiro.

O evento bruto é gravado pela IoT Rule no S3 antes deste consumidor.

## Gerar o ZIP autocontido

Na raiz do repositório:

```bash
python infra/aws/lambda_ingest/package.py \
  --output entrega/aws/qar-lambda-ingest.zip
```

O pacote inclui `handler.py` e `qar_poc/` na raiz e usa timestamps fixos para
ser determinístico. `boto3` é fornecido pelo runtime. Para revisar:

```bash
python -m zipfile -l entrega/aws/qar-lambda-ingest.zip
python -m unittest poc.tests.test_aws_template -v
```

Hash auditado do ZIP atual:
`7ED1D4E4F27A4076C5132EEF4FB4809967928B2FCD3B4423C4BCF0299650A40D`.

## Publicar e aplicar o template

1. Crie/eleja um bucket de artefatos na mesma região e habilite versionamento.
2. Envie `qar-lambda-ingest.zip` e anote bucket, key e version ID.
3. Valide `sandbox.template.json` e crie um change set passando
   `LambdaCodeS3Bucket`, `LambdaCodeS3Key` e opcionalmente `LambdaCodeS3Version`.
4. Revise IAM, nomes, tags, retenção, concorrência e custo antes de executar.
5. Após criar a stack, configure Thing/certificado/política do dispositivo e
   teste S3, fila, Lambda, DynamoDB, DLQ e alarmes.

Exemplo deliberadamente incompleto, para evitar implantar sem revisão:

```bash
aws cloudformation validate-template \
  --template-body file://infra/aws/sandbox.template.json

aws cloudformation deploy \
  --template-file infra/aws/sandbox.template.json \
  --stack-name qar-sandbox \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    LambdaCodeS3Bucket=BUCKET_REVISADO \
    LambdaCodeS3Key=CAMINHO_REVISADO/qar-lambda-ingest.zip
```

O template usa Python 3.13, `ReportBatchItemFailures`, concorrência reservada,
SSE, retenções e alarmes. Timeout Lambda é 30 s e o visibility timeout SQS é
maior. Nenhum recurso foi criado durante a revisão: AWS pode gerar custos, e a
execução exige conta sandbox, orçamento e autorização explícita.

## Teardown controlado

Antes de apagar a stack, decida se os objetos S3 devem ser exportados. Buckets
não vazios podem bloquear remoção; não force exclusão sem confirmar a retenção.
Depois verifique filas, tabela, logs, certificados IoT e objetos remanescentes.
