// =============================================================================
//  contrato.js — Espelho, no backend, do contrato de dados (v1.0 e v1.1)
//  Mantem a MESMA regra de poc/qar_poc/contrato.py.
// =============================================================================

export const SCHEMA_VERSIONS = ["1.0", "1.1"];

export const CAMPOS_OBRIGATORIOS = [
  "schema_version", "message_id", "device_id", "site_id",
  "sent_at", "sequence", "measurements",
];

export const MEDIDAS_POR_VERSAO = {
  "1.0": ["co2_ppm", "tvoc_ppb", "pm1_ugm3", "pm25_ugm3", "pm10_ugm3",
          "temperature_c", "humidity_pct"],
  "1.1": ["co2_ppm", "voc_index", "lpg_ppm", "pm1_ugm3", "pm25_ugm3",
          "pm10_ugm3", "temperature_c", "humidity_pct"],
};

const GAS_STATUS = ["SAFE", "UNSAFE", "UNKNOWN"];
const SENSOR_STATUS = ["OK", "DEGRADED", "ERROR"];

export const LIMITES_MEDIDAS = {
  co2_ppm: [0, 100000], tvoc_ppb: [0, 10000000], voc_index: [0, 500],
  lpg_ppm: [0, 1000000], pm1_ugm3: [0, 10000], pm25_ugm3: [0, 10000],
  pm10_ugm3: [0, 10000], temperature_c: [-50, 100], humidity_pct: [0, 100],
  gas_raw_v: [0, 5.5],
};

const ID_RE = /^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$/;
const ULID_RE = /^[0-9A-HJKMNP-TV-Z]{26}$/;
const RFC3339_TZ_RE = /(Z|[+-]\d{2}:\d{2})$/;

// Retorna null se valido; senao, uma string com o primeiro erro.
export function validarContrato(msg) {
  if (typeof msg !== "object" || msg === null) return "payload nao e objeto";
  for (const c of CAMPOS_OBRIGATORIOS) if (!(c in msg)) return `campo ausente: ${c}`;
  const versao = msg.schema_version;
  if (!SCHEMA_VERSIONS.includes(versao)) return `schema_version inesperado: ${versao}`;
  if (typeof msg.message_id !== "string" || !ULID_RE.test(msg.message_id))
    return "message_id nao e ULID canonico";
  for (const id of ["device_id", "site_id"])
    if (typeof msg[id] !== "string" || !ID_RE.test(msg[id])) return `${id} invalido`;
  if (typeof msg.sent_at !== "string" || !RFC3339_TZ_RE.test(msg.sent_at) ||
      !Number.isFinite(Date.parse(msg.sent_at)))
    return "sent_at invalido (use RFC 3339 com fuso)";
  if (!Number.isInteger(msg.sequence) || msg.sequence < 0)
    return "sequence deve ser inteiro nao negativo";
  const m = msg.measurements;
  if (typeof m !== "object" || m === null) return "measurements nao e objeto";
  for (const med of MEDIDAS_POR_VERSAO[versao]) {
    if (!(med in m)) return `medida ausente: ${med}`;
    const valor = m[med];
    if (valor === null) continue;
    if (typeof valor !== "number" || !Number.isFinite(valor))
      return `medida nao numerica/finita: ${med}`;
    const [min, max] = LIMITES_MEDIDAS[med];
    if (valor < min || valor > max) return `medida fora da faixa plausivel: ${med}`;
  }
  for (const med of ["gas_raw_v"]) {
    if (!(med in m) || m[med] === null) continue;
    const valor = m[med];
    if (typeof valor !== "number" || !Number.isFinite(valor))
      return `medida nao numerica/finita: ${med}`;
    const [min, max] = LIMITES_MEDIDAS[med];
    if (valor < min || valor > max) return `medida fora da faixa plausivel: ${med}`;
  }
  const q = msg.quality;
  if (q != null && (typeof q !== "object" || Array.isArray(q))) return "quality nao e objeto";
  if (q) {
    if (q.gas_status != null && !GAS_STATUS.includes(q.gas_status))
      return `gas_status invalido: ${q.gas_status}`;
    if (q.sensor_status != null && !SENSOR_STATUS.includes(q.sensor_status))
      return `sensor_status invalido: ${q.sensor_status}`;
    if (q.sensor_status === "OK" && MEDIDAS_POR_VERSAO[versao].some((med) => m[med] === null))
      return "sensor_status OK com medida obrigatoria nula";
  }
  if (msg.metadata != null && (typeof msg.metadata !== "object" || Array.isArray(msg.metadata)))
    return "metadata nao e objeto";
  return null;
}

export function validarTopico(topico, msg) {
  const esperado = `qualidade-ar/${msg.site_id}/${msg.device_id}/telemetria`;
  return topico === esperado ? null : `topico divergente: esperado ${esperado}`;
}
