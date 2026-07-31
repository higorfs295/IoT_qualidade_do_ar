# Contrato de telemetria v1.1

## Transporte e tópico

- MQTT 3.1.1, QoS 1 para telemetria.
- Tópico: `qualidade-ar/{site_id}/{device_id}/telemetria`.
- O backend rejeita mensagem cujo tópico não coincida com os IDs do payload.
- Status retido: `qualidade-ar/{site_id}/{device_id}/status` (`online/offline`).
- Payload em UTF-8 JSON, máximo operacional recomendado de 8 KiB no broker.

## Campos

| Campo | Tipo | Regra |
|---|---|---|
| `schema_version` | string | `1.0` ou `1.1`; emissores novos usam `1.1` |
| `message_id` | string | ULID canônico de 26 caracteres |
| `device_id`, `site_id` | string | 1–64 caracteres seguros para tópico |
| `sent_at` | string | RFC 3339 com fuso, preferencialmente UTC `Z` |
| `sequence` | inteiro | não negativo; cresce dentro de um `boot_id` |
| `measurements` | objeto | campos da versão, número finito ou `null` |
| `quality` | objeto | `gas_status` e `sensor_status` |
| `metadata` | objeto | firmware, RSSI, `boot_id`, modo e extensões |

## Medições v1.1

| Campo | Unidade/semântica | Origem planejada |
|---|---|---|
| `co2_ppm` | ppm de CO₂ | SCD41 |
| `voc_index` | índice adimensional 0–500 | SGP40 + algoritmo Sensirion |
| `lpg_ppm` | ppm, somente se calibrado | canal experimental MiCS |
| `gas_raw_v` | V, extensão opcional | tensão diagnóstica do canal analógico |
| `pm1_ugm3` | µg/m³ | PMS7003 |
| `pm25_ugm3` | µg/m³ | PMS7003 |
| `pm10_ugm3` | µg/m³ | PMS7003 |
| `temperature_c` | °C | SHT31 |
| `humidity_pct` | %RH | SHT31 |

`null` significa “não disponível/confiável nesta leitura”; não significa zero.
Se qualquer campo obrigatório estiver nulo, `sensor_status` não pode ser `OK`.

## Estados de qualidade

- `sensor_status=OK`: todos os campos obrigatórios presentes e recentes.
- `DEGRADED`: parte do conjunto indisponível, mas há medições críticas recentes.
- `ERROR`: faltam medições críticas ou expirou o heartbeat.
- `gas_status=SAFE/UNSAFE`: classificação operacional pelas regras versionadas.
- `gas_status=UNKNOWN`: não há evidência suficiente para classificar.

Esses estados são diagnóstico do protótipo, não certificação de segurança.

## Sequência, reinício e idempotência

- `message_id` deduplica reentregas de QoS 1.
- `sequence` detecta lacunas/reordenação.
- `metadata.boot_id` muda a cada inicialização. O consumidor reinicia a janela
  de sequência quando o `boot_id` muda.
- Consumidores não devem substituir o estado atual por mensagem reordenada.

## Evolução

Mudanças aditivas opcionais podem manter a versão. Remover/renomear campo,
alterar unidade/semântica ou tornar opcional algo obrigatório exige nova versão.
Durante migração, consumidores devem aceitar a versão anterior pelo período de
compatibilidade definido e medir o uso de cada versão.

Schema: [`telemetria-v1.1.schema.json`](telemetria-v1.1.schema.json). Exemplo:
[`../poc/payload_exemplo.json`](../poc/payload_exemplo.json).
