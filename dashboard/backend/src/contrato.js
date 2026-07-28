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

// Retorna null se valido; senao, uma string com o primeiro erro.
export function validarContrato(msg) {
  if (typeof msg !== "object" || msg === null) return "payload nao e objeto";
  for (const c of CAMPOS_OBRIGATORIOS) if (!(c in msg)) return `campo ausente: ${c}`;
  const versao = msg.schema_version;
  if (!SCHEMA_VERSIONS.includes(versao)) return `schema_version inesperado: ${versao}`;
  if (!Number.isInteger(msg.sequence)) return "sequence nao inteiro";
  const m = msg.measurements;
  if (typeof m !== "object" || m === null) return "measurements nao e objeto";
  for (const med of MEDIDAS_POR_VERSAO[versao]) {
    if (!(med in m)) return `medida ausente: ${med}`;
  }
  const q = msg.quality;
  if (q && typeof q === "object") {
    if (q.gas_status != null && !GAS_STATUS.includes(q.gas_status))
      return `gas_status invalido: ${q.gas_status}`;
    if (q.sensor_status != null && !SENSOR_STATUS.includes(q.sensor_status))
      return `sensor_status invalido: ${q.sensor_status}`;
  }
  return null;
}
