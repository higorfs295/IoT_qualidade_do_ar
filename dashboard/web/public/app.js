/* app.js — logica do painel de qualidade do ar (legivel para leigos). */
(function () {
  "use strict";
  var CFG = window.APP_CONFIG || {};
  var BASE = CFG.BASE_URL || "";

  // Config das grandezas: rotulo amigavel, emoji, unidade, faixas [atencao, ruim].
  var METRICAS = [
    { k: "co2_ppm",       nome: "Gás carbônico", emoji: "🫁", un: "ppm",  lim: [800, 1000], ref: "bom < 800" },
    { k: "pm25_ugm3",     nome: "Poeira fina (PM2.5)", emoji: "🌫️", un: "µg/m³", lim: [25, 35], ref: "bom < 25" },
    { k: "pm10_ugm3",     nome: "Poeira (PM10)", emoji: "💨", un: "µg/m³", lim: [50, 80], ref: "bom < 50" },
    { k: "pm1_ugm3",      nome: "Partículas finas (PM1)", emoji: "✨", un: "µg/m³", lim: [20, 30], ref: "bom < 20" },
    { k: "voc_index",     nome: "Cheiros/químicos (VOC)", emoji: "🧴", un: "",   lim: [150, 250], ref: "~100 é limpo" },
    { k: "lpg_ppm",       nome: "Indicador experimental de gás", emoji: "🧪", un: "ppm", lim: [50, 100], ref: "exige calibração específica" },
    { k: "temperature_c", nome: "Temperatura", emoji: "🌡️", un: "°C", lim: null, ref: "conforto 20–26" },
    { k: "humidity_pct",  nome: "Umidade", emoji: "💧", un: "%", lim: null, ref: "conforto 40–60" },
  ];

  var series = {};      // k -> [valores]
  var dispositivoAtual = null;
  var metricasTimer = null;
  var reconectarTimer = null;
  var eventoInstalacao = null;

  window.addEventListener("beforeinstallprompt", function (ev) {
    ev.preventDefault();
    eventoInstalacao = ev;
    document.getElementById("installApp").hidden = false;
  });
  window.addEventListener("appinstalled", function () {
    eventoInstalacao = null;
    document.getElementById("installApp").hidden = true;
  });

  function nivel(k, v, lim) {
    if (v == null) return "neutro";
    if (!lim) return "bom";
    if (v >= lim[1]) return "ruim";
    if (v >= lim[0]) return "atencao";
    return "bom";
  }

  var VEREDITOS = {
    bom:     { emoji: "🙂", titulo: "Ar bom", acao: "Ambiente saudável.", cls: "bom" },
    atencao: { emoji: "😐", titulo: "Atenção", acao: "Verifique a ventilação e possíveis fontes de poluição.", cls: "atencao" },
    ruim:    { emoji: "⚠️", titulo: "Leitura elevada", acao: "Confirme com instrumento adequado e siga o plano de segurança do local.", cls: "ruim" },
    neutro:  { emoji: "❓", titulo: "Sem dados", acao: "Aguardando leitura do sensor…", cls: "neutro" },
  };
  var ORD = { neutro: 0, bom: 1, atencao: 2, ruim: 3 };

  function vereditoGeral(msg) {
    if (!msg) return "neutro";
    var q = msg.quality || {};
    if (q.gas_status === "UNSAFE") return "ruim";
    if (q.sensor_status === "ERROR" || q.gas_status === "UNKNOWN") return "neutro";
    var pior = "bom";
    var m = msg.measurements || {};
    METRICAS.forEach(function (def) {
      var n = nivel(def.k, m[def.k], def.lim);
      if (ORD[n] > ORD[pior]) pior = n;
    });
    return pior;
  }

  function fmt(v) {
    if (v == null || typeof v !== "number" || !isFinite(v)) return "—";
    return Number.isInteger(v) ? String(v) : v.toFixed(1);
  }

  function corNivel(n) {
    return { bom: "#16a34a", atencao: "#d97706", ruim: "#dc2626", neutro: "#64748b" }[n];
  }

  function render(msg) {
    // Veredito
    var vg = vereditoGeral(msg);
    var v = VEREDITOS[vg];
    var sec = document.getElementById("veredito");
    sec.className = "veredito " + v.cls;
    document.getElementById("vEmoji").textContent = v.emoji;
    document.getElementById("vTitulo").textContent = v.titulo;
    document.getElementById("vAcao").textContent = v.acao;
    document.getElementById("vQuando").textContent = msg
      ? "atualizado " + new Date(msg.sent_at || Date.now()).toLocaleTimeString("pt-BR") : "";

    // Cartoes
    var m = (msg && msg.measurements) || {};
    var grade = document.getElementById("grade");
    grade.innerHTML = METRICAS.map(function (def) {
      var val = m[def.k];
      if (val != null) {
        series[def.k] = series[def.k] || [];
        series[def.k].push(val);
        if (series[def.k].length > 40) series[def.k].shift();
      }
      var n = nivel(def.k, val, def.lim);
      var cor = corNivel(n);
      return '<div class="cartao">' +
        '<div class="cartao-topo">' + def.emoji + " " + def.nome +
        '<span class="pino ' + n + '"></span></div>' +
        '<div class="cartao-valor" style="color:' + cor + '">' + fmt(val) +
        '<span class="un">' + def.un + "</span></div>" +
        '<div class="cartao-ref">' + def.ref + "</div>" +
        '<div class="cartao-spark">' + Charts.sparkline(series[def.k] || [], { cor: cor }) + "</div>" +
        "</div>";
    }).join("");
  }

  function setConexao(on, txt) {
    var e = document.getElementById("conexao");
    e.className = "conexao " + (on ? "on" : "off");
    e.textContent = txt;
  }

  function atualizarMetricas() {
    fetch(BASE + "/api/metricas").then(function (r) { return r.json(); }).then(function (mt) {
      document.getElementById("metricas").textContent =
        mt.dispositivos + " dispositivo(s) · " + mt.online + " online · " +
        mt.recebidas + " msgs · " + mt.lacunas + " perdas · " + mt.invalidas + " inválidas";
    }).catch(function () {});
  }

  // --- Modo LIVE (backend real) ---------------------------------------------
  function iniciarLive() {
    var proto = location.protocol === "https:" ? "wss" : "ws";
    var ws = new WebSocket(proto + "://" + location.host + (CFG.WS_PATH || "/ws"));
    ws.onopen = function () { setConexao(true, "ao vivo"); };
    ws.onclose = function () {
      setConexao(false, "reconectando…");
      clearTimeout(reconectarTimer);
      reconectarTimer = setTimeout(iniciarLive, 3000);
    };
    ws.onmessage = function (ev) {
      var d;
      try { d = JSON.parse(ev.data); } catch (_) { return; }
      if (d.tipo === "telemetria") {
        if (!dispositivoAtual) dispositivoAtual = d.device_id;
        if (d.device_id === dispositivoAtual) render(d.msg);
        atualizarMetricas();
      }
    };
    // carga inicial
    fetch(BASE + "/api/dispositivos").then(function (r) { return r.json(); }).then(function (lst) {
      var sel = document.getElementById("seletorDispositivo");
      sel.replaceChildren();
      lst.forEach(function (d) {
        var opt = document.createElement("option");
        opt.value = d.device_id;
        opt.textContent = d.device_id;
        sel.appendChild(opt);
      });
      sel.onchange = function () {
        dispositivoAtual = sel.value;
        fetch(BASE + "/api/dispositivos/" + encodeURIComponent(sel.value) + "/atual")
          .then(function (r) { return r.json(); }).then(render).catch(function () {});
      };
      if (lst.length) { dispositivoAtual = lst[0].device_id; render(lst[0].ultimo); }
    }).catch(function () {});
    atualizarMetricas();
    if (!metricasTimer) metricasTimer = setInterval(atualizarMetricas, 5000);
  }

  // --- Modo MOCK (sem backend, para demonstrar) ------------------------------
  function iniciarMock() {
    setConexao(false, "modo demonstração");
    document.getElementById("seletorDispositivo").innerHTML = "<option>esp32-demo</option>";
    var base = { co2_ppm: 700, voc_index: 100, lpg_ppm: 4, pm1_ugm3: 8, pm25_ugm3: 12,
      pm10_ugm3: 18, temperature_c: 24, humidity_pct: 50 };
    var evento = 0;
    function passo(v, d, lo, hi) { return Math.max(lo, Math.min(hi, v + (Math.random() * 2 - 1) * d)); }
    setInterval(function () {
      if (evento <= 0 && Math.random() < 0.1) evento = 5;
      base.co2_ppm = passo(base.co2_ppm, 40, 400, evento > 0 ? 2500 : 1200);
      base.pm25_ugm3 = passo(base.pm25_ugm3, 3, 0, evento > 0 ? 120 : 30);
      base.pm10_ugm3 = passo(base.pm10_ugm3, 4, 0, evento > 0 ? 160 : 45);
      base.pm1_ugm3 = passo(base.pm1_ugm3, 2, 0, 40);
      base.voc_index = passo(base.voc_index, 15, 50, evento > 0 ? 400 : 180);
      base.lpg_ppm = evento > 0 && Math.random() < 0.5 ? passo(base.lpg_ppm, 80, 0, 700) : passo(base.lpg_ppm, 2, 0, 30);
      base.temperature_c = passo(base.temperature_c, 0.4, 18, evento > 0 ? 42 : 30);
      base.humidity_pct = passo(base.humidity_pct, 1, 30, 75);
      if (evento > 0) evento--;
      var m = {}; for (var k in base) m[k] = k === "co2_ppm" || k === "voc_index" || k === "lpg_ppm" ? Math.round(base[k]) : Math.round(base[k] * 10) / 10;
      var unsafe = m.co2_ppm > 1000 || m.voc_index > 250 || m.lpg_ppm > 100 || m.pm25_ugm3 > 35;
      render({ sent_at: new Date().toISOString(), measurements: m,
        quality: { gas_status: unsafe ? "UNSAFE" : "SAFE", sensor_status: "OK" } });
      document.getElementById("metricas").textContent = "modo demonstração (dados simulados no navegador)";
    }, CFG.MOCK_TICK_MS || 2000);
  }

  // --- Escolha do modo -------------------------------------------------------
  function iniciar() {
    render(null);
    var modo = CFG.MODO || "auto";
    if (modo === "mock") return iniciarMock();
    if (modo === "live") return iniciarLive();
    // auto: testa o backend; cai para mock se falhar
    fetch(BASE + "/api/metricas", { signal: AbortSignal.timeout(1500) })
      .then(function (r) { if (!r.ok) throw 0; return iniciarLive(); })
      .catch(function () { iniciarMock(); });
  }
  document.getElementById("installApp").addEventListener("click", function () {
    if (!eventoInstalacao) return;
    eventoInstalacao.prompt();
    eventoInstalacao.userChoice.finally(function () {
      eventoInstalacao = null;
      document.getElementById("installApp").hidden = true;
    });
  });
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", function () {
      navigator.serviceWorker.register("/sw.js").catch(function () {});
    });
  }
  iniciar();
})();
