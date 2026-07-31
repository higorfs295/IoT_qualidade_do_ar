# Consumidor Lambda de telemetria

O `handler.py` implementa o consumidor parcial de lotes SQS:

1. decodifica o corpo produzido pela IoT Rule;
2. valida contrato v1.1 e coerência do tópico;
3. atualiza o estado atual no DynamoDB somente se o ULID for mais novo;
4. retorna `batchItemFailures` para que apenas registros com erro sejam
   repetidos e eventualmente enviados à DLQ.

O histórico bruto é responsabilidade da ação S3 da IoT Rule. Isso impede que
uma falha do consumidor elimine a evidência original.

Para empacotar, inclua `handler.py` e a pasta `poc/qar_poc` como `qar_poc` na
raiz do ZIP/Lambda Layer. `boto3` já existe no runtime AWS; fixe uma versão no
pacote apenas se a aplicação depender de comportamento específico. Configure:

- `CURRENT_STATE_TABLE`;
- event source SQS com `ReportBatchItemFailures`;
- timeout menor que o visibility timeout da fila;
- concorrência reservada e alarmes para erro/throttle/DLQ;
- IAM mínimo: `dynamodb:PutItem` somente na tabela de estado.

O exemplo não cria recursos nem credenciais automaticamente.
