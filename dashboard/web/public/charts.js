/* charts.js — sparkline SVG inline sem dependencias.
 * Adaptado do charts.js do IoT-IDEA. Retorna string SVG para innerHTML.
 */
(function (global) {
  "use strict";
  function minmax(a) {
    var mn = Infinity, mx = -Infinity;
    for (var i = 0; i < a.length; i++) { if (a[i] < mn) mn = a[i]; if (a[i] > mx) mx = a[i]; }
    if (!isFinite(mn)) { mn = 0; mx = 1; }
    return { mn: mn, mx: mx, rng: (mx - mn) || 1 };
  }
  function sparkline(arr, opt) {
    opt = opt || {};
    var w = opt.w || 190, h = opt.h || 30, pad = 3, cor = opt.cor || "#38bdf8";
    arr = (arr || []).filter(function (v) { return typeof v === "number"; });
    if (arr.length < 2)
      return '<svg viewBox="0 0 ' + w + ' ' + h + '" style="width:100%;height:' + h + 'px"></svg>';
    var mm = minmax(arr);
    var pts = arr.map(function (v, i) {
      var x = pad + (i / (arr.length - 1)) * (w - 2 * pad);
      var y = h - pad - ((v - mm.mn) / mm.rng) * (h - 2 * pad);
      return x.toFixed(1) + "," + y.toFixed(1);
    }).join(" ");
    var last = arr[arr.length - 1];
    var lx = w - pad, ly = h - pad - ((last - mm.mn) / mm.rng) * (h - 2 * pad);
    return '<svg viewBox="0 0 ' + w + ' ' + h + '" preserveAspectRatio="none" style="width:100%;height:' + h + 'px">' +
      '<polyline points="' + pts + '" fill="none" stroke="' + cor + '" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>' +
      '<circle cx="' + lx.toFixed(1) + '" cy="' + ly.toFixed(1) + '" r="2.4" fill="' + cor + '"/></svg>';
  }
  global.Charts = { sparkline: sparkline };
})(window);
