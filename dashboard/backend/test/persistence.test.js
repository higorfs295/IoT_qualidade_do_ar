import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, rm } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import {
  carregarSnapshot, criarSnapshot, normalizarSnapshot, salvarSnapshot,
} from "../src/persistence.js";

function estado() {
  const dispositivos = new Map([["esp32-01", {
    site_id: "lab", ultimo: { sequence: 2 },
    serie: [{ ts: 1 }, { ts: 2 }, { ts: 3 }], ultimoSeq: 2,
    ultimoVistoMs: 1234, bootId: "01JQ7PK0P3R7V5BT7P0Q9YQ8A2",
  }]]);
  const ids = new Map([["id-1", 1], ["id-2", 2], ["id-3", 3]]);
  const metricas = { recebidas: 3, invalidas: 1, lacunas: 2, duplicadas: 0, reordenadas: 0, reinicios: 1 };
  return { dispositivos, ids, metricas };
}

test("snapshot limita serie e janela de deduplicacao", () => {
  const e = estado();
  const snap = criarSnapshot(e.dispositivos, e.ids, e.metricas, { serieMax: 2, idsMax: 2 });
  assert.equal(snap.dispositivos[0].serie.length, 2);
  assert.deepEqual(snap.ids_vistos.map((p) => p[0]), ["id-2", "id-3"]);
  const restaurado = normalizarSnapshot(snap, { serieMax: 2, idsMax: 2, devicesMax: 2 });
  assert.equal(restaurado.dispositivos.get("esp32-01").ultimoSeq, 2);
  assert.equal(restaurado.metricas.lacunas, 2);
});

test("persistencia atomica pode ser recarregada", async () => {
  const dir = await mkdtemp(path.join(os.tmpdir(), "qar-state-"));
  try {
    const arquivo = path.join(dir, "state.json");
    const e = estado();
    const snap = criarSnapshot(e.dispositivos, e.ids, e.metricas);
    await salvarSnapshot(arquivo, snap);
    const restaurado = await carregarSnapshot(arquivo);
    assert.equal(restaurado.dispositivos.size, 1);
    assert.equal(restaurado.idsVistos.size, 3);
    assert.equal(restaurado.metricas.recebidas, 3);
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
});
