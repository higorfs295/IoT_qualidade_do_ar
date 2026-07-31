# Firmware ESP32

Firmware com HAL/Strategy para alternar entre HIL serial e sensores físicos sem
alterar a lógica de telemetria.

## Builds

```bash
pio run -e esp32-hil
pio run -e esp32-fisico
```

Ambos foram compilados na auditoria de 31/07/2026:

| Ambiente | RAM | Flash |
|---|---:|---:|
| `esp32-hil` | 46.984 B (14,3%) | 785.569 B (59,9%) |
| `esp32-fisico` | 47.076 B (14,4%) | 816.437 B (62,3%) |

Compilado não significa validado eletricamente. O ambiente físico requer o
bring-up de [`../docs/ROADMAP_FIRMWARE.md`](../docs/ROADMAP_FIRMWARE.md).

## Configuração segura

```powershell
Copy-Item include\secrets.example.h include\secrets.h
```

Edite `secrets.h`. Ele é ignorado pelo Git. Para TLS, use a porta 8883, defina
`MQTT_TLS` em `src/config.h` e forneça a CA do broker em `MQTT_CA_CERT`.

## HIL

```bash
pio run -e esp32-hil -t upload
python ../simulador/central_sensores.py --porta COM5 --cenario auto
```

O simulador escreve NDJSON e drena os logs que voltam pela mesma UART. Quadros
maiores que 511 bytes ou JSON inválido são descartados. O heartbeat classifica
leituras antigas como degradadas/erro.

## Fonte física

- SHT31: temperatura/umidade em `0x44`.
- SGP40: sinal bruto compensado por T/RH + algoritmo VOC a 1 Hz.
- SCD41: modo periódico e leitura somente quando `dataReady`.
- PMS7003: parser não bloqueante, frame de 32 bytes e checksum.
- GPIO34: média de 32 leituras em mV, divisor 15k/10k, `gas_raw_v`.

`lpg_ppm` permanece nulo até calibração rastreável do conjunto analógico. Isso
mantém `sensor_status=DEGRADED`, sem fabricar uma precisão inexistente.

## MQTT e integridade

- Biblioteca MQTT com publicação QoS 1 real.
- ULID canônico por mensagem e `boot_id` por inicialização.
- `sequence` MQTT cresce durante o boot; consumidores usam `boot_id` para reset.
- NTP obrigatório: sem hora válida o firmware não publica data 1970.
- Last Will retido em `.../status` e reconexão com intervalo.
- Credenciais fora do código versionado.

## Estrutura

```text
include/secrets.example.h
src/config.h
src/contrato.h
src/main.cpp
src/hal/leitura.h
src/hal/fonte_sensores.h
src/hal/fonte_simulada.{h,cpp}
src/hal/fonte_fisica.{h,cpp}
src/net/publicador_mqtt.{h,cpp}
```

## Próximas evoluções

Persistência limitada de mensagens, watchdog/diagnóstico, OTA assinada com
rollback, mTLS por dispositivo e calibração/compensação registradas. Critérios
de release no roadmap de firmware.
