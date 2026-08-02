import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]


class AwsInfrastructureTest(unittest.TestCase):
    def test_template_liga_iot_fila_lambda_e_estado(self):
        template = json.loads((ROOT / "infra/aws/sandbox.template.json").read_text(encoding="utf-8"))
        resources = template["Resources"]
        self.assertEqual(resources["TelemetryIngestFunction"]["Properties"]["Runtime"], "python3.13")
        mapping = resources["TelemetryQueueMapping"]["Properties"]
        self.assertEqual(mapping["FunctionResponseTypes"], ["ReportBatchItemFailures"])
        self.assertEqual(mapping["EventSourceArn"], {"Fn::GetAtt": ["TelemetryQueue", "Arn"]})
        self.assertGreaterEqual(
            resources["TelemetryQueue"]["Properties"]["VisibilityTimeout"],
            resources["TelemetryIngestFunction"]["Properties"]["Timeout"] * 3,
        )
        self.assertIn("${message_id}", resources["TelemetryRule"]["Properties"]["TopicRulePayload"]["Actions"][1]["S3"]["Key"])

    def test_pacote_lambda_e_autocontido(self):
        import importlib.util

        script = ROOT / "infra/aws/lambda_ingest/package.py"
        spec = importlib.util.spec_from_file_location("lambda_package", script)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            output, digest = module.build(Path(directory) / "lambda.zip")
            self.assertEqual(len(digest), 64)
            with ZipFile(output) as zf:
                self.assertIn("handler.py", zf.namelist())
                self.assertIn("qar_poc/contrato.py", zf.namelist())


if __name__ == "__main__":
    unittest.main()
