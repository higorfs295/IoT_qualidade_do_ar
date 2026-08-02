import { mkdir, readFile, rename, unlink, writeFile } from "node:fs/promises";
import path from "node:path";

const FORMAT_VERSION = 1;

function inteiro(valor, padrao = 0) {
  return Number.isSafeInteger(valor) && valor >= 0 ? valor : padrao;
}

export function criarSnapshot(dispositivos, idsVistos, metricas, limites = {}) {
  const serieMax = inteiro(limites.serieMax, 500);
  const idsMax = inteiro(limites.idsMax, 200000);
  return {
    format_version: FORMAT_VERSION,
    saved_at: new Date().toISOString(),
    metricas: {
      recebidas: inteiro(metricas.recebidas),
      invalidas: inteiro(metricas.invalidas),
      lacunas: inteiro(metricas.lacunas),
      duplicadas: inteiro(metricas.duplicadas),
      reordenadas: inteiro(metricas.reordenadas),
      reinicios: inteiro(metricas.reinicios),
    },
    dispositivos: [...dispositivos.entries()].map(([deviceId, d]) => ({
      device_id: deviceId,
      site_id: d.site_id,
      ultimo: d.ultimo,
      serie: Array.isArray(d.serie) ? d.serie.slice(-serieMax) : [],
      ultimo_seq: Number.isSafeInteger(d.ultimoSeq) ? d.ultimoSeq : null,
      ultimo_visto_ms: inteiro(d.ultimoVistoMs),
      boot_id: typeof d.bootId === "string" ? d.bootId : null,
    })),
    ids_vistos: [...idsVistos.entries()].slice(-idsMax),
  };
}

export function normalizarSnapshot(raw, limites = {}) {
  if (!raw || raw.format_version !== FORMAT_VERSION) throw new Error("formato de persistencia incompativel");
  const serieMax = inteiro(limites.serieMax, 500);
  const devicesMax = inteiro(limites.devicesMax, 10000);
  const idsMax = inteiro(limites.idsMax, 200000);
  const dispositivos = new Map();
  for (const item of Array.isArray(raw.dispositivos) ? raw.dispositivos.slice(0, devicesMax) : []) {
    if (!item || typeof item.device_id !== "string" || typeof item.site_id !== "string") continue;
    dispositivos.set(item.device_id, {
      site_id: item.site_id,
      ultimo: item.ultimo && typeof item.ultimo === "object" ? item.ultimo : null,
      serie: Array.isArray(item.serie) ? item.serie.slice(-serieMax) : [],
      ultimoSeq: Number.isSafeInteger(item.ultimo_seq) ? item.ultimo_seq : null,
      ultimoVistoMs: inteiro(item.ultimo_visto_ms),
      bootId: typeof item.boot_id === "string" ? item.boot_id : null,
    });
  }
  const idsVistos = new Map();
  for (const par of Array.isArray(raw.ids_vistos) ? raw.ids_vistos.slice(-idsMax) : []) {
    if (Array.isArray(par) && typeof par[0] === "string") idsVistos.set(par[0], inteiro(par[1]));
  }
  const m = raw.metricas || {};
  return {
    savedAt: typeof raw.saved_at === "string" && Number.isFinite(Date.parse(raw.saved_at))
      ? raw.saved_at : null,
    dispositivos,
    idsVistos,
    metricas: {
      recebidas: inteiro(m.recebidas), invalidas: inteiro(m.invalidas),
      lacunas: inteiro(m.lacunas), duplicadas: inteiro(m.duplicadas),
      reordenadas: inteiro(m.reordenadas), reinicios: inteiro(m.reinicios),
    },
  };
}

export async function carregarSnapshot(arquivo, limites = {}) {
  try {
    const raw = JSON.parse(await readFile(arquivo, "utf8"));
    return normalizarSnapshot(raw, limites);
  } catch (erro) {
    if (erro?.code === "ENOENT") return null;
    throw erro;
  }
}

export async function salvarSnapshot(arquivo, snapshot) {
  await mkdir(path.dirname(arquivo), { recursive: true });
  const temporario = `${arquivo}.${process.pid}.tmp`;
  await writeFile(temporario, JSON.stringify(snapshot), { encoding: "utf8", mode: 0o600 });
  try {
    await rename(temporario, arquivo);
  } catch (erro) {
    if (erro?.code !== "EEXIST" && erro?.code !== "EPERM") throw erro;
    await unlink(arquivo).catch((e) => { if (e?.code !== "ENOENT") throw e; });
    await rename(temporario, arquivo);
  }
}
