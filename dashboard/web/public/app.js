/* Aplicação web Air Sense: REST + WebSocket + PWA, sem dependências externas. */
(function () {
  "use strict";
  var CFG = window.APP_CONFIG || {};
  var BASE = (CFG.BASE_URL || "").replace(/\/$/, "");
  var METRICAS = [
    { k: "co2_ppm", nome: "Gás carbônico", curto: "CO₂", icone: "CO₂", un: "ppm", lim: [800, 1000], ref: "faixa operacional: bom < 800" },
    { k: "pm25_ugm3", nome: "Poeira fina (PM2.5)", curto: "PM2.5", icone: "•", un: "µg/m³", lim: [25, 35], ref: "faixa operacional: bom < 25" },
    { k: "pm10_ugm3", nome: "Poeira (PM10)", curto: "PM10", icone: "••", un: "µg/m³", lim: [50, 80], ref: "faixa operacional: bom < 50" },
    { k: "pm1_ugm3", nome: "Partículas finas (PM1)", curto: "PM1", icone: "·", un: "µg/m³", lim: [20, 30], ref: "indicador complementar" },
    { k: "voc_index", nome: "Compostos voláteis", curto: "VOC", icone: "V", un: "índice", lim: [150, 250], ref: "referência limpa próxima de 100" },
    { k: "lpg_ppm", nome: "Indicador experimental de gás", curto: "LPG", icone: "G", un: "ppm", lim: [50, 100], ref: "somente após calibração específica" },
    { k: "temperature_c", nome: "Temperatura", curto: "Temperatura", icone: "°", un: "°C", lim: null, ref: "conforto típico: 20–26 °C" },
    { k: "humidity_pct", nome: "Umidade", curto: "Umidade", icone: "%", un: "%", lim: null, ref: "conforto típico: 40–60%" }
  ];
  var VEREDITOS = {
    bom: { emoji: "✓", titulo: "Ar em boa condição", acao: "As leituras estão dentro das faixas operacionais do protótipo." },
    atencao: { emoji: "!", titulo: "Atenção ao ambiente", acao: "Ventile o local e confira possíveis fontes de poluição." },
    ruim: { emoji: "!!", titulo: "Leitura elevada", acao: "Confirme com instrumento adequado e siga o plano de segurança do local." },
    neutro: { emoji: "?", titulo: "Sem diagnóstico", acao: "Aguardando dados válidos ou recuperação dos sensores." }
  };
  var ORDEM = { neutro: 0, bom: 1, atencao: 2, ruim: 3 };
  var CORES = { bom: "#16865b", atencao: "#b86a09", ruim: "#c63f49", neutro: "#657983" };

  var series = {};
  var devices = [];
  var currentId = null;
  var currentMessage = null;
  var health = null;
  var metrics = null;
  var alerts = carregarAlertas();
  var ws = null;
  var demoTimer = null;
  var pollTimer = null;
  var reconnectTimer = null;
  var installEvent = null;
  var demo = false;
  var reconnectEnabled = false;

  function el(id) { return document.getElementById(id); }
  function metric(field) { return METRICAS.find(function (item) { return item.k === field; }) || METRICAS[0]; }
  function apiUrl(path) { return (BASE || location.origin) + path; }
  function wsUrl() {
    var root = new URL(BASE || location.origin, location.origin);
    root.protocol = root.protocol === "https:" ? "wss:" : "ws:";
    root.pathname = root.pathname.replace(/\/$/, "") + (CFG.WS_PATH || "/ws");
    root.search = ""; root.hash = "";
    return root.toString();
  }
  function fetchJson(path) {
    var controller = typeof AbortController !== "undefined" ? new AbortController() : null;
    var timer = controller ? setTimeout(function () { controller.abort(); }, 5000) : null;
    return fetch(apiUrl(path), { headers: { Accept: "application/json" }, signal: controller && controller.signal })
      .then(function (response) {
        if (!response.ok) throw new Error("HTTP " + response.status);
        return response.json();
      }).finally(function () { if (timer) clearTimeout(timer); });
  }
  function fmt(value, digits) {
    if (value == null || typeof value !== "number" || !isFinite(value)) return "—";
    return value.toLocaleString("pt-BR", { maximumFractionDigits: digits == null ? 1 : digits });
  }
  function fmtDate(value) {
    var date = new Date(value || Date.now());
    return isNaN(date.getTime()) ? "—" : date.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
  }
  function nivel(def, value) {
    if (value == null || typeof value !== "number" || !isFinite(value)) return "neutro";
    if (!def.lim) return "bom";
    if (value >= def.lim[1]) return "ruim";
    if (value >= def.lim[0]) return "atencao";
    return "bom";
  }
  function veredito(msg) {
    if (!msg) return "neutro";
    var quality = msg.quality || {};
    if (quality.gas_status === "UNSAFE") return "ruim";
    if (quality.sensor_status === "ERROR" || quality.gas_status === "UNKNOWN") return "neutro";
    var worst = "bom", values = msg.measurements || {};
    METRICAS.forEach(function (def) {
      var current = nivel(def, values[def.k]);
      if (ORDEM[current] > ORDEM[worst]) worst = current;
    });
    return worst;
  }
  function setConnection(on, text) {
    el("conexao").className = "conexao " + (on ? "on" : "off");
    el("conexao").textContent = text;
  }

  function renderCurrent(msg, register) {
    currentMessage = msg || null;
    var verdict = veredito(msg), copy = VEREDITOS[verdict];
    el("veredito").className = "veredito " + verdict;
    el("vEmoji").textContent = copy.emoji;
    el("vTitulo").textContent = copy.titulo;
    el("vAcao").textContent = copy.acao;
    el("vQuando").textContent = msg ? "Atualizado em " + fmtDate(msg.sent_at) : "";
    var values = msg && msg.measurements || {};
    var grid = el("grade"); grid.replaceChildren();
    METRICAS.forEach(function (def) {
      var value = values[def.k], status = nivel(def, value);
      if (register && value != null && typeof value === "number") {
        series[def.k] = series[def.k] || [];
        series[def.k].push(value);
        if (series[def.k].length > 1000) series[def.k].splice(0, series[def.k].length - 1000);
      }
      var card = document.createElement("article"); card.className = "cartao";
      var top = document.createElement("div"); top.className = "cartao-topo";
      var icon = document.createElement("span"); icon.className = "cartao-icone"; icon.textContent = def.icone;
      var label = document.createElement("span"); label.textContent = def.nome;
      var dot = document.createElement("span"); dot.className = "pino " + status;
      top.append(icon, label, dot);
      var number = document.createElement("div"); number.className = "cartao-valor"; number.style.color = CORES[status];
      number.append(document.createTextNode(fmt(value)));
      var unit = document.createElement("span"); unit.className = "un"; unit.textContent = def.un; number.appendChild(unit);
      var reference = document.createElement("div"); reference.className = "cartao-ref"; reference.textContent = def.ref;
      var spark = document.createElement("div"); spark.className = "cartao-spark";
      spark.innerHTML = Charts.sparkline(series[def.k] || [], { cor: CORES[status] });
      card.append(top, number, reference, spark); grid.appendChild(card);
    });
    renderDiagnostic();
    if (register && msg) considerAlert(msg, verdict);
  }

  function updateSelector() {
    var select = el("seletorDispositivo"), previous = currentId;
    select.replaceChildren();
    if (!devices.length) {
      var empty = document.createElement("option"); empty.textContent = "sem dispositivos"; empty.value = ""; select.appendChild(empty); currentId = null; return;
    }
    devices.forEach(function (device) {
      var option = document.createElement("option"); option.value = device.device_id;
      option.textContent = device.device_id + (device.online ? "" : " · offline"); select.appendChild(option);
    });
    currentId = devices.some(function (item) { return item.device_id === previous; }) ? previous : devices[0].device_id;
    select.value = currentId;
  }
  function registerTelemetry(msg) {
    if (!msg || !msg.device_id) return;
    var index = devices.findIndex(function (device) { return device.device_id === msg.device_id; });
    var summary = { device_id: msg.device_id, site_id: msg.site_id, online: true, ultimo: msg };
    if (index < 0) devices.push(summary); else devices[index] = summary;
    if (!currentId) currentId = msg.device_id;
    updateSelector();
    if (msg.device_id === currentId) renderCurrent(msg, true);
  }

  function renderMetrics() {
    if (demo) { el("metricas").textContent = "Modo demonstração · dados simulados no navegador"; return; }
    if (!metrics) { el("metricas").textContent = "Aguardando métricas do backend…"; return; }
    el("metricas").textContent = (metrics.dispositivos || 0) + " dispositivo(s) · " + (metrics.online || 0) + " online · " +
      (metrics.recebidas || 0) + " mensagens · " + (metrics.lacunas || 0) + " perdas · " + (metrics.invalidas || 0) + " inválidas";
  }

  function setView(name) {
    var valid = ["agora", "historico", "alertas", "dispositivo"].indexOf(name) >= 0 ? name : "agora";
    document.querySelectorAll("[data-view-panel]").forEach(function (panel) {
      var active = panel.dataset.viewPanel === valid; panel.hidden = !active; panel.classList.toggle("ativa", active);
    });
    document.querySelectorAll("[data-view]").forEach(function (button) { button.classList.toggle("ativo", button.dataset.view === valid); });
    if (location.hash !== "#" + valid) history.replaceState(null, "", "#" + valid);
    if (valid === "historico") loadHistory();
    if (valid === "alertas") renderAlerts();
    if (valid === "dispositivo") renderDiagnostic();
  }

  function loadHistory() {
    var field = el("campoHistorico").value || "co2_ppm", limit = Number(el("pontosHistorico").value || 200);
    if (demo) return renderHistory(field, (series[field] || []).slice(-limit));
    if (!currentId) return renderHistory(field, []);
    fetchJson("/api/dispositivos/" + encodeURIComponent(currentId) + "/serie?campo=" + encodeURIComponent(field) + "&n=" + limit)
      .then(function (data) { renderHistory(field, data.serie || []); })
      .catch(function () { renderHistory(field, []); });
  }

  function loadSparklines() {
    if (demo || !currentId) return Promise.resolve();
    var id = encodeURIComponent(currentId);
    return Promise.all(METRICAS.map(function (def) {
      return fetchJson("/api/dispositivos/" + id + "/serie?campo=" + encodeURIComponent(def.k) + "&n=40")
        .then(function (data) { series[def.k] = Charts.values(data.serie || []); })
        .catch(function () { series[def.k] = series[def.k] || []; });
    })).then(function () { renderCurrent(currentMessage, false); });
  }
  function renderHistory(field, input) {
    var def = metric(field), values = Charts.values(input);
    el("histNome").textContent = def.nome;
    el("histAtual").textContent = values.length ? fmt(values[values.length - 1]) + " " + def.un : "—";
    el("histMin").textContent = values.length ? fmt(Math.min.apply(null, values)) : "—";
    el("histMax").textContent = values.length ? fmt(Math.max.apply(null, values)) : "—";
    el("histMedia").textContent = values.length ? fmt(values.reduce(function (sum, value) { return sum + value; }, 0) / values.length) : "—";
    el("graficoHistorico").innerHTML = Charts.line(values, { cor: CORES[nivel(def, values[values.length - 1])] });
    el("histVazio").hidden = values.length >= 2;
  }

  function carregarAlertas() {
    try {
      var data = JSON.parse(localStorage.getItem("air-sense-alerts") || "[]");
      return Array.isArray(data) ? data.slice(0, 50) : [];
    } catch (_) { return []; }
  }
  function saveAlerts() {
    try { localStorage.setItem("air-sense-alerts", JSON.stringify(alerts.slice(0, 50))); } catch (_) { /* armazenamento opcional */ }
  }
  function considerAlert(msg, verdict) {
    if (verdict === "bom" || verdict === "neutro") return;
    var latest = alerts.find(function (item) { return item.device_id === msg.device_id && item.level === verdict; });
    if (latest && Date.now() - new Date(latest.timestamp).getTime() < 10 * 60 * 1000) return;
    alerts.unshift({ id: msg.message_id || (msg.device_id + "-" + Date.now()), device_id: msg.device_id, level: verdict,
      title: VEREDITOS[verdict].titulo, description: VEREDITOS[verdict].acao, timestamp: msg.sent_at || new Date().toISOString(), acknowledged: false });
    alerts = alerts.slice(0, 50); saveAlerts(); renderAlerts();
  }
  function renderAlerts() {
    var list = el("listaAlertas"); list.replaceChildren();
    alerts.forEach(function (item) {
      var row = document.createElement("article"); row.className = "alerta-item " + (item.level === "ruim" ? "ruim" : "") + (item.acknowledged ? " reconhecido" : "");
      var icon = document.createElement("div"); icon.className = "alerta-icone"; icon.textContent = item.level === "ruim" ? "!!" : "!";
      var content = document.createElement("div"); content.className = "alerta-conteudo";
      var title = document.createElement("strong"); title.textContent = item.title;
      var description = document.createElement("span"); description.textContent = item.description; content.append(title, description);
      var meta = document.createElement("div"); meta.className = "alerta-meta"; meta.append(document.createTextNode(item.device_id + " · " + fmtDate(item.timestamp)));
      if (!item.acknowledged) { var acknowledge = document.createElement("button"); acknowledge.type = "button"; acknowledge.textContent = "Reconhecer";
        acknowledge.addEventListener("click", function () { item.acknowledged = true; saveAlerts(); renderAlerts(); }); meta.appendChild(document.createElement("br")); meta.appendChild(acknowledge); }
      row.append(icon, content, meta); list.appendChild(row);
    });
    el("alertasVazio").hidden = alerts.length > 0;
    var pending = alerts.filter(function (item) { return !item.acknowledged; }).length;
    el("alertBadge").hidden = pending === 0; el("alertBadge").textContent = String(pending);
  }

  function diagCard(title, rows) {
    var card = document.createElement("article"); card.className = "diag-card";
    var heading = document.createElement("h2"); heading.textContent = title; card.appendChild(heading);
    rows.forEach(function (row) { var line = document.createElement("div"); line.className = "diag-linha";
      var label = document.createElement("span"); label.textContent = row[0]; var value = document.createElement("strong"); value.textContent = row[1] == null || row[1] === "" ? "—" : String(row[1]); line.append(label, value); card.appendChild(line); });
    return card;
  }
  function renderDiagnostic() {
    var msg = currentMessage || {}, meta = msg.metadata || {}, quality = msg.quality || {}, selected = devices.find(function (item) { return item.device_id === currentId; });
    var root = el("diagnostico"); root.replaceChildren();
    root.append(
      diagCard("Identidade", [["Dispositivo", currentId], ["Site", msg.site_id], ["Contrato", msg.schema_version], ["Sequência", msg.sequence], ["Última amostra", msg.sent_at ? fmtDate(msg.sent_at) : null]]),
      diagCard("Firmware e placa", [["Firmware", meta.firmware_version], ["Placa", meta.board_model], ["Revisão", meta.hardware_revision], ["Modo de sensores", meta.sensor_mode], ["Boot ID", meta.boot_id]]),
      diagCard("Saúde do dispositivo", [["Online", selected ? (selected.online ? "sim" : "não") : null], ["Sensores", quality.sensor_status], ["Gás", quality.gas_status], ["RSSI", meta.rssi_dbm != null ? meta.rssi_dbm + " dBm" : null], ["Uptime", meta.uptime_s != null ? meta.uptime_s + " s" : null]]),
      diagCard("Memória ESP32", [["Heap livre", meta.free_heap_bytes != null ? meta.free_heap_bytes + " B" : null], ["Menor heap", meta.min_free_heap_bytes != null ? meta.min_free_heap_bytes + " B" : null], ["Maior bloco", meta.max_alloc_heap_bytes != null ? meta.max_alloc_heap_bytes + " B" : null], ["Fila offline", meta.offline_queue_depth], ["Descartadas", meta.offline_dropped_total]]),
      diagCard("Backend", [["Pronto", health ? (health.ready ? "sim" : "não") : null], ["MQTT", health ? (health.mqtt_connected ? "conectado" : "desconectado") : null], ["Assinatura", health && health.mqtt_enabled ? (health.mqtt_subscribed ? "ativa" : "inativa") : "desabilitada"], ["Persistência", health ? (health.persistence_enabled ? "ativa" : "desabilitada") : null], ["Dispositivos", health && health.devices]]),
      diagCard("Integridade", [["Recebidas", metrics && metrics.recebidas], ["Inválidas", metrics && metrics.invalidas], ["Duplicadas", metrics && metrics.duplicadas], ["Lacunas", metrics && metrics.lacunas], ["Reinícios", metrics && metrics.reinicios]])
    );
  }

  function populateHistoryFields() {
    var select = el("campoHistorico"); select.replaceChildren();
    METRICAS.filter(function (def) { return def.k !== "lpg_ppm"; }).forEach(function (def) {
      var option = document.createElement("option"); option.value = def.k; option.textContent = def.nome; select.appendChild(option);
    });
  }

  function closeLive() {
    reconnectEnabled = false;
    clearTimeout(reconnectTimer); clearInterval(pollTimer); pollTimer = null;
    if (ws) { ws.onclose = null; ws.close(); ws = null; }
  }
  function connectSocket() {
    if (!reconnectEnabled || demo) return;
    ws = new WebSocket(wsUrl());
    ws.onopen = function () { setConnection(true, "ao vivo"); };
    ws.onmessage = function (event) { try { var data = JSON.parse(event.data); if (data.tipo === "telemetria") registerTelemetry(data.msg); } catch (_) { /* quadro inválido */ } };
    ws.onerror = function () { ws.close(); };
    ws.onclose = function () { setConnection(false, "reconectando…"); if (reconnectEnabled) reconnectTimer = setTimeout(connectSocket, 3000); };
  }
  function refreshLive() {
    return Promise.all([fetchJson("/api/health"), fetchJson("/api/dispositivos"), fetchJson("/api/metricas")]).then(function (results) {
      health = results[0]; devices = results[1]; metrics = results[2]; updateSelector();
      var selected = devices.find(function (item) { return item.device_id === currentId; });
      renderCurrent(selected && selected.ultimo || null, false); renderMetrics(); return results;
    });
  }
  function startLive() {
    closeLive(); clearInterval(demoTimer); demoTimer = null; demo = false; el("modoBanner").hidden = true;
    setConnection(false, "conectando…");
    return refreshLive().then(function () {
      reconnectEnabled = true; connectSocket(); pollTimer = setInterval(function () { refreshLive().catch(function () { setConnection(false, "backend indisponível"); }); }, 10000);
      if (!health.ready) setConnection(false, "MQTT não pronto");
      loadSparklines();
      var active = document.querySelector("[data-view-panel]:not([hidden])");
      if (active && active.dataset.viewPanel === "historico") loadHistory();
    });
  }

  function seedDemo(base) {
    METRICAS.forEach(function (def) { series[def.k] = []; });
    for (var index = 60; index > 0; index--) {
      var wave = Math.sin(index / 7);
      series.co2_ppm.push(base.co2_ppm + wave * 90);
      series.pm25_ugm3.push(base.pm25_ugm3 + wave * 4);
      series.pm10_ugm3.push(base.pm10_ugm3 + wave * 6);
      series.pm1_ugm3.push(base.pm1_ugm3 + wave * 2);
      series.voc_index.push(base.voc_index + wave * 20);
      series.lpg_ppm.push(base.lpg_ppm);
      series.temperature_c.push(base.temperature_c + wave);
      series.humidity_pct.push(base.humidity_pct - wave * 4);
    }
  }
  function startDemo() {
    closeLive(); clearInterval(demoTimer); demo = true; el("modoBanner").hidden = false; setConnection(false, "demonstração");
    var base = { co2_ppm: 690, pm25_ugm3: 12, pm10_ugm3: 19, pm1_ugm3: 7, voc_index: 98, lpg_ppm: 4, temperature_c: 24, humidity_pct: 51 };
    seedDemo(base); devices = [{ device_id: "esp32-demo", site_id: "campus-demo", online: true, ultimo: null }]; currentId = "esp32-demo";
    health = { ready: true, mqtt_enabled: false, mqtt_connected: false, mqtt_subscribed: false, persistence_enabled: false, devices: 1 };
    metrics = { dispositivos: 1, online: 1, recebidas: 0, lacunas: 0, invalidas: 0, duplicadas: 0, reinicios: 0 };
    updateSelector(); var sequence = 1;
    function tick() {
      function step(value, delta, min, max) { return Math.max(min, Math.min(max, value + (Math.random() * 2 - 1) * delta)); }
      base.co2_ppm = step(base.co2_ppm, 35, 430, 1250); base.pm25_ugm3 = step(base.pm25_ugm3, 2, 2, 42); base.pm10_ugm3 = step(base.pm10_ugm3, 3, 4, 70);
      base.pm1_ugm3 = step(base.pm1_ugm3, 1.2, 1, 25); base.voc_index = step(base.voc_index, 10, 55, 280); base.temperature_c = step(base.temperature_c, .3, 19, 30); base.humidity_pct = step(base.humidity_pct, 1, 35, 70);
      var measurements = {}; Object.keys(base).forEach(function (key) { measurements[key] = Math.round(base[key] * 10) / 10; });
      var unsafe = measurements.co2_ppm >= 1000 || measurements.pm25_ugm3 >= 35 || measurements.voc_index >= 250;
      var msg = { schema_version: "1.1", message_id: "DEMO-" + Date.now(), device_id: "esp32-demo", site_id: "campus-demo", sent_at: new Date().toISOString(), sequence: sequence++, measurements: measurements,
        quality: { gas_status: unsafe ? "UNSAFE" : "SAFE", sensor_status: "OK" }, metadata: { firmware_version: "1.3.0-demo", board_model: "ESP-WROOM-32 DevKit 30P USB-C", hardware_revision: "PROTO-REV-A", sensor_mode: "DEMO", rssi_dbm: -58, free_heap_bytes: 172000, min_free_heap_bytes: 151000, max_alloc_heap_bytes: 108000, uptime_s: sequence * 2, offline_queue_depth: 0, offline_dropped_total: 0 } };
      devices[0].ultimo = msg; metrics.recebidas++; registerTelemetry(msg); renderMetrics();
    }
    tick(); demoTimer = setInterval(tick, CFG.MOCK_TICK_MS || 2000);
  }

  function bind() {
    document.querySelectorAll("[data-view]").forEach(function (button) { button.addEventListener("click", function () { setView(button.dataset.view); }); });
    el("seletorDispositivo").addEventListener("change", function () { currentId = el("seletorDispositivo").value || null; series = {}; var selected = devices.find(function (item) { return item.device_id === currentId; }); renderCurrent(selected && selected.ultimo || null, false); loadSparklines(); loadHistory(); });
    el("campoHistorico").addEventListener("change", loadHistory); el("pontosHistorico").addEventListener("change", loadHistory);
    el("atualizarAgora").addEventListener("click", function () { if (demo) return; refreshLive().catch(function () { setConnection(false, "backend indisponível"); }); });
    el("tentarLive").addEventListener("click", function () { startLive().catch(function () { startDemo(); }); });
    el("reconhecerTodos").addEventListener("click", function () { alerts.forEach(function (item) { item.acknowledged = true; }); saveAlerts(); renderAlerts(); });
    el("installApp").addEventListener("click", function () { if (!installEvent) return; installEvent.prompt(); installEvent.userChoice.finally(function () { installEvent = null; el("installApp").hidden = true; }); });
    window.addEventListener("beforeinstallprompt", function (event) { event.preventDefault(); installEvent = event; el("installApp").hidden = false; });
    window.addEventListener("appinstalled", function () { installEvent = null; el("installApp").hidden = true; });
  }

  function start() {
    populateHistoryFields(); bind(); renderCurrent(null, false); renderAlerts(); setView(location.hash.replace("#", "") || "agora");
    var mode = CFG.MODO || "auto";
    if (mode === "mock") startDemo();
    else startLive().catch(function () { if (mode === "live") { setConnection(false, "backend indisponível"); renderMetrics(); } else startDemo(); });
    if ("serviceWorker" in navigator) window.addEventListener("load", function () { navigator.serviceWorker.register("/sw.js").catch(function () {}); });
  }
  start();
})();
