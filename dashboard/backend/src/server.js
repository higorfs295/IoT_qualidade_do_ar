// =============================================================================
//  server.js — Ingestao MVP (Fase 2)
//  Projeto: Estacao de Qualidade do Ar (base_final)
// =============================================================================
//
//  Faz, de forma enxuta, o que a Lambda fara na nuvem:
//   1. assina o broker MQTT (qualidade-ar/#);
//   2. VALIDA cada mensagem contra o contrato v1.1 (contrato.js);
//   3. deduplica por message_id e DETECTA LACUNAS por sequence;
//   4. guarda a serie temporal (em memoria) e o estado atual por dispositivo;
//   5. serve REST + WebSocket (tempo real) + o dashboard estatico.
//
//  Armazenamento: em memoria (ring buffer). Evolucao: SQLite/TimescaleDB (ver
//  dashboard/backend/README.md). Sem dependencia de banco para o MVP rodar.
//
//  Variaveis de ambiente:
//   MQTT_URL   (padrao mqtt://localhost:1883)   PORT (padrao 3001)
//   SERIE_MAX  (padrao 500 pontos por dispositivo)
// =============================================================================

import http from "node:http";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";
import mqtt from "mqtt";
import { WebSocketServer } from "ws";
import { validarContrato } from "./contrato.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const WEB_DIR = path.resolve(__dirname, "../../web/public");

const MQTT_URL = process.env.MQTT_URL || "mqtt://localhost:1883";
const PORT = Number(process.env.PORT || 3001);
const SERIE_MAX = Number(process.env.SERIE_MAX || 500);

// --- Estado em memoria -------------------------------------------------------
const dispositivos = new Map(); // device_id -> { site_id, ultimo, serie[], ultimoSeq, ultimoVistoMs }
const idsVistos = new Set();    // message_id (janela deslizante)
const metricas = {
  recebidas: 0, invalidas: 0, lacunas: 0, duplicadas: 0, inicio: Date.now(),
};

function ingerir(msg, origem) {
  metricas.recebidas++;
  const erro = validarContrato(msg);
  if (erro) { metricas.invalidas++; return { ok: false, erro }; }

  if (idsVistos.has(msg.message_id)) { metricas.duplicadas++; return { ok: true, dup: true }; }
  idsVistos.add(msg.message_id);
  if (idsVistos.size > 200000) idsVistos.clear();

  let d = dispositivos.get(msg.device_id);
  if (!d) {
    d = { site_id: msg.site_id, ultimo: null, serie: [], ultimoSeq: null, ultimoVistoMs: 0 };
    dispositivos.set(msg.device_id, d);
  }
  if (d.ultimoSeq != null) {
    const delta = msg.sequence - d.ultimoSeq;
    if (delta > 1) metricas.lacunas += delta - 1;
  }
  d.ultimoSeq = Math.max(msg.sequence, d.ultimoSeq ?? msg.sequence);
  d.site_id = msg.site_id;
  d.ultimo = msg;
  d.ultimoVistoMs = Date.now();
  d.serie.push({ ts: Date.now(), m: msg.measurements, gas: msg.quality?.gas_status });
  if (d.serie.length > SERIE_MAX) d.serie.shift();

  broadcast({ tipo: "telemetria", device_id: msg.device_id, msg });
  return { ok: true, origem };
}

function online(d) { return Date.now() - d.ultimoVistoMs < 120000; }

// --- HTTP + REST -------------------------------------------------------------
const TIPOS = { ".html": "text/html; charset=utf-8", ".css": "text/css",
  ".js": "text/javascript", ".svg": "image/svg+xml", ".json": "application/json" };

function json(res, code, obj) {
  const s = JSON.stringify(obj);
  res.writeHead(code, { "content-type": "application/json; charset=utf-8" });
  res.end(s);
}

async function servirEstatico(res, urlPath) {
  const rel = urlPath === "/" ? "/index.html" : urlPath;
  const fp = path.join(WEB_DIR, path.normalize(rel).replace(/^(\.\.[/\\])+/, ""));
  try {
    const dados = await readFile(fp);
    res.writeHead(200, { "content-type": TIPOS[path.extname(fp)] || "application/octet-stream" });
    res.end(dados);
  } catch {
    res.writeHead(404, { "content-type": "text/plain" });
    res.end("nao encontrado");
  }
}

const servidor = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host}`);
  const p = url.pathname;

  // --- API ---
  if (p === "/api/dispositivos") {
    const lista = [...dispositivos.entries()].map(([id, d]) => ({
      device_id: id, site_id: d.site_id, online: online(d), ultimo: d.ultimo,
    }));
    return json(res, 200, lista);
  }
  if (p.startsWith("/api/dispositivos/") && p.endsWith("/atual")) {
    const id = decodeURIComponent(p.split("/")[3]);
    const d = dispositivos.get(id);
    return d ? json(res, 200, d.ultimo) : json(res, 404, { erro: "sem dispositivo" });
  }
  if (p.startsWith("/api/dispositivos/") && p.endsWith("/serie")) {
    const id = decodeURIComponent(p.split("/")[3]);
    const campo = url.searchParams.get("campo") || "co2_ppm";
    const n = Math.min(Number(url.searchParams.get("n") || 200), SERIE_MAX);
    const d = dispositivos.get(id);
    if (!d) return json(res, 404, { erro: "sem dispositivo" });
    const serie = d.serie.slice(-n).map((p) => ({ ts: p.ts, valor: p.m?.[campo] ?? null }));
    return json(res, 200, { campo, serie });
  }
  if (p === "/api/metricas") {
    return json(res, 200, {
      ...metricas, dispositivos: dispositivos.size,
      online: [...dispositivos.values()].filter(online).length,
      uptime_s: Math.round((Date.now() - metricas.inicio) / 1000),
    });
  }
  // Ingestao por HTTP (para teste/dev sem broker; mesmo caminho do MQTT).
  if (p === "/api/ingest" && req.method === "POST") {
    let corpo = "";
    req.on("data", (c) => (corpo += c));
    req.on("end", () => {
      try { return json(res, 200, ingerir(JSON.parse(corpo), "http")); }
      catch { return json(res, 400, { ok: false, erro: "json invalido" }); }
    });
    return;
  }

  // --- Estatico (dashboard) ---
  return servirEstatico(res, p);
});

// --- WebSocket (tempo real) --------------------------------------------------
const wss = new WebSocketServer({ server: servidor, path: "/ws" });
function broadcast(obj) {
  const s = JSON.stringify(obj);
  for (const c of wss.clients) if (c.readyState === 1) c.send(s);
}
wss.on("connection", (ws) => {
  ws.send(JSON.stringify({ tipo: "ola", dispositivos: dispositivos.size }));
});

// --- MQTT --------------------------------------------------------------------
function conectarMqtt() {
  const cli = mqtt.connect(MQTT_URL, { reconnectPeriod: 3000 });
  cli.on("connect", () => {
    console.log(`[mqtt] conectado em ${MQTT_URL}`);
    cli.subscribe("qualidade-ar/#", { qos: 1 }, (e) =>
      console.log(e ? `[mqtt] falha ao assinar: ${e}` : "[mqtt] assinando qualidade-ar/#"));
  });
  cli.on("message", (_topico, payload) => {
    try { ingerir(JSON.parse(payload.toString()), "mqtt"); }
    catch { metricas.recebidas++; metricas.invalidas++; }
  });
  cli.on("error", (e) => console.log(`[mqtt] erro: ${e.message}`));
}

servidor.listen(PORT, () => {
  console.log("=".repeat(60));
  console.log(" Ingestao MVP — Estacao de Qualidade do Ar (Fase 2)");
  console.log("=".repeat(60));
  console.log(`  dashboard .... http://localhost:${PORT}`);
  console.log(`  API .......... http://localhost:${PORT}/api/metricas`);
  console.log(`  broker MQTT .. ${MQTT_URL}`);
  console.log("=".repeat(60));
  conectarMqtt();
});
