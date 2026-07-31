"""Consumidor SQS para AWS Lambda com resposta parcial por lote.

O histórico bruto é escrito pelo IoT Rule no S3. Esta função valida novamente o
contrato/tópico e atualiza somente o estado mais recente no DynamoDB. Mensagens
inválidas retornam como falha e, após as tentativas configuradas, chegam à DLQ.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

try:
    from qar_poc.contrato import validar_contrato, validar_topico
except ModuleNotFoundError:  # execução/teste diretamente no repositório
    sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "poc"))
    from qar_poc.contrato import validar_contrato, validar_topico


def classificar_registro(record: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    """Retorna (mensagem, erro), sem rede e sem dependência do SDK AWS."""
    try:
        msg = json.loads(record["body"])
    except (KeyError, TypeError, json.JSONDecodeError):
        return None, "corpo SQS nao e JSON"
    if not isinstance(msg, dict):
        return None, "corpo SQS nao e objeto"
    erro = validar_contrato(msg)
    if erro:
        return None, erro
    topico = msg.get("mqtt_topic")
    if not isinstance(topico, str):
        return None, "mqtt_topic ausente na saida da IoT Rule"
    erro = validar_topico(topico, msg)
    return (msg, None) if erro is None else (None, erro)


def _atualizar_estado(msg: dict[str, Any]) -> None:
    """Atualiza por ULID crescente; duplicata/mensagem antiga vira sucesso idempotente."""
    import boto3
    from botocore.exceptions import ClientError

    tabela = os.environ["CURRENT_STATE_TABLE"]
    chave = f"{msg['site_id']}#{msg['device_id']}"
    item = {
        "device_key": {"S": chave},
        "site_id": {"S": msg["site_id"]},
        "device_id": {"S": msg["device_id"]},
        "message_id": {"S": msg["message_id"]},
        "sent_at": {"S": msg["sent_at"]},
        "sequence": {"N": str(msg["sequence"])},
        "payload": {"S": json.dumps(msg, separators=(",", ":"), ensure_ascii=False)},
    }
    try:
        boto3.client("dynamodb").put_item(
            TableName=tabela,
            Item=item,
            ConditionExpression="attribute_not_exists(#pk) OR #mid < :mid",
            ExpressionAttributeNames={"#pk": "device_key", "#mid": "message_id"},
            ExpressionAttributeValues={":mid": {"S": msg["message_id"]}},
        )
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") != "ConditionalCheckFailedException":
            raise


def handler(event: dict[str, Any], _context: Any) -> dict[str, list[dict[str, str]]]:
    falhas: list[dict[str, str]] = []
    for record in event.get("Records", []):
        record_id = str(record.get("messageId", "sem-id"))
        try:
            msg, erro = classificar_registro(record)
            if erro or msg is None:
                raise ValueError(erro or "registro invalido")
            _atualizar_estado(msg)
        except Exception as exc:
            print(json.dumps({"record_id": record_id, "erro": str(exc)}, ensure_ascii=False))
            falhas.append({"itemIdentifier": record_id})
    return {"batchItemFailures": falhas}
