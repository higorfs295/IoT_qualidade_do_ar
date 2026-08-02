/* Gráficos SVG sem dependências externas; entradas são exclusivamente numéricas. */
(function (global) {
  "use strict";
  function values(input) {
    return (input || []).map(function (item) {
      return typeof item === "number" ? item : item && item.valor;
    }).filter(function (value) { return typeof value === "number" && isFinite(value); });
  }
  function minmax(input) {
    var data = values(input), min = Math.min.apply(null, data), max = Math.max.apply(null, data);
    if (!data.length) return { min: 0, max: 1, range: 1 };
    return { min: min, max: max, range: (max - min) || 1 };
  }
  function points(data, width, height, padding, mm) {
    return data.map(function (value, index) {
      var x = padding + (index / Math.max(1, data.length - 1)) * (width - 2 * padding);
      var y = height - padding - ((value - mm.min) / mm.range) * (height - 2 * padding);
      return x.toFixed(1) + "," + y.toFixed(1);
    }).join(" ");
  }
  function sparkline(input, opt) {
    opt = opt || {};
    var data = values(input), width = opt.w || 190, height = opt.h || 34, pad = 3, color = opt.cor || "#23b6a8";
    if (data.length < 2) return '<svg viewBox="0 0 ' + width + " " + height + '" aria-hidden="true"></svg>';
    return '<svg viewBox="0 0 ' + width + " " + height + '" preserveAspectRatio="none" aria-hidden="true">' +
      '<polyline points="' + points(data, width, height, pad, minmax(data)) + '" fill="none" stroke="' + color + '" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round"/></svg>';
  }
  function line(input, opt) {
    opt = opt || {};
    var data = values(input), width = 900, height = 300, padX = 34, padY = 28, color = opt.cor || "#23b6a8";
    if (data.length < 2) return "";
    var mm = minmax(data), plotPoints = points(data, width, height, padY, mm);
    var areaPoints = padX + "," + (height - padY) + " " + plotPoints + " " + (width - padX) + "," + (height - padY);
    return '<svg viewBox="0 0 900 300" preserveAspectRatio="none" aria-hidden="true">' +
      '<defs><linearGradient id="area" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="' + color + '" stop-opacity=".30"/><stop offset="1" stop-color="' + color + '" stop-opacity="0"/></linearGradient></defs>' +
      '<line x1="28" y1="272" x2="872" y2="272" class="chart-grid"/>' +
      '<line x1="28" y1="150" x2="872" y2="150" class="chart-grid"/>' +
      '<line x1="28" y1="28" x2="872" y2="28" class="chart-grid"/>' +
      '<polygon points="' + areaPoints + '" fill="url(#area)"/>' +
      '<polyline points="' + plotPoints + '" fill="none" stroke="' + color + '" stroke-width="4" vector-effect="non-scaling-stroke" stroke-linejoin="round" stroke-linecap="round"/></svg>';
  }
  global.Charts = { sparkline: sparkline, line: line, values: values };
})(window);
