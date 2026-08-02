// =============================================================================
//  server.js — servico local de ingestao e consulta
//  Projeto: Estacao de Qualidade do Ar (base_final)
// =============================================================================
//
//  Faz, de forma enxuta, o que a Lambda fara na nuvem:
//   1. assina o broker MQTT (qualidade-ar/+/+/telemetria);
//   2. VALIDA cada mensagem contra o contrato v1.1 (contrato.js);
//   3. deduplica por message_id e DETECTA LACUNAS por sequence;
//   4. guarda a serie temporal limitada e persiste snapshots atomicos;
//   5. serve REST + WebSocket (tempo real) + o dashboard estatico.
//
//  Armazenamento local: ring buffers limitados + snapshot JSON atomico. Um banco
//  temporal continua recomendado para retencao longa, concorrencia ou HA.
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
import { MEDIDAS_POR_VERSAO, validarContrato, validarTopico } from "./contrato.js";
import { carregarSnapshot, criarSnapshot, salvarSnapshot } from "./persistence.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const WEB_DIR = path.resolve(__dirname, "../../web/public");

const MQTT_URL = process.env.MQTT_URL || "mqtt://localhost:1883";
const MQTT_ENABLED = process.env.MQTT_ENABLED !== "false";
function inteiroPositivo(valor, padrao, maximo) {
  const n = Number(valor);
  return Number.isInteger(n) && n > 0 && n <= maximo ? n : padrao;
}

const PORT = inteiroPositivo(process.env.PORT, 3001, 65535);
const HOST = process.env.HOST || "0.0.0.0";
const SERIE_MAX = inteiroPositivo(process.env.SERIE_MAX, 500, 100000);
const BODY_MAX = inteiroPositivo(process.env.BODY_MAX, 65536, 1048576);
const IDS_MAX = inteiroPositivo(process.env.IDS_MAX, 200000, 2000000);
const DEVICES_MAX = inteiroPositivo(process.env.DEVICES_MAX, 10000, 1000000);
const ONLINE_TIMEOUT_MS = inteiroPositivo(process.env.ONLINE_TIMEOUT_MS, 120000, 86400000);
const HTTP_INGEST_TOKEN = process.env.HTTP_INGEST_TOKEN || "";
const DATA_DIR = process.env.DATA_DIR || "";
const STATE_FILE = process.env.STATE_FILE || (DATA_DIR ? path.join(DATA_DIR, "state.json") : "");
const PERSIST_INTERVAL_MS = inteiroPositivo(process.env.PERSIST_INTERVAL_MS, 5000, 3600000);
const HTTP_INGEST_ENABLED = process.env.ENABLE_HTTP_INGEST === "true" ||
  (process.env.NODE_ENV !== "production" && process.env.ENABLE_HTTP_INGEST !== "false");
const CORS_ORIGINS = new Set((process.env.CORS_ORIGINS || "")
  .split(",").map((item) => item.trim().replace(/\/$/, "")).filter(Boolean));
const CAMPOS_SERIE = new Set([...new Set(Object.values(MEDIDAS_POR_VERSAO).flat()), "gas_raw_v"]);

// --- Estado em memoria -------------------------------------------------------
const dispositivos = new Map(); // device_id -> { site_id, ultimo, serie[], ultimoSeq, ultimoVistoMs }
const idsVistos = new Map();    // message_id -> instante (janela LRU limitada)
const metricas = {
  recebidas: 0, invalidas: 0, lacunas: 0, duplicadas: 0,
  reordenadas: 0, reinicios: 0, inicio: Date.now(),
};
const limitesPersistencia = { serieMax: SERIE_MAX, idsMax: IDS_MAX, devicesMax: DEVICES_MAX };
let persistenciaSuja = false;
let tarefaPersistencia = null;
let ultimoPersistidoEm = null;
let erroPersistencia = null;

function marcarPersistencia() { if (STATE_FILE) persistenciaSuja = true; }

async function restaurarPersistencia() {
  if (!STATE_FILE) return;
  try {
    const salvo = await carregarSnapshot(STATE_FILE, limitesPersistencia);
    if (!salvo) return;
    for (const [id, d] of salvo.dispositivos) dispositivos.set(id, d);
    for (const [id, instante] of salvo.idsVistos) idsVistos.set(id, instante);
    Object.assign(metricas, salvo.metricas, { inicio: Date.now() });
    ultimoPersistidoEm = salvo.savedAt;
    console.log(`[persistencia] restaurados ${dispositivos.size} dispositivo(s)`);
  } catch (erro) {
    erroPersistencia = erro.message;
    console.error(`[persistencia] estado ignorado: ${erro.message}`);
  }
}

async function persistirAgora(forcar = false) {
  if (!STATE_FILE) return;
  if (tarefaPersistencia) {
    await tarefaPersistencia;
    if (forcar && persistenciaSuja) return persistirAgora(true);
    return;
  }
  if (!persistenciaSuja && !forcar) return;
  persistenciaSuja = false;
  tarefaPersistencia = (async () => {
    try {
      const snapshot = criarSnapshot(dispositivos, idsVistos, metricas, limitesPersistencia);
      await salvarSnapshot(STATE_FILE, snapshot);
      ultimoPersistidoEm = snapshot.saved_at;
      erroPersistencia = null;
    } catch (erro) {
      persistenciaSuja = true;
      erroPersistencia = erro.message;
      console.error(`[persistencia] falha ao salvar: ${erro.message}`);
    }
  })();
  await tarefaPersistencia;
  tarefaPersistencia = null;
}

await restaurarPersistencia();
const timerPersistencia = STATE_FILE
  ? setInterval(() => { void persistirAgora(); }, PERSIST_INTERVAL_MS)
  : null;

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
  marcarPersistencia();
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
  ".js": "text/javascript", ".svg": "image/svg+xml", ".json": "application/json",
  ".webmanifest": "application/manifest+json" };

function json(res, code, obj) {
  const s = JSON.stringify(obj);
  res.writeHead(code, { "content-type": "application/json; charset=utf-8",
    "cache-control": "no-store" });
  res.end(s);
}

function metodoPermitido(req, res, permitido) {
  if (req.method === permitido) return true;
  res.setHeader("allow", permitido);
  json(res, 405, { erro: `metodo nao permitido; use ${permitido}` });
  return false;
}

function aplicarCors(req, res) {
  const origem = req.headers.origin?.replace(/\/$/, "");
  const permitida = origem && CORS_ORIGINS.has(origem);
  if (permitida) {
    res.setHeader("access-control-allow-origin", origem);
    res.setHeader("vary", "Origin");
    res.setHeader("access-control-allow-methods", "GET, POST, OPTIONS");
    res.setHeader("access-control-allow-headers", "Content-Type, Authorization");
    res.setHeader("access-control-max-age", "600");
  }
  if (req.method !== "OPTIONS") return false;
  if (!permitida) {
    json(res, 403, { erro: "origem CORS nao autorizada" });
  } else {
    res.writeHead(204);
    res.end();
  }
  return true;
}

function decodificarSegmento(valor) {
  try { return decodeURIComponent(valor); }
  catch { return null; }
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

async function tratarRequisicao(req, res) {
  res.setHeader("x-content-type-options", "nosniff");
  res.setHeader("x-frame-options", "DENY");
  res.setHeader("referrer-policy", "no-referrer");
  res.setHeader("permissions-policy", "camera=(), microphone=(), geolocation=()");
  res.setHeader("content-security-policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self' http: https: ws: wss:; img-src 'self' data:");
  if (aplicarCors(req, res)) return;
  let url;
  try { url = new URL(req.url, "http://localhost"); }
  catch { return json(res, 400, { erro: "URL invalida" }); }
  const p = url.pathname;

  // --- API ---
  if (p === "/api/health") {
    if (!metodoPermitido(req, res, "GET")) return;
    return json(res, 200, {
      ok: true,
      ready: !MQTT_ENABLED || (mqttConectado && mqttAssinado),
      mqtt_enabled: MQTT_ENABLED,
      mqtt_connected: mqttConectado,
      mqtt_subscribed: mqttAssinado,
      persistence_enabled: Boolean(STATE_FILE),
      persistence_last_saved_at: ultimoPersistidoEm,
      persistence_error: erroPersistencia,
      devices: dispositivos.size,
      uptime_s: Math.round((Date.now() - metricas.inicio) / 1000),
    });
  }
  if (p === "/api/info") {
    if (!metodoPermitido(req, res, "GET")) return;
    return json(res, 200, {
      api_version: "1.1.0",
      telemetry_schema_versions: ["1.0", "1.1"],
      series_fields: [...CAMPOS_SERIE].sort(),
      websocket_path: "/ws",
      http_ingest_enabled: HTTP_INGEST_ENABLED,
    });
  }
  if (p === "/api/dispositivos") {
    if (!metodoPermitido(req, res, "GET")) return;
    const lista = [...dispositivos.entries()].map(([id, d]) => ({
      device_id: id, site_id: d.site_id, online: online(d), ultimo: d.ultimo,
    })).sort((a, b) => a.device_id.localeCompare(b.device_id));
    return json(res, 200, lista);
  }
  const rotaAtual = /^\/api\/dispositivos\/([^/]+)\/atual$/.exec(p);
  if (rotaAtual) {
    if (!metodoPermitido(req, res, "GET")) return;
    const id = decodificarSegmento(rotaAtual[1]);
    if (id === null) return json(res, 400, { erro: "device_id invalido" });
    const d = dispositivos.get(id);
    return d ? json(res, 200, d.ultimo) : json(res, 404, { erro: "sem dispositivo" });
  }
  const rotaSerie = /^\/api\/dispositivos\/([^/]+)\/serie$/.exec(p);
  if (rotaSerie) {
    if (!metodoPermitido(req, res, "GET")) return;
    const id = decodificarSegmento(rotaSerie[1]);
    if (id === null) return json(res, 400, { erro: "device_id invalido" });
    const campo = url.searchParams.get("campo") || "co2_ppm";
    if (!CAMPOS_SERIE.has(campo))
      return json(res, 400, { erro: "campo de serie invalido", campos: [...CAMPOS_SERIE].sort() });
    const pedido = Number(url.searchParams.get("n") || 200);
    const n = Number.isInteger(pedido) && pedido > 0 ? Math.min(pedido, SERIE_MAX) : 200;
    const d = dispositivos.get(id);
    if (!d) return json(res, 404, { erro: "sem dispositivo" });
    const serie = d.serie.slice(-n).map((p) => ({ ts: p.ts, valor: p.m?.[campo] ?? null }));
    return json(res, 200, { campo, serie });
  }
  if (p === "/api/metricas") {
    if (!metodoPermitido(req, res, "GET")) return;
    return json(res, 200, {
      ...metricas, dispositivos: dispositivos.size,
      online: [...dispositivos.values()].filter(online).length,
      uptime_s: Math.round((Date.now() - metricas.inicio) / 1000),
    });
  }
  if (p === "/metrics") {
    if (!metodoPermitido(req, res, "GET")) return;
    const linhas = [
      "# HELP qar_messages_received_total Mensagens recebidas pelo backend.",
      "# TYPE qar_messages_received_total counter",
      `qar_messages_received_total ${metricas.recebidas}`,
      "# TYPE qar_messages_invalid_total counter",
      `qar_messages_invalid_total ${metricas.invalidas}`,
      "# TYPE qar_messages_duplicate_total counter",
      `qar_messages_duplicate_total ${metricas.duplicadas}`,
      "# TYPE qar_sequence_gaps_total counter",
      `qar_sequence_gaps_total ${metricas.lacunas}`,
      "# TYPE qar_devices gauge",
      `qar_devices ${dispositivos.size}`,
      "# TYPE qar_devices_online gauge",
      `qar_devices_online ${[...dispositivos.values()].filter(online).length}`,
      "# TYPE qar_mqtt_connected gauge",
      `qar_mqtt_connected ${mqttConectado ? 1 : 0}`,
      "# TYPE qar_mqtt_subscribed gauge",
      `qar_mqtt_subscribed ${mqttAssinado ? 1 : 0}`,
      "# TYPE qar_persistence_error gauge",
      `qar_persistence_error ${erroPersistencia ? 1 : 0}`,
      "",
    ];
    res.writeHead(200, { "content-type": "text/plain; version=0.0.4; charset=utf-8", "cache-control": "no-store" });
    return res.end(linhas.join("\n"));
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
        metricas.recebidas++; metricas.invalidas++; marcarPersistencia();
        json(res, 413, { ok: false, erro: "payload excede o limite" });
      }
    });
    req.on("end", () => {
      if (excedeu) return;
      try { return json(res, 200, ingerir(JSON.parse(corpo), "http")); }
      catch {
        metricas.recebidas++; metricas.invalidas++; marcarPersistencia();
        return json(res, 400, { ok: false, erro: "json invalido" });
      }
    });
    return;
  }

  if (p.startsWith("/api/")) return json(res, 404, { erro: "recurso inexistente" });

  // --- Estatico (dashboard) ---
  if (!metodoPermitido(req, res, "GET")) return;
  return servirEstatico(res, p);
}

const servidor = http.createServer((req, res) => {
  void tratarRequisicao(req, res).catch((erro) => {
    console.error(`[http] falha inesperada: ${erro.message}`);
    if (!res.headersSent) json(res, 500, { erro: "falha interna" });
    else res.destroy();
  });
});

// --- WebSocket (tempo real) --------------------------------------------------
const wss = new WebSocketServer({ server: servidor, path: "/ws", maxPayload: 65536 });
function broadcast(obj) {
  const s = JSON.stringify(obj);
  for (const c of wss.clients) if (c.readyState === 1) c.send(s);
}
wss.on("connection", (ws) => {
  ws.isAlive = true;
  ws.on("pong", () => { ws.isAlive = true; });
  ws.send(JSON.stringify({ tipo: "ola", dispositivos: dispositivos.size }));
});
const timerWebSocket = setInterval(() => {
  for (const ws of wss.clients) {
    if (ws.isAlive === false) { ws.terminate(); continue; }
    ws.isAlive = false;
    ws.ping();
  }
}, 30000);
timerWebSocket.unref();

// --- MQTT --------------------------------------------------------------------
let mqttConectado = false;
let mqttAssinado = false;
let clienteMqtt = null;

function mqttUrlSemSegredo(valor) {
  try {
    const url = new URL(valor);
    if (url.username) url.username = "***";
    if (url.password) url.password = "***";
    return url.toString();
  } catch { return "URL MQTT configurada"; }
}

function conectarMqtt() {
  const cli = mqtt.connect(MQTT_URL, { reconnectPeriod: 3000 });
  clienteMqtt = cli;
  cli.on("connect", () => {
    mqttConectado = true;
    mqttAssinado = false;
    console.log(`[mqtt] conectado em ${mqttUrlSemSegredo(MQTT_URL)}`);
    const filtro = "qualidade-ar/+/+/telemetria";
    cli.subscribe(filtro, { qos: 1 }, (e) => {
      mqttAssinado = !e;
      console.log(e ? `[mqtt] falha ao assinar: ${e}` : `[mqtt] assinando ${filtro}`);
    });
  });
  cli.on("message", (topico, payload) => {
    try { ingerir(JSON.parse(payload.toString()), "mqtt", topico); }
    catch { metricas.recebidas++; metricas.invalidas++; marcarPersistencia(); }
  });
  cli.on("close", () => { mqttConectado = false; mqttAssinado = false; });
  cli.on("offline", () => { mqttConectado = false; mqttAssinado = false; });
  cli.on("error", (e) => console.log(`[mqtt] erro: ${e.message}`));
}

servidor.listen(PORT, HOST, () => {
  console.log("=".repeat(60));
  console.log(" Ingestao local — Estacao de Qualidade do Ar");
  console.log("=".repeat(60));
  console.log(`  dashboard .... http://localhost:${PORT}`);
  console.log(`  API .......... http://localhost:${PORT}/api/metricas`);
  console.log(`  broker MQTT .. ${MQTT_ENABLED ? MQTT_URL : "desabilitado"}`);
  console.log(`  persistencia . ${STATE_FILE || "desabilitada"}`);
  console.log("=".repeat(60));
  if (MQTT_ENABLED) conectarMqtt();
});

let encerrando = false;
async function encerrar(sinal) {
  if (encerrando) return;
  encerrando = true;
  console.log(`[sistema] ${sinal}; encerrando com persistencia...`);
  if (timerPersistencia) clearInterval(timerPersistencia);
  clearInterval(timerWebSocket);
  await persistirAgora(true);
  if (clienteMqtt) clienteMqtt.end(true);
  wss.close();
  servidor.close(() => process.exit(0));
  setTimeout(() => process.exit(1), 5000).unref();
}

process.on("SIGTERM", () => { void encerrar("SIGTERM"); });
process.on("SIGINT", () => { void encerrar("SIGINT"); });
