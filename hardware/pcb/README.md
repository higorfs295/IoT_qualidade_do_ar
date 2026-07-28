# Shield PCB — Especificação (Fase 4, scaffold)

Placa que encaixa sobre o ESP32 DevKit V1 e organiza a ligação dos sensores,
alimentação e conectores. Esta é a **especificação de projeto**; o layout você
faz no seu EDA (KiCad/EasyEDA) a partir daqui.

## Objetivos

- Um **barramento I2C** limpo (com pull-ups) para SHT31, SGP40 e SCD41.
- Uma **UART** dedicada para o PMS7003.
- Uma **entrada ADC** para o MiCS-5524.
- Alimentação separada: **5 V** (ventoinha do PMS7003, aquecedor do MiCS) e
  **3.3 V** (I2C e lógica).
- Conectores por módulo (JST-XH) para montagem/manutenção fáceis.

## Mapa de ligação (coerente com `firmware/src/config.h`)

| Sinal | ESP32 | Vai para | Observação |
|---|---|---|---|
| I2C SDA | GPIO21 | SHT31, SGP40, SCD41 | pull-up 4.7 kΩ para 3.3 V |
| I2C SCL | GPIO22 | idem | pull-up 4.7 kΩ para 3.3 V |
| UART2 RX | GPIO16 | PMS7003 TX | 3.3 V-tolerante |
| UART2 TX | GPIO17 | PMS7003 RX | opcional (comandos SET/RESET) |
| ADC1 | GPIO34 | MiCS-5524 VOUT | GPIO34 é só entrada |
| 5 V | VIN/5V | PMS7003 (ventoinha), MiCS (heater) | corrente da fonte USB |
| 3.3 V | 3V3 | I2C e sensores lógicos | do regulador do DevKit |
| GND | GND | comum a todos | plano de terra sólido |

## Endereços I2C (sem conflito)

| Módulo | Endereço |
|---|---|
| SHT31-D | `0x44` |
| SGP40 | `0x59` |
| SCD41 | `0x62` |

## Cuidados de projeto

- **Desacoplamento**: capacitores de 100 nF perto de cada módulo; bulk de
  10–100 µF na entrada de 5 V (a ventoinha do PMS gera transientes).
- **Térmica**: manter o MiCS-5524 (aquece) e o regulador longe do SCD41/SHT31
  para não contaminar temperatura/umidade.
- **Roteamento I2C**: trilhas curtas; pull-ups únicos no barramento (não um por
  módulo).
- **Conectores**: JST-XH nomeados; serigrafia clara de 3.3 V vs 5 V.

## Entregáveis do projeto de PCB (a produzir no EDA)

- Esquemático, layout, Gerbers e BOM.
- Um `INTERCONEXAO.md` (ou SVG) com o diagrama de ligação, no estilo do
  `LIGACAO_ESP32.svg` do IoT-IDEA.
