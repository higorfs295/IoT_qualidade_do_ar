import test from "node:test";
import assert from "node:assert/strict";
import { validarContrato, validarTopico } from "../src/contrato.js";

const base = () => ({
  schema_version: "1.1",
  message_id: "01JQ7PK0P3R7V5BT7P0Q9YQ8A1",
  device_id: "esp32-sala-01",
  site_id: "campus-ufg",
  sent_at: "2026-07-31T12:00:00.000Z",
  sequence: 1,
  measurements: {
    co2_ppm: 600, voc_index: 100, lpg_ppm: 4,
    pm1_ugm3: 4.2, pm25_ugm3: 8.5, pm10_ugm3: 12.1,
    temperature_c: 24.3, humidity_pct: 51.2,
  },
  quality: { gas_status: "SAFE", sensor_status: "OK" },
  metadata: { firmware_version: "1.1.0" },
});

test("aceita payload v1.1 canonico", () => assert.equal(validarContrato(base()), null));

test("rejeita NaN, faixa invalida e booleano", () => {
  for (const valor of [NaN, 501, true]) {
    const msg = base();
    msg.measurements.voc_index = valor;
    assert.ok(validarContrato(msg));
  }
});

test("rejeita timestamp sem fuso e sequence negativa", () => {
  const semFuso = base(); semFuso.sent_at = "2026-07-31T12:00:00";
  assert.match(validarContrato(semFuso), /sent_at/);
  const negativa = base(); negativa.sequence = -1;
  assert.match(validarContrato(negativa), /sequence/);
});

test("medida nula exige estado degradado ou erro", () => {
  const msg = base(); msg.measurements.co2_ppm = null;
  assert.match(validarContrato(msg), /status/);
  msg.quality.sensor_status = "ERROR"; msg.quality.gas_status = "UNKNOWN";
  assert.equal(validarContrato(msg), null);
});

test("valida também a tensão diagnóstica opcional", () => {
  const msg = base(); msg.measurements.gas_raw_v = 2.1;
  assert.equal(validarContrato(msg), null);
  for (const valor of [true, Infinity, 5.6]) {
    msg.measurements.gas_raw_v = valor;
    assert.ok(validarContrato(msg));
  }
});

test("topico precisa corresponder ao payload", () => {
  const msg = base();
  assert.equal(validarTopico("qualidade-ar/campus-ufg/esp32-sala-01/telemetria", msg), null);
  assert.match(validarTopico("qualidade-ar/outro/esp32-sala-01/telemetria", msg), /divergente/);
});
