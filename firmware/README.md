# Firmware ESP-WROOM-32 DevKit 30P USB-C

Firmware com HAL/Strategy para alternar entre HIL serial e sensores físicos sem
alterar a lógica de telemetria.

## Builds

```bash
pio run -e esp32-hil
pio run -e esp32-fisico
pio run -e esp32-aws
```

Os três ambientes foram compilados na auditoria de 31/07/2026. A coluna flash
usa cada slot OTA de 1.572.864 bytes, não os 4 MB inteiros:

| Ambiente | RAM | Flash |
|---|---:|---:|
| `esp32-hil` | 47.888 B (14,6%) | 787.625 B (50,1%) |
| `esp32-fisico` | 47.996 B (14,6%) | 818.353 B (52,0%) |
| `esp32-aws` | 49.024 B (15,0%) | 953.429 B (60,6%) |

Compilado não significa validado eletricamente. O ambiente físico requer o
bring-up de [`../docs/ROADMAP_FIRMWARE.md`](../docs/ROADMAP_FIRMWARE.md).

## Configuração segura

Na raiz do projeto:

```bash
python scripts/configure_firmware.py --ssid MINHA_REDE \
  --mqtt-host 192.168.1.10 --device-id esp32-sala-01 --site-id minha-casa
```

O script solicita a senha sem eco, valida IDs/porta/intervalo e grava
`include/secrets.h` com permissão restrita. Ele não sobrescreve um arquivo
existente sem `--force`. Para AWS, use `--aws --mqtt-port 8883` e forneça CA,
certificado e chave exclusivos; o ambiente já ativa TLS+mTLS.

## Placa e pinos

O alvo é o clone DevKit 30P/USB-C com módulo Wi-Fi ESP-WROOM-32. O perfil
PlatformIO `esp32doit-devkit-v1` é compatível com a pinagem GPIO, mas o
footprint físico precisa ser medido.

| Barramento | Pino da placa | GPIO |
|---|---|---:|
| I²C SDA/SCL | D21/D22 | 21/22 |
| PMS7003 RX/TX do ESP | D16/D17 | 16/17 |
| ADC MiCS | D34 | 34/ADC1_CH6 |
| HIL/log/upload | RX0/TX0 | 3/1 |

Detalhes e a ambiguidade `VIN`/`VN`: [`../docs/PINOUT_ESP32_WROOM32_30P.md`](../docs/PINOUT_ESP32_WROOM32_30P.md).

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
- Buffer MQTT/payload limitado a 896 bytes e recusa de publicação com heap
  abaixo do mínimo configurado.
- Metadados de heap livre/mínimo/maior bloco, uptime e motivo de reset.
- Tópicos e ULIDs em buffers fixos para reduzir fragmentação.

## Flash, OTA e memória

`partitions_4mb_ota.csv` reserva dois slots de 1,5 MiB e 960 KiB de LittleFS.
Isso prepara rollback OTA, mas não implementa ainda download/verificação da
imagem. Confirme os 4 MB reais com `esptool.py flash_id` antes de gravar.

Orçamento e gates: [`../docs/MEMORIA_ESP32_WROOM32.md`](../docs/MEMORIA_ESP32_WROOM32.md).

## AWS IoT Core

O ambiente `esp32-aws` usa sensores físicos, Wi-FiClientSecure e certificado de
cliente. Requisitos de runtime:

- `MQTT_HOST`: endpoint ATS da conta;
- `MQTT_PORT=8883`;
- `DEVICE_ID` = Thing Name = MQTT client ID;
- atributo do Thing `siteId` = `SITE_ID`;
- política mínima em [`../infra/aws/iot-policy-device.example.json`](../infra/aws/iot-policy-device.example.json).

Com certificados vazios ou porta incorreta, o firmware recusa conexão em vez de
usar TLS inseguro.

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

Persistência limitada de mensagens, watchdog, cliente OTA assinado/rollback,
secure boot/flash encryption quando aplicável, provisionamento de frota e
calibração registrada. Critérios no roadmap de firmware.
