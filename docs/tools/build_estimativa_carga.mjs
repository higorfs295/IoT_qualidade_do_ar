import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = path.resolve(import.meta.dirname, "../..");
const previewDir = path.join(root, "tmp", "spreadsheet", "previews");
await fs.mkdir(previewDir, { recursive: true });

const wb = Workbook.create();
const prem = wb.worksheets.add("Premissas");
const cen = wb.worksheets.add("Cenarios");
const cap = wb.worksheets.add("Capacidade");

const navy = "#12304A";
const teal = "#0F766E";
const pale = "#E8F3F5";
const input = "#FFF4CC";
const line = "#CBD5E1";
const text = "#17212B";
const muted = "#52606D";

for (const sheet of [prem, cen, cap]) sheet.showGridLines = false;

prem.mergeCells("A1:D1");
prem.getRange("A1").values = [["Estimativa de carga - premissas editáveis"]];
prem.getRange("A1:D1").format = { fill: navy, font: { bold: true, color: "#FFFFFF", size: 16 },
  horizontalAlignment: "center", verticalAlignment: "center" };
prem.getRange("A1:D1").format.rowHeight = 30;
prem.getRange("A3:D3").values = [["Parâmetro", "Valor", "Unidade", "Observação"]];
prem.getRange("A4:D8").values = [
  ["Intervalo de publicação", 60, "s", "Uma mensagem consolidada por dispositivo"],
  ["Payload médio", 470, "bytes", "Premissa; medir no tráfego real"],
  ["Fator de pico", 2, "x média", "Margem para rajadas e reconexões"],
  ["Dias por mês", 30, "dias", "Usado apenas na projeção mensal"],
  ["Retenção operacional", 30, "dias", "Não inclui agregados, backup ou data lake"],
];
prem.getRange("A3:D3").format = { fill: teal, font: { bold: true, color: "#FFFFFF" } };
prem.getRange("B4:B8").format = { fill: input, font: { bold: true, color: text },
  horizontalAlignment: "right" };
prem.getRange("A3:D8").format.borders = { preset: "insideHorizontal", style: "thin", color: line };
prem.getRange("A10:D12").merge(true);
prem.getRange("A10").values = [["Escopo"]];
prem.getRange("A11").values = [["GB decimal; não inclui TCP/TLS/MQTT, índices, WAL, réplicas, compressão, backups nem consultas."]];
prem.getRange("A12").values = [["Entradas amarelas são editáveis. Fórmulas permanecem nas demais abas para auditoria."]];
prem.getRange("A10:D10").format = { fill: pale, font: { bold: true, color: navy } };
prem.getRange("A11:D12").format = { font: { color: muted }, wrapText: true };
prem.getRange("A:D").format.font = { name: "Aptos", color: text, size: 10 };
prem.getRange("A1:D1").format.font = { name: "Aptos Display", bold: true, color: "#FFFFFF", size: 16 };
prem.getRange("A3:A8").format.columnWidth = 27;
prem.getRange("B3:B8").format.columnWidth = 13;
prem.getRange("C3:C8").format.columnWidth = 14;
prem.getRange("D3:D12").format.columnWidth = 52;
prem.getRange("A11:D12").format.rowHeight = 34;
prem.freezePanes.freezeRows(3);

cen.mergeCells("A1:I1");
cen.getRange("A1").values = [["Cenários de volumetria"]];
cen.getRange("A1:I1").format = { fill: navy, font: { name: "Aptos Display", bold: true, color: "#FFFFFF", size: 16 },
  horizontalAlignment: "center", verticalAlignment: "center" };
cen.getRange("A1:I1").format.rowHeight = 30;
cen.getRange("A3:I3").values = [["Dispositivos", "Intervalo (s)", "Payload (B)", "Média (msg/s)",
  "Pico (msg/s)", "Mensagens/dia", "GB/dia", "GB/mês", "Mbit/s payload"]];
cen.getRange("A4:A7").values = [[5000], [10000], [50000], [100000]];
for (let row = 4; row <= 7; row++) {
  cen.getRange(`B${row}:I${row}`).formulas = [[
    "='Premissas'!$B$4",
    "='Premissas'!$B$5",
    `=A${row}/B${row}`,
    `=D${row}*'Premissas'!$B$6`,
    `=A${row}*86400/B${row}`,
    `=F${row}*C${row}/1000000000`,
    `=G${row}*'Premissas'!$B$7`,
    `=D${row}*C${row}*8/1000000`,
  ]];
}
cen.getRange("A3:I3").format = { fill: teal, font: { bold: true, color: "#FFFFFF" }, wrapText: true,
  horizontalAlignment: "center" };
cen.getRange("A4:C7").format.fill = input;
cen.getRange("D4:I7").format.fill = pale;
cen.getRange("A3:I7").format.borders = { preset: "insideHorizontal", style: "thin", color: line };
cen.getRange("A4:C7").format.numberFormat = "#,##0";
cen.getRange("D4:E7").format.numberFormat = "#,##0.00";
cen.getRange("F4:F7").format.numberFormat = "#,##0";
cen.getRange("G4:I7").format.numberFormat = "#,##0.000";
cen.getRange("A3:I7").format.font = { name: "Aptos", color: text, size: 10 };
cen.getRange("A3:I3").format.font = { name: "Aptos", bold: true, color: "#FFFFFF", size: 10 };
for (const col of ["A", "B", "C", "D", "E", "F", "G", "H", "I"]) cen.getRange(`${col}3:${col}7`).format.columnWidth = 15;
cen.getRange("F3:F7").format.columnWidth = 18;
cen.getRange("A3:I3").format.rowHeight = 34;
cen.freezePanes.freezeRows(3);

cen.getRange("K3:M7").formulas = [
  ["=A3", "=D3", "=E3"],
  ["=A4", "=D4", "=E4"],
  ["=A5", "=D5", "=E5"],
  ["=A6", "=D6", "=E6"],
  ["=A7", "=D7", "=E7"],
];
cen.getRange("K3:M7").format = { fill: "#F8FAFC", font: { color: muted, size: 9 } };
cen.getRange("K3:M3").format.font = { bold: true, color: navy, size: 9 };
const chart = cen.charts.add("bar", { title: "Taxa média e pico por cenário (msg/s)", hasLegend: true });
const avg = chart.series.add("Média");
avg.categoryFormula = "'Cenarios'!$K$4:$K$7";
avg.formula = "'Cenarios'!$L$4:$L$7";
avg.fill = "#0F766E";
const peak = chart.series.add("Pico 2x");
peak.categoryFormula = "'Cenarios'!$K$4:$K$7";
peak.formula = "'Cenarios'!$M$4:$M$7";
peak.fill = "#D97706";
chart.setPosition("K9", "S25");
chart.titleTextStyle.fontSize = 12;
chart.yAxis = { numberFormatCode: "#,##0" };

cap.mergeCells("A1:D1");
cap.getRange("A1").values = [["Calculadora de capacidade"]];
cap.getRange("A1:D1").format = { fill: navy, font: { name: "Aptos Display", bold: true, color: "#FFFFFF", size: 16 },
  horizontalAlignment: "center", verticalAlignment: "center" };
cap.getRange("A1:D1").format.rowHeight = 30;
cap.getRange("A3:D3").values = [["Entrada", "Valor", "Unidade", "Uso"]];
cap.getRange("A4:D7").values = [
  ["Dispositivos", 100000, "un", "Cenário a avaliar"],
  ["Capacidade medida do consumidor", 5000, "msg/s", "Resultado de benchmark, não estimativa"],
  ["Reserva operacional", 0.30, "%", "Margem acima do pico"],
  ["Retenção", 30, "dias", "Histórico bruto"],
];
cap.getRange("A9:D9").values = [["Saída", "Resultado", "Unidade", "Interpretação"]];
cap.getRange("A10:D14").values = [
  ["Taxa média", null, "msg/s", "Dispositivos / intervalo"],
  ["Pico planejado", null, "msg/s", "Média x fator de pico"],
  ["Capacidade necessária", null, "msg/s", "Pico com reserva"],
  ["Headroom do consumidor", null, "%", "Positivo = capacidade acima da necessidade"],
  ["Armazenamento bruto", null, "GB", "Payload sem overhead pelo período"],
];
cap.getRange("B10:B14").formulas = [
  ["=B4/'Premissas'!$B$4"],
  ["=B10*'Premissas'!$B$6"],
  ["=B11*(1+B6)"],
  ["=B5/B12-1"],
  ["=B4*86400/'Premissas'!$B$4*'Premissas'!$B$5/1000000000*B7"],
];
cap.getRange("A3:D3").format = { fill: teal, font: { bold: true, color: "#FFFFFF" } };
cap.getRange("A9:D9").format = { fill: teal, font: { bold: true, color: "#FFFFFF" } };
cap.getRange("B4:B7").format = { fill: input, font: { bold: true, color: text } };
cap.getRange("B10:B14").format = { fill: pale, font: { bold: true, color: navy } };
cap.getRange("A3:D14").format.borders = { preset: "insideHorizontal", style: "thin", color: line };
cap.getRange("A3:D14").format.font = { name: "Aptos", color: text, size: 10 };
cap.getRange("A3:D3").format.font = cap.getRange("A9:D9").format.font = { name: "Aptos", bold: true, color: "#FFFFFF", size: 10 };
cap.getRange("A3:A14").format.columnWidth = 34;
cap.getRange("B3:B14").format.columnWidth = 18;
cap.getRange("C3:C14").format.columnWidth = 14;
cap.getRange("D3:D14").format.columnWidth = 48;
cap.getRange("B4:B5").format.numberFormat = "#,##0";
cap.getRange("B6:B6").format.numberFormat = "0%";
cap.getRange("B7:B7").format.numberFormat = "#,##0";
cap.getRange("B10:B12").format.numberFormat = "#,##0.00";
cap.getRange("B13:B13").format.numberFormat = "0.0%";
cap.getRange("B14:B14").format.numberFormat = "#,##0.00";
cap.freezePanes.freezeRows(3);

console.log((await wb.inspect({ kind: "sheet,table", range: "Cenarios!A3:I7", maxChars: 2500, tableMaxRows: 8, tableMaxCols: 12 })).ndjson);
console.log((await wb.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A", options: { useRegex: true, maxResults: 100 }, summary: "formula errors" })).ndjson);

for (const sheetName of ["Premissas", "Cenarios", "Capacidade"]) {
  const preview = await wb.render({ sheetName, autoCrop: "all", scale: 1.5, format: "png" });
  await fs.writeFile(path.join(previewDir, `${sheetName}.png`), new Uint8Array(await preview.arrayBuffer()));
}

const out = await SpreadsheetFile.exportXlsx(wb);
await out.save(path.join(root, "docs", "estimativa_carga.xlsx"));
