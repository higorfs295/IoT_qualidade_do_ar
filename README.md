# Estação IoT de Qualidade do Ar

Estação experimental baseada em ESP32 para monitorar CO₂, partículas, VOC,
temperatura e umidade, com firmware alternável entre sensores simulados
(Hardware-in-the-Loop) e físicos, telemetria MQTT, ingestão em tempo real e
dashboard web.

> **Escopo de segurança:** este é um protótipo acadêmico/experimental. Não é um
> detector certificado de gás, fumaça ou incêndio e não substitui instrumentos
> calibrados, alarmes regulamentares nem orientação profissional. O canal
> analógico MiCS publica tensão bruta; `lpg_ppm` só pode ser habilitado depois de
> calibração rastreável do conjunto físico.

## Estado da versão final da base

| Parte | Estado verificável | Próximo gate |
|---|---|---|
| Firmware HIL | implementado e compilado | flash no ESP32 + teste serial |
| Firmware físico | implementado e compilado | bancada sensor a sensor + calibração |
| Simulador HIL | implementado; self-test aprovado | teste com porta serial real |
| Contrato v1.1 | validadores Python/Node e testes aprovados | compatibilidade em bancada |
| Backend | MVP funcional em memória; teste HTTP aprovado | persistência e autenticação de produção |
| Dashboard web | MVP funcional, responsivo e com aviso de escopo | histórico/alertas persistentes |
| Broker/PoC de carga | configuração e gerador disponíveis | benchmark reproduzido na máquina-alvo |
| PCB | especificação, BOM, netlist e roteiro completos | esquemático/PCB no EasyEDA + revisão elétrica |
| Case | roteiro paramétrico completo | medir montagem e modelar no SolidWorks |
| Mobile | arquitetura e roadmap definidos | criar o projeto Flutter |

Detalhes e evidências: [`docs/STATUS_PROJETO.md`](docs/STATUS_PROJETO.md).

## Arquitetura

```text
Central HIL (PC) --NDJSON/USB--┐
                              ├--> ESP32/HAL --> MQTT QoS 1 --> Mosquitto
Sensores físicos I2C/UART/ADC-┘                            |
                                                            +--> backend
                                                                 |-- REST
                                                                 |-- WebSocket
                                                                 +--> dashboard web
```

O padrão Strategy mantém a aplicação independente da fonte dos sensores. O
ambiente `esp32-hil` lê quadros do simulador; `esp32-fisico` lê SHT31, SGP40,
SCD41, PMS7003 e a entrada analógica. Ambos geram o mesmo payload v1.1.

## Início rápido: demonstração sem hardware

Pré-requisitos: Python 3.10+ e Node.js 20+.

```bash
# Terminal 1: backend + dashboard (o MQTT pode ficar indisponível nesta demo)
cd dashboard/backend
npm ci
npm start

# Abra http://localhost:3001. Sem dados, o front pode operar em modo mock.

# Validar o gerador HIL sem ESP32
python simulador/central_sensores.py --self-test
python simulador/central_sensores.py --dry-run --cenario auto --duracao 10

# Testes automatizados
python -m unittest discover -s poc/tests -v
cd dashboard/backend && npm test
```

## Início rápido: fluxo MQTT local

```bash
# Terminal 1 - broker
cd infra/server_config
docker compose up -d mosquitto

# Terminal 2 - backend
cd dashboard/backend
npm ci && npm start

# Terminal 3 - poucos dispositivos virtuais
cd poc
python -m pip install -r requirements.txt
python ingestao_teste.py --host localhost --sensores 5 --gateways 1 \
  --intervalo 3 --duracao 60
```

O dashboard fica em `http://localhost:3001`. O listener 1883 é anônimo e só
deve ser usado em rede local isolada.

## Firmware ESP32

1. Copie `firmware/include/secrets.example.h` para
   `firmware/include/secrets.h` e configure Wi-Fi/broker.
2. Compile um dos ambientes:

```bash
cd firmware
pio run -e esp32-hil
pio run -e esp32-fisico
```

3. Para HIL, grave o primeiro ambiente e execute:

```bash
pio run -e esp32-hil -t upload
python ../simulador/central_sensores.py --porta COM5 --cenario auto
```

O firmware só publica depois de obter horário NTP válido, usa ULID canônico,
inclui `boot_id` e publica com QoS 1 real. Instruções completas:
[`firmware/README.md`](firmware/README.md) e
[`docs/ROADMAP_FIRMWARE.md`](docs/ROADMAP_FIRMWARE.md).

## Contrato de telemetria

Tópico:

```text
qualidade-ar/{site_id}/{device_id}/telemetria
```

Payload resumido:

```json
{
  "schema_version": "1.1",
  "message_id": "01JQ7PK0P3R7V5BT7P0Q9YQ8A1",
  "device_id": "esp32-sala-01",
  "site_id": "campus-ufg",
  "sent_at": "2026-07-31T12:00:00.000Z",
  "sequence": 1,
  "measurements": {
    "co2_ppm": 620,
    "voc_index": 102,
    "lpg_ppm": null,
    "pm1_ugm3": 5.0,
    "pm25_ugm3": 9.0,
    "pm10_ugm3": 14.0,
    "temperature_c": 24.2,
    "humidity_pct": 51.0
  },
  "quality": { "gas_status": "SAFE", "sensor_status": "DEGRADED" },
  "metadata": { "firmware_version": "1.1.0", "boot_id": "..." }
}
```

Campos de medição podem ser `null` quando indisponíveis, mas um payload com
`sensor_status: "OK"` não pode conter medida obrigatória nula. Especificação:
[`docs/CONTRATO_TELEMETRIA.md`](docs/CONTRATO_TELEMETRIA.md).

## Estrutura do repositório

```text
firmware/       ESP32, HAL HIL/física e MQTT
simulador/      central de sensores via Serial/USB
poc/            gerador de carga e consumidor MQTT em Python
dashboard/      backend Node e painel web
infra/          Mosquitto, ThingsBoard e plano de nuvem
hardware/pcb/   especificação elétrica/EasyEDA Pro
hardware/case/  especificação mecânica/SolidWorks
mobile/         arquitetura do futuro app Flutter
docs/           contrato, status, testes, roadmaps e artefatos finais
```

## Roadmaps e documentação final

- [`docs/ROADMAP_GERAL.md`](docs/ROADMAP_GERAL.md) — sequência de execução e gates.
- [`docs/ROADMAP_FIRMWARE.md`](docs/ROADMAP_FIRMWARE.md) — bring-up, calibração e release.
- [`docs/ROADMAP_SOFTWARE.md`](docs/ROADMAP_SOFTWARE.md) — backend, web, mobile e nuvem.
- [`docs/ROADMAP_HARDWARE_EASYEDA.md`](docs/ROADMAP_HARDWARE_EASYEDA.md) — esquemático e PCB no EasyEDA Pro.
- [`docs/ROADMAP_CASE_SOLIDWORKS.md`](docs/ROADMAP_CASE_SOLIDWORKS.md) — case paramétrico no SolidWorks.
- [`docs/PLANO_TESTES.md`](docs/PLANO_TESTES.md) — matriz de verificação e aceite.
- [`docs/estimativa_carga.md`](docs/estimativa_carga.md) — volumetria e fórmulas.
- [`docs/estimativa_carga.xlsx`](docs/estimativa_carga.xlsx) — calculadora editável com cenários e gráfico.
- [`docs/arquitetura_solucao.pdf`](docs/arquitetura_solucao.pdf) — dossiê técnico diagramado.
- [`docs/apresentacao_slides.pdf`](docs/apresentacao_slides.pdf) — apresentação executiva em 11 páginas.
- [`docs/telemetria-v1.1.schema.json`](docs/telemetria-v1.1.schema.json) — JSON Schema do contrato.
- [`docs/modelagem_dados.json`](docs/modelagem_dados.json) — modelo lógico para a persistência.
- [`ARQUITETURA.md`](ARQUITETURA.md) — histórico detalhado da PoC de ingestão.
- [`BASE_FINAL.md`](BASE_FINAL.md) — blueprint original da evolução do projeto.

Os PDFs podem ser regenerados por `python docs/tools/build_pdfs.py` em um
ambiente com ReportLab instalado. A planilha tem fonte reproduzível em
`docs/tools/build_estimativa_carga.mjs` e usa `@oai/artifact-tool`.

## Critério de conclusão do produto físico

A base de software está compilável e testada, mas o produto só deve ser chamado
de “validado” após: revisão do esquemático por outra pessoa, ERC/DRC sem erros,
teste de alimentação com carga, bring-up individual dos sensores, comparação
com referências, ensaio térmico do case, teste de perda/reconexão MQTT e registro
dos resultados conforme [`docs/PLANO_TESTES.md`](docs/PLANO_TESTES.md).

## Autoria e contexto

Projeto acadêmico da UFG, disciplina de Internet das
Coisas. A documentação preserva o histórico das atividades anteriores e separa
explicitamente resultados reproduzidos nesta revisão de resultados históricos.
