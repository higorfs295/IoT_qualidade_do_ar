# Central de Sensores Virtual (Hardware-in-the-Loop)

O elo **HIL** do projeto: um script Python que roda no PC e faz o papel dos
sensores físicos **durante o desenvolvimento**. Ele gera leituras ambientais
coerentes (de normais a emergências) e as envia, em **JSON por linha (NDJSON)**,
pela **Serial/USB** ao ESP32. O firmware real decodifica cada quadro como se
viesse de um sensor — é a `FonteSimulada` da HAL (ver
[`../BASE_FINAL.md`](../BASE_FINAL.md) e [`../firmware`](../firmware)).

Quando os sensores físicos chegarem, o firmware troca `MODO_SENSOR` para
`FONTE_FISICA` e este script deixa de ser necessário — **sem mudar mais nada**.

## Por que isso é útil

Você constrói e valida **hoje** todo o ecossistema (publicação MQTT, dashboards,
alertas, processamento de borda) usando o **ESP32 real** rodando o **firmware
real**, com os sensores emulados. O hardware sensível chega depois; o software
já está pronto e testado.

## Cenários

| Cenário | O que simula |
|---|---|
| `normal` | operação típica de ambiente fechado |
| `pico_poluicao` | particulado alto (trânsito, obra, fumaça externa) |
| `incendio` | CO₂ e particulado muito altos, VOC alto, temperatura sobe |
| `vazamento_glp` | pico de GLP (`lpg_ppm`) — cenário crítico do MiCS-5524 |
| `auto` | majoritariamente normal, injetando eventos aleatórios |

## Uso

```bash
pip install -r requirements.txt        # pyserial (só p/ enviar pela serial)

# Sem hardware: imprime os quadros (inspeção/validação)
python central_sensores.py --dry-run --intervalo 1

# Alimentando o ESP32 pela serial
python central_sensores.py --porta COM5 --baud 115200 --cenario auto

# Forçar uma emergência por 30 s
python central_sensores.py --dry-run --cenario incendio --duracao 30

# Conferir a geração e sair
python central_sensores.py --self-test
```

## Formato do quadro (NDJSON, uma linha por leitura)

```json
{"t":"sensors","seq":128,"co2_ppm":812,"voc_index":140,"lpg_ppm":6,"pm1_ugm3":9.2,"pm25_ugm3":14.7,"pm10_ugm3":22.1,"temperature_c":24.8,"humidity_pct":51.3,"cenario":"normal"}
```

- `co2_ppm`, `voc_index`, `lpg_ppm` são inteiros; particulados/temperatura/
  umidade são ponto flutuante. Mesmos nomes do contrato v1.1.
- O firmware detecta lacunas por `seq` e aplica **timeout/heartbeat**: se os
  quadros param de chegar, a telemetria vira `DEGRADED`/`ERROR`.

## Reuso

A geração coerente das leituras reaproveita o modelo de sensor da PoC
(`poc/qar_poc/sensor.py`, random walk em faixas plausíveis). Este script apenas
adiciona a **camada de cenários** e o **transporte serial**, evitando duplicar
lógica — coerência com o resto do repositório.
