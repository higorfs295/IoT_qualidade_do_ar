import test from "node:test";
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { readFile, mkdtemp, rm } from "node:fs/promises";
import net from "node:net";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const AQUI = path.dirname(fileURLToPath(import.meta.url));
const BACKEND = path.resolve(AQUI, "..");
const ROOT = path.resolve(BACKEND, "../..");

async function portaLivre() {
  return new Promise((resolve, reject) => {
    const s = net.createServer();
    s.once("error", reject);
    s.listen(0, "127.0.0.1", () => {
      const porta = s.address().port;
      s.close(() => resolve(porta));
    });
  });
}

async function esperar(url, condicao, timeout = 8000) {
  const fim = Date.now() + timeout;
  while (Date.now() < fim) {
    try {
      const resposta = await fetch(url);
      if (resposta.ok) {
        const valor = await resposta.json();
        if (!condicao || condicao(valor)) return valor;
      }
    } catch { /* processo ainda inicializando */ }
    await new Promise((resolve) => setTimeout(resolve, 80));
  }
  throw new Error(`timeout aguardando ${url}`);
}

function iniciar(porta, dataDir) {
  return spawn(process.execPath, ["src/server.js"], {
    cwd: BACKEND,
    env: {
      ...process.env, PORT: String(porta), HOST: "127.0.0.1",
      MQTT_ENABLED: "false", ENABLE_HTTP_INGEST: "true",
      DATA_DIR: dataDir, PERSIST_INTERVAL_MS: "50",
    },
    stdio: "ignore",
  });
}

async function parar(processo) {
  if (processo.exitCode !== null) return;
  processo.kill("SIGTERM");
  await Promise.race([
    new Promise((resolve) => processo.once("exit", resolve)),
    new Promise((resolve) => setTimeout(resolve, 3000)),
  ]);
  if (processo.exitCode === null) processo.kill("SIGKILL");
}

test("API, PWA e persistencia sobrevivem ao reinicio", async () => {
  const porta = await portaLivre();
  const dataDir = await mkdtemp(path.join(os.tmpdir(), "qar-integration-"));
  let processo = iniciar(porta, dataDir);
  try {
    const base = `http://127.0.0.1:${porta}`;
    await esperar(`${base}/api/health`, (h) => h.ok && h.persistence_enabled);
    const payload = await readFile(path.join(ROOT, "poc/payload_exemplo.json"), "utf8");
    const ingestao = await fetch(`${base}/api/ingest`, {
      method: "POST", headers: { "content-type": "application/json" }, body: payload,
    });
    assert.equal(ingestao.status, 200);
    await esperar(`${base}/api/dispositivos`, (d) => d.length === 1);
    await new Promise((resolve) => setTimeout(resolve, 180));
    await parar(processo);

    processo = iniciar(porta, dataDir);
    const restaurados = await esperar(`${base}/api/dispositivos`, (d) => d.length === 1);
    assert.equal(restaurados[0].device_id, JSON.parse(payload).device_id);
    const manifest = await fetch(`${base}/manifest.webmanifest`);
    assert.match(manifest.headers.get("content-type"), /manifest\+json/);
    assert.equal((await fetch(`${base}/sw.js`)).status, 200);
    const prometheus = await (await fetch(`${base}/metrics`)).text();
    assert.match(prometheus, /qar_devices 1/);
  } finally {
    await parar(processo);
    await rm(dataDir, { recursive: true, force: true });
  }
});
