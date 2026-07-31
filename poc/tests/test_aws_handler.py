import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "infra" / "aws" / "lambda_ingest"))

from handler import classificar_registro, handler  # noqa: E402


class AwsHandlerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = json.loads((ROOT / "poc" / "payload_exemplo.json").read_text(encoding="utf-8"))

    def registro(self, payload=None):
        msg = dict(payload or self.payload)
        msg["mqtt_topic"] = f"qualidade-ar/{msg['site_id']}/{msg['device_id']}/telemetria"
        msg["ingested_at"] = 1785524400000
        return {"messageId": "sqs-1", "body": json.dumps(msg)}

    def test_aceita_saida_da_iot_rule(self):
        msg, erro = classificar_registro(self.registro())
        self.assertIsNone(erro)
        self.assertEqual(msg["device_id"], self.payload["device_id"])

    def test_rejeita_topico_divergente_e_json_invalido(self):
        registro = self.registro()
        corpo = json.loads(registro["body"])
        corpo["mqtt_topic"] = "qualidade-ar/outro/dispositivo/telemetria"
        registro["body"] = json.dumps(corpo)
        self.assertIsNotNone(classificar_registro(registro)[1])
        self.assertIsNotNone(classificar_registro({"body": "{"})[1])

    def test_handler_retorna_somente_falha_parcial(self):
        valido = self.registro()
        invalido = {"messageId": "sqs-invalido", "body": "{"}
        with patch("handler._atualizar_estado") as atualizar:
            resposta = handler({"Records": [valido, invalido]}, None)
        atualizar.assert_called_once()
        self.assertEqual(
            resposta,
            {"batchItemFailures": [{"itemIdentifier": "sqs-invalido"}]},
        )
