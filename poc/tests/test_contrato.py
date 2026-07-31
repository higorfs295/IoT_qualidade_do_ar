import json
import math
import random
import sys
import unittest
from copy import deepcopy
from pathlib import Path

POC_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(POC_DIR))

from qar_poc import contrato  # noqa: E402
from qar_poc.sensor import Dispositivo  # noqa: E402


class ContratoTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.exemplo = json.loads((POC_DIR / "payload_exemplo.json").read_text(encoding="utf-8"))

    def test_exemplo_v11_e_valido(self):
        self.assertIsNone(contrato.validar_contrato(self.exemplo))

    def test_ulid_canonico_e_ordenavel(self):
        rng = random.Random(7)
        primeiro = contrato.gerar_ulid(rng, 1_000)
        segundo = contrato.gerar_ulid(rng, 1_001)
        self.assertRegex(primeiro, r"^[0-9A-HJKMNP-TV-Z]{26}$")
        self.assertLess(primeiro, segundo)

    def test_rejeita_timestamp_sem_fuso(self):
        msg = deepcopy(self.exemplo)
        msg["sent_at"] = "2026-07-31T10:00:00"
        self.assertIn("sent_at", contrato.validar_contrato(msg))

    def test_rejeita_nan_booleano_e_fora_de_faixa(self):
        for valor in (math.nan, True, 501):
            with self.subTest(valor=valor):
                msg = deepcopy(self.exemplo)
                msg["measurements"]["voc_index"] = valor
                self.assertIsNotNone(contrato.validar_contrato(msg))

    def test_nulo_exige_status_nao_ok(self):
        msg = deepcopy(self.exemplo)
        msg["measurements"]["co2_ppm"] = None
        self.assertIn("status", contrato.validar_contrato(msg))
        msg["quality"]["sensor_status"] = "ERROR"
        msg["quality"]["gas_status"] = "UNKNOWN"
        self.assertIsNone(contrato.validar_contrato(msg))

    def test_medida_diagnostica_opcional_tambem_e_validada(self):
        msg = deepcopy(self.exemplo)
        msg["measurements"]["gas_raw_v"] = 2.1
        self.assertIsNone(contrato.validar_contrato(msg))
        for valor in (True, math.inf, 5.6):
            with self.subTest(valor=valor):
                msg["measurements"]["gas_raw_v"] = valor
                self.assertIsNotNone(contrato.validar_contrato(msg))

    def test_topico_deve_coincidir_com_payload(self):
        certo = contrato.montar_topico(self.exemplo["site_id"], self.exemplo["device_id"])
        self.assertIsNone(contrato.validar_topico(certo, self.exemplo))
        self.assertIsNotNone(contrato.validar_topico("qualidade-ar/outro/id/telemetria", self.exemplo))

    def test_sensor_virtual_emite_payload_valido(self):
        sensor = Dispositivo("esp32-teste-01", "bancada", seed=123)
        for _ in range(25):
            self.assertIsNone(contrato.validar_contrato(sensor.proxima_leitura(0.15)))


if __name__ == "__main__":
    unittest.main()
