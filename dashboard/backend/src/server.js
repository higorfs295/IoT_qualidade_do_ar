// =============================================================================
//  server.js — Ingestao MVP (Fase 2)
//  Projeto: Estacao de Qualidade do Ar (base_final)
// =============================================================================
//
//  Faz, de forma enxuta, o que a Lambda fara na nuvem:
//   1. assina o broker MQTT (qualidade-ar/+/+/telemetria);
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
//   SERIE_MAX (padrao 500 pontos/dispositivo)  DEVICES_MAX (padrao 10000)
//   BODY_MAX (padrao 65536 bytes)  IDS_MAX (padrao 200000 IDs)
// =============================================================================

import http from "node:http";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";
import mqtt from "mqtt";
import { WebSocketServer } from "ws";
import { validarContrato, validarTopico } from "./contrato.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const WEB_DIR = path.resolve(__dirname, "../../web/public");

const MQTT_URL = process.env.MQTT_URL || "mqtt://localhost:1883";
function inteiroPositivo(valor, padrao, maximo) {
  const n = Number(valor);
  return Number.isInteger(n) && n > 0 && n <= maximo ? n : padrao;
}

const PORT = inteiroPositivo(process.env.PORT, 3001, 65535);
const SERIE_MAX = inteiroPositivo(process.env.SERIE_MAX, 500, 100000);
const BODY_MAX = inteiroPositivo(process.env.BODY_MAX, 65536, 1048576);
const IDS_MAX = inteiroPositivo(process.env.IDS_MAX, 200000, 2000000);
const DEVICES_MAX = inteiroPositivo(process.env.DEVICES_MAX, 10000, 1000000);
const ONLINE_TIMEOUT_MS = inteiroPositivo(process.env.ONLINE_TIMEOUT_MS, 120000, 86400000);
const HTTP_INGEST_TOKEN = process.env.HTTP_INGEST_TOKEN || "";
const HTTP_INGEST_ENABLED = process.env.ENABLE_HTTP_INGEST === "true" ||
  (process.env.NODE_ENV !== "production" && process.env.ENABLE_HTTP_INGEST !== "false");

// --- Estado em memoria -------------------------------------------------------
const dispositivos = new Map(); // device_id -> { site_id, ultimo, serie[], ultimoSeq, ultimoVistoMs }
const idsVistos = new Map();    // message_id -> instante (janela LRU limitada)
const metricas = {
  recebidas: 0, invalidas: 0, lacunas: 0, duplicadas: 0,
  reordenadas: 0, reinicios: 0, inicio: Date.now(),
};

function idDuplicado(messageId) {
  if (idsVistos.has(messageId)) {
    const vistoEm = idsVistos.get(messageId);
    idsVistos.delete(messageId);
    idsVistos.set(messageId, vistoEm);
    return true;
  }
  idsVistos.set(messageId, Date.now());
  if (idsVistos.size > IDS_MAX) {
    const manter = Math.floor(IDS_MAX * 0.9);
    for (const id of idsVistos.keys()) {
      if (idsVistos.size <= manter) break;
      idsVistos.delete(id);
    }
  }
  return false;
}

function ingerir(msg, origem, topico = null) {
  metricas.recebidas++;
  const erro = validarContrato(msg) || (topico ? validarTopico(topico, msg) : null);
  if (erro) { metricas.invalidas++; return { ok: false, erro }; }

  let d = dispositivos.get(msg.device_id);
  if (!d) {
    if (dispositivos.size >= DEVICES_MAX) {
      metricas.invalidas++;
      return { ok: false, erro: "limite de dispositivos atingido" };
    }
    d = { site_id: msg.site_id, ultimo: null, serie: [], ultimoSeq: null,
      ultimoVistoMs: 0, bootId: msg.metadata?.boot_id ?? null };
  } else if (d.site_id !== msg.site_id) {
    metricas.invalidas++;
    return { ok: false, erro: "device_id ja associado a outro site_id" };
  }
  if (idDuplicado(msg.message_id)) {
    metricas.duplicadas++;
    return { ok: true, dup: true };
  }
  if (!dispositivos.has(msg.device_id)) dispositivos.set(msg.device_id, d);
  const bootId = msg.metadata?.boot_id ?? null;
  if (bootId && d.bootId && bootId !== d.bootId) {
    metricas.reinicios++;
    d.ultimoSeq = null;
  }
  if (bootId) d.bootId = bootId;

  let nova = true;
  if (d.ultimoSeq != null) {
    const delta = msg.sequence - d.ultimoSeq;
    if (delta > 1) metricas.lacunas += delta - 1;
    if (delta <= 0) { metricas.reordenadas++; nova = false; }
  }
  d.ultimoVistoMs = Date.now();
  if (!nova) return { ok: true, reordenada: true, origem };

  d.ultimoSeq = msg.sequence;
  d.ultimo = msg;
  d.serie.push({ ts: Date.now(), m: msg.measurements, gas: msg.quality?.gas_status });
  if (d.serie.length > SERIE_MAX) d.serie.shift();

  broadcast({ tipo: "telemetria", device_id: msg.device_id, msg });
  return { ok: true, origem };
}

function online(d) { return Date.now() - d.ultimoVistoMs < ONLINE_TIMEOUT_MS; }

// --- HTTP + REST -------------------------------------------------------------
const TIPOS = { ".html": "text/html; charset=utf-8", ".css": "text/css",
  ".js": "text/javascript", ".svg": "image/svg+xml", ".json": "application/json" };

function json(res, code, obj) {
  const s = JSON.stringify(obj);
  res.writeHead(code, { "content-type": "application/json; charset=utf-8",
    "cache-control": "no-store" });
  res.end(s);
}

async function servirEstatico(res, urlPath) {
  let rel;
  try { rel = decodeURIComponent(urlPath === "/" ? "index.html" : urlPath.replace(/^\/+/, "")); }
  catch { return json(res, 400, { erro: "caminho invalido" }); }
  const fp = path.resolve(WEB_DIR, rel);
  if (fp !== WEB_DIR && !fp.startsWith(WEB_DIR + path.sep))
    return json(res, 403, { erro: "caminho fora da raiz publica" });
  try {
    const dados = await readFile(fp);
    res.writeHead(200, { "content-type": TIPOS[path.extname(fp)] || "application/octet-stream",
      "cache-control": path.extname(fp) === ".html" ? "no-cache" : "public, max-age=300" });
    res.end(dados);
  } catch {
    res.writeHead(404, { "content-type": "text/plain" });
    res.end("nao encontrado");
  }
}

const servidor = http.createServer(async (req, res) => {
  res.setHeader("x-content-type-options", "nosniff");
  res.setHeader("x-frame-options", "DENY");
  res.setHeader("referrer-policy", "no-referrer");
  res.setHeader("content-security-policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self' ws: wss:; img-src 'self' data:");
  const url = new URL(req.url, "http://localhost");
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
    const pedido = Number(url.searchParams.get("n") || 200);
    const n = Number.isInteger(pedido) && pedido > 0 ? Math.min(pedido, SERIE_MAX) : 200;
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
    if (!HTTP_INGEST_ENABLED) return json(res, 404, { erro: "ingestao HTTP desabilitada" });
    if (HTTP_INGEST_TOKEN && req.headers.authorization !== `Bearer ${HTTP_INGEST_TOKEN}`)
      return json(res, 401, { erro: "token de ingestao invalido" });
    if (!(req.headers["content-type"] || "").toLowerCase().startsWith("application/json"))
      return json(res, 415, { erro: "use Content-Type: application/json" });
    let corpo = "";
    let excedeu = false;
    req.setEncoding("utf8");
    req.on("data", (c) => {
      if (excedeu) return;
      corpo += c;
      if (Buffer.byteLength(corpo) > BODY_MAX) {
        excedeu = true;
        corpo = "";
        json(res, 413, { ok: false, erro: "payload excede o limite" });
      }
    });
    req.on("end", () => {
      if (excedeu) return;
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
    const filtro = "qualidade-ar/+/+/telemetria";
    cli.subscribe(filtro, { qos: 1 }, (e) =>
      console.log(e ? `[mqtt] falha ao assinar: ${e}` : `[mqtt] assinando ${filtro}`));
  });
  cli.on("message", (topico, payload) => {
    try { ingerir(JSON.parse(payload.toString()), "mqtt", topico); }
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
