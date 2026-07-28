# Shield PCB — Arquitetura, Pinagem e Alimentação (EasyEDA Pro)

Guia completo para você **desenhar a placa no EasyEDA Pro**: arquitetura de
energia, mapa de pinos, netlist, divisor de tensão do sensor de gás, BOM e
checklist de roteamento. A placa é um **shield** que encaixa sobre o ESP32
DevKit V1 e organiza os cinco sensores.

> Coerente com `firmware/src/config.h` (pinos) e com o `BASE_FINAL.md` (sensores).

---

## 1. Visão geral da placa

```text
                 ┌──────────────────────────────────────────────┐
                 │                 SHIELD PCB                    │
   USB 5V ──────►│  [5V rail] ──┬─────────────┬───────────┐      │
   (>=1A)        │              │             │           │      │
                 │           PMS7003        MiCS-5524   ESP32 VIN │
                 │           (ventoinha)    (aquecedor)  (5V)     │
                 │                              │                 │
                 │                          [÷2 divisor]──► GPIO34 (ADC)
                 │                                                │
                 │  [3V3 rail do DevKit] ──┬──────┬──────┐        │
                 │                       SCD41  SHT31  SGP40      │
                 │                       (I2C 0x62/0x44/0x59)     │
                 │   pull-ups 4k7 no I2C (SDA=21, SCL=22)         │
                 │   PMS7003 UART2: RX=16, TX=17                  │
                 └──────────────────────────────────────────────┘
```

Regra de ouro da divisão de energia:
- **5 V** para o que tem parte mecânica/aquecedor: **ventoinha do PMS7003** e
  **aquecedor do MiCS-5524**.
- **3.3 V** para a lógica sensível: os **três sensores I2C** (Sensirion).
- O **MiCS é analógico** e seu VOUT pode passar de 3.3 V → precisa de **divisor**
  antes do ADC do ESP32.

---

## 2. Estratégia de alimentação (o ponto crítico)

### 2.1. Orçamento de corrente

| Consumidor | Trilho | Corrente típica | Pico |
|---|---|---:|---:|
| ESP32 (Wi-Fi) | 5 V → 3V3 interno | ~160 mA | ~500 mA |
| PMS7003 (ventoinha) | 5 V | ~100 mA | ~120 mA |
| MiCS-5524 (aquecedor) | 5 V | ~35 mA | ~50 mA |
| SCD41 | 3.3 V | ~18 mA | ~205 mA (pico curto na medição) |
| SGP40 | 3.3 V | ~3 mA | ~5 mA |
| SHT31-D | 3.3 V | ~1.5 mA | ~1.5 mA |
| **Total aprox.** | | **~320 mA** | **~700 mA+** |

> **Correção de alimentação (importante):** uma porta USB de PC entrega só
> **500 mA** — insuficiente nos picos (Wi-Fi + ventoinha + medição do SCD41).
> **Use uma fonte USB de ≥ 1 A** (carregador de celular) e **capacitor bulk de
> 470–1000 µF** no trilho de 5 V, perto do PMS7003, para absorver o inrush da
> ventoinha e os picos de Wi-Fi. Sem isso, o ESP32 pode resetar (brownout).

### 2.2. Trilho de 3.3 V — duas opções

- **Opção A (simples):** usar o pino **3V3** do DevKit (regulador AMS1117 de
  bordo). Os três sensores I2C somam ~25 mA médios — dentro da folga. É o
  recomendado para o protótipo.
- **Opção B (baixo ruído):** um **LDO 3.3 V dedicado** no shield (ex.: MCP1700
  ou XC6206, ~250 mA), alimentado do 5 V, só para os sensores. Melhora a leitura
  analógica do MiCS e isola o ruído de chaveamento do Wi-Fi. Inclua se notar
  ruído no ADC.

### 2.3. Divisor de tensão do MiCS-5524 (o "redutor")

O MiCS-5524 é alimentado em **5 V** (aquecedor mais estável) e seu **VOUT
analógico pode chegar perto de 5 V** — isso **queimaria o GPIO34** (máx. 3.3 V).
Solução obrigatória: **divisor resistivo ÷2** + filtro RC.

```text
  MiCS VOUT ──[ R1 = 10 kΩ ]──┬──► GPIO34 (ADC1_CH6)
                              │
                          [ R2 = 10 kΩ ]     [ C = 100 nF ]
                              │                    │
                             GND                  GND

  Vadc = Vout · R2/(R1+R2) = Vout · 0.5     (0–5 V  ->  0–2.5 V)
  RC (R1‖R2 = 5 kΩ, C = 100 nF) -> fc ≈ 318 Hz (suaviza ruído do ADC)
```

- Mantém o ADC na faixa **linear** do ESP32 (≤ ~2.5 V) e protege o pino.
- No firmware, multiplique a leitura por **2** para recuperar o VOUT real antes
  de aplicar a curva de calibração (constante `MICS_DIVISOR` em `config.h`).

---

## 3. Pinagem completa (ESP32 DevKit V1, 30 pinos)

| ESP32 (GPIO) | Função | Liga em | Trilho | Observação |
|---|---|---|---|---|
| **21** | I2C SDA | SCD41 / SHT31 / SGP40 (SDA) | 3.3 V lógico | pull-up 4k7 → 3V3 |
| **22** | I2C SCL | SCD41 / SHT31 / SGP40 (SCL) | 3.3 V lógico | pull-up 4k7 → 3V3 |
| **16** (RX2) | UART2 RX | **PMS7003 TX** | 3.3 V lógico | dado do sensor |
| **17** (TX2) | UART2 TX | PMS7003 RX | 3.3 V lógico | opcional (SET/RESET) |
| **34** (ADC1_CH6) | Entrada analógica | **saída do divisor do MiCS** | 0–2.5 V | só entrada; nunca >3.3 V |
| **3V3** | Alimentação lógica | VCC de SCD41/SHT31/SGP40 | 3.3 V | opção A |
| **VIN/5V** | Alimentação 5 V | VCC de PMS7003 e MiCS-5524 | 5 V | da fonte USB |
| **GND** (vários) | Terra comum | todos os GND | — | plano de terra sólido |

Endereços I2C (sem conflito — podem compartilhar o mesmo barramento):

| Módulo | Endereço |
|---|---|
| SHT31-D | `0x44` |
| SGP40 | `0x59` |
| SCD41 | `0x62` |

---

## 4. Netlist (para desenhar no EasyEDA Pro)

Ligações por nó (net → pinos conectados):

```text
NET  +5V     : USB_5V, ESP32.VIN, PMS7003.VCC, MiCS.VCC, C_BULK+, C1(5V)+
NET  +3V3    : ESP32.3V3, SCD41.VCC, SHT31.VCC, SGP40.VCC, Rpu_SDA, Rpu_SCL, C2(3V3)+
NET  GND     : ESP32.GND, todos os .GND, C_BULK-, C1-, C2-, R2_div-, C_adc-
NET  I2C_SDA : ESP32.GPIO21, SCD41.SDA, SHT31.SDA, SGP40.SDA, Rpu_SDA
NET  I2C_SCL : ESP32.GPIO22, SCD41.SCL, SHT31.SCL, SGP40.SCL, Rpu_SCL
NET  PMS_TX  : PMS7003.TX, ESP32.GPIO16
NET  PMS_RX  : PMS7003.RX, ESP32.GPIO17
NET  MICS_OUT: MiCS.VOUT, R1_div.1
NET  ADC_IN  : R1_div.2, R2_div.1, C_adc.1, ESP32.GPIO34
             (R2_div.2 e C_adc.2 -> GND)
```

Passos no EasyEDA Pro:
1. **Novo projeto** → esquemático. Coloque o símbolo do **ESP32 DevKit V1**
   (biblioteca de peças; procure "ESP32 DevKitC" / "DOIT ESP32 DEVKIT V1").
2. Adicione **conectores** para os sensores (não os módulos inteiros): para os
   três I2C use **JST-SH 4 pinos (Qwiic/STEMMA QT)** encadeáveis; para o PMS7003
   um **JST-XH** conforme o cabo do módulo; para o MiCS um **JST-XH 3 pinos**
   (VCC/GND/VOUT).
3. Coloque **R1, R2** (divisor), **Rpu_SDA/SCL** (pull-ups), **capacitores** e
   trace os nets acima.
4. Atribua **footprints** (0805 para R/C do protótipo é confortável de soldar).
5. **Converter em PCB**, definir contorno do shield alinhado aos headers do
   DevKit, rotear, verificar DRC, exportar **Gerber** e **BOM**.

---

## 5. BOM (lista de materiais)

| Ref | Item | Qtd | Nota |
|---|---|---|---|
| U1 | ESP32 DevKit V1 (30 pinos) | 1 | placa-base |
| U2 | Sensirion **SCD41** (I2C) | 1 | CO₂ |
| U3 | Sensirion **SHT31-D** (I2C) | 1 | temp/umidade |
| U4 | Sensirion **SGP40** (I2C) | 1 | VOC index |
| U5 | Plantower **PMS7003** (UART) | 1 | particulados |
| U6 | **MiCS-5524** breakout | 1 | GLP (analógico) |
| R1,R2 | Resistor **10 kΩ** | 2 | divisor do MiCS (÷2) |
| R3,R4 | Resistor **4.7 kΩ** | 2 | pull-ups I2C (→3V3) |
| C1..C5 | Capacitor **100 nF** | 5 | desacoplamento + filtro ADC |
| C6,C7 | Capacitor **10 µF** | 2 | bulk local 3V3/5V |
| C8 | Capacitor **470–1000 µF** | 1 | bulk do 5 V (perto do PMS) |
| J1..J3 | Conector **JST-SH 4p** (Qwiic) | 3 | barramento I2C |
| J4 | Conector **JST-XH** (PMS) | 1 | conforme cabo do PMS7003 |
| J5 | Conector **JST-XH 3p** | 1 | MiCS (VCC/GND/VOUT) |
| — | Headers fêmea p/ o DevKit | 2 tiras | encaixe do shield |
| U7 | (Opcional) LDO 3.3 V MCP1700 | 1 | trilho 3V3 dedicado (Opção B) |

---

## 6. Checklist de roteamento e cuidados

- [ ] **Plano de terra** sólido (bottom), com vias fartas nos GND.
- [ ] **Bulk de 470–1000 µF** e 100 nF junto ao PMS7003 (inrush da ventoinha).
- [ ] **100 nF** em cada VCC de sensor, o mais perto possível do pino.
- [ ] **Pull-ups I2C únicos** (4k7). Se um breakout já tiver pull-up, remova/
      considere — pull-ups em paralelo baixam demais a resistência.
- [ ] **Divisor + 100 nF** no VOUT do MiCS antes do GPIO34 (nunca ligar direto).
- [ ] **Térmica:** afaste MiCS (aquece) e o regulador do **SCD41/SHT31**, senão
      a temperatura/umidade lidas ficam contaminadas.
- [ ] Trilhas de **5 V** mais largas (corrente da ventoinha/aquecedor).
- [ ] I2C com trilhas curtas; se der ruído, reduza pull-up para 2k2.
- [ ] Rotule na serigrafia **3.3 V vs 5 V** para não trocar na montagem.

---

## 7. Reflexo no firmware

- Pinos já batem com `firmware/src/config.h` (`I2C_SDA=21`, `I2C_SCL=22`,
  `PMS_UART_RX=16`, `PMS_UART_TX=17`, `MICS_ADC_PIN=34`).
- Adicione a constante do divisor no `config.h`:
  `#define MICS_DIVISOR 2.0f` e, no `lerMiCS5524()`, calcule
  `Vout = (adc/4095.0f)*Vref*MICS_DIVISOR` antes da curva de calibração.
- Lembre: o **SCD41 tem pico de ~205 mA** durante a medição — mais um motivo
  para o bulk no 5 V e uma fonte ≥ 1 A.
