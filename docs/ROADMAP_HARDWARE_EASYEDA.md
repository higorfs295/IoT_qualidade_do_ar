# Roadmap do esquemático e PCB no EasyEDA Pro

Este roteiro produz um shield Rev A para o **DevKit USB-C de 30 pinos com
módulo ESP-WROOM-32** descrito em [`PINOUT_ESP32_WROOM32_30P.md`](PINOUT_ESP32_WROOM32_30P.md).
Não selecione footprint pela aparência: DevKits, breakouts e cabos vendidos com
o mesmo nome variam. Meça e confirme os itens físicos antes de liberar Gerber.

Referências de operação do editor: [criar projeto](https://prodocs.easyeda.com/en/project/file-new-project/index.html),
[converter esquemático em PCB](https://prodocs.easyeda.com/en/schematic/design-update-convert-schematic-to-pcb/index.html)
e [exportar BOM/Gerber](https://prodocs.easyeda.com/en/schematic/export-order-parts/index.html).

## 1. Arquitetura elétrica Rev A

```text
J_PWR 5 V regulados -> F1 polyfuse -> +5V_SYS -----> PMS7003 / breakout MiCS
                              |       |  |
                              |       |  +-> D_ESP -> JP1 -> VIN do DevKit
                              |       +----> U_LDO 3V3 -> sensores I2C
                              +-> TVS + bulk -> GND

ESP32 GPIO21/22 <---- I2C + pull-ups selecionáveis ---- SHT31/SGP40/SCD41
ESP32 GPIO16    <---------------- PMS_TX
ESP32 GPIO17    ----------------> PMS_RX
MiCS VOUT -> 15k/10k + RC + proteção -> GPIO34 (ADC1)
```

### Por que há uma entrada externa

O modo físico deve usar uma fonte regulada de 5 V/2 A no conector do shield.
`D_ESP` bloqueia o caminho inverso do VIN do DevKit para as cargas, mas **não é
um power mux**. `JP1` torna a escolha explícita:

- HIL: USB-C ligado, fonte externa desligada, `JP1` aberto;
- debug físico: USB-C alimenta o ESP32, fonte externa alimenta sensores,
  terras comuns e `JP1` aberto;
- autônomo: USB-C desconectado, fonte externa alimenta tudo e `JP1` fechado.

Nunca fechar `JP1` com USB-C energizado. A documentação oficial do DevKit trata
USB, 5 V e 3V3 como alternativas de alimentação, não fontes simultâneas.

### Trilhos

- `+5V_SYS`: PMS7003, módulo analógico compatível, bulk e entrada do LDO.
- `+3V3_SENS`: SHT31, SGP40 e SCD41; não alimentar esses ICs com 5 V.
- `+3V3_ESP`: nível lógico do DevKit; os dois 3,3 V devem ter terra comum e
  tensão compatível. Pull-ups ficam em `+3V3_SENS` apenas quando o sistema
  externo também alimenta o ESP32.
- GND: plano contínuo. Separação “analógica/digital” deve ser por posicionamento
  e caminho de corrente, não por cortar o retorno do plano.

## 2. Decisões que precisam ser fechadas antes do desenho

1. Resolver o segundo `VIN` informado: nessa posição ele é VN/GPIO39 provável.
   Confirmar por serigrafia/continuidade e nunca aplicar 5 V até resolver.
2. Medir distância entre fileiras, passo, comprimento e altura dos headers do
   DevKit real; fotografar com paquímetro.
3. Identificar pinout e conector do PMS7003 comprado. “JST-XH” genérico não é
   uma especificação suficiente.
4. Identificar se o MiCS-5524 é **sensor cru** ou **breakout condicionado**.
   Este shield aceita somente uma saída analógica condicionada 0–5 V. O sensor
   cru exige circuito de aquecimento/medição próprio e outro esquemático.
5. Confirmar se breakouts I2C já possuem pull-ups; resistores em paralelo podem
   deixar o barramento forte demais.
6. Definir dimensões mecânicas, posição da antena e conectores junto do case.

Sem essas seis evidências, o resultado é apenas um desenho conceitual.

## 3. Esquemático — folha 1: alimentação

### Componentes

- `J1`: entrada 5 V/GND chaveada e polarizada, corrente >=2 A.
- `F1`: polyfuse hold aproximado 1,1–1,5 A, escolhido após corrente medida.
- `D_TVS`: TVS compatível com barramento 5 V e energia esperada.
- `C1`: 1000 µF/10 V low-ESR; `C2`: 10 µF; `C3`: 100 nF.
- `D_ESP`: Schottky >=1 A entre `+5V_SYS` e `ESP32_5V`.
- `JP1`: jumper removível entre D_ESP e VIN; deve ficar aberto durante USB.
- `U2`: LDO 3,3 V >=600 mA (AP2112K-3.3 ou equivalente) com capacitores do
  datasheet e dissipação/elevação térmica verificadas. Se aquecer os sensores,
  migrar para buck de baixo ruído e refazer layout/EMI.
- LEDs opcionais de 5 V/3,3 V com resistores; acrescente jumpers para isolar
  cada trilho durante o bring-up.

### Nets

```text
J1.5V -> F1.1
F1.2 -> +5V_SYS
+5V_SYS -> D_TVS.K, C1+, C2+, C3+, D_ESP.A, U2.IN, J_PMS.VCC, J_GAS.VCC
D_ESP.K -> JP1.1
JP1.2 -> ESP32_VIN
U2.OUT -> +3V3_SENS
J1.GND, D_TVS.A, capacitores-, U2.GND -> GND
```

Coloque test points `TP_5V`, `TP_3V3`, `TP_GND` e um ponto de medição de
corrente (jumper ou resistor 0 Ω) antes das cargas.

## 4. Esquemático — folha 2: ESP32 e sensores

### Símbolo do DevKit de 30 pinos

Crie dois conectores 1x15 conforme o CSV físico, com `D21/GPIO21`,
`D22/GPIO22`, `D16/GPIO16`, `D17/GPIO17` e `D34/GPIO34` explícitos. Marque
RX0/TX0, strapping pins e entradas-only com notas elétricas. O pad ambíguo só
recebe o nome VN/GPIO39 depois do gate físico. VP/VN não são alimentação.

### I2C

```text
I2C_SDA: ESP32.GPIO21, J_SHT.SDA, J_SGP.SDA, J_SCD.SDA, R_SDA.1
I2C_SCL: ESP32.GPIO22, J_SHT.SCL, J_SGP.SCL, J_SCD.SCL, R_SCL.1
R_SDA.2/R_SCL.2 -> +3V3_SENS via jumpers de solda
```

Use 4,7 kΩ como ponto inicial e pads de jumper para desligar os pull-ups do
shield. Conectores Qwiic/JST-SH de 4 vias normalmente usam GND/3V3/SDA/SCL,
mas confirme a orientação e o pin 1 do footprint escolhido.

### PMS7003

```text
PMS_TX -> ESP32.GPIO16
ESP32.GPIO17 -> PMS_RX
PMS_VCC -> +5V_SYS
PMS_GND -> GND
```

Exponha `SET` e `RESET` em pads/jumper, mesmo que a Rev A não os controle.
Não invente o footprint do conector: use o mating part do cabo real.

### Entrada analógica

```text
J_GAS.VOUT -> R1 15k -> ADC_DIV
ADC_DIV -> R2 10k -> GND
ADC_DIV -> C_ADC 100nF -> GND
ADC_DIV -> R_SER 1k -> ADC_PROT -> ESP32.GPIO34
ADC_PROT -> diodos Schottky de clamp para GND/+3V3_ESP (opcional recomendado)
```

O ganho do divisor é `10/(15+10)=0,4`; 5 V viram 2 V. O firmware usa
`MICS_DIVISOR=2.5`. O canal é diagnóstico até calibração. GPIO34 é somente
entrada e pertence ao ADC1, o que evita o conflito clássico ADC2/Wi-Fi.

### Desacoplamento

Cada conector de sensor deve ter 100 nF próximo ao pino de alimentação e um
10 µF por grupo. Não some capacitores ao acaso: confirme estabilidade do LDO e
inrush do PMS em bancada.

## 5. Criar o projeto no EasyEDA Pro

1. `File > New > Project`; mantenha esquemático e PCB sob o mesmo **Board**.
2. Crie duas páginas: `01_POWER` e `02_ESP_SENSORS`.
3. Coloque símbolos genéricos de conectores para módulos; símbolos devem mostrar
   os nomes funcionais dos pinos, não esconder o pinout.
4. Crie um device próprio para o DevKit medido, usando dois headers 1x15.
   Numere símbolo/footprint de forma idêntica, preserve o lado do USB-C e marque
   pinos sem uso com `No Connect`.
5. Preencha em cada componente: designator, valor, fabricante/MPN quando
   definido, footprint e propriedade `DNP` para opcionais.
6. Use net labels iguais aos nomes acima; evite fios longos cruzando páginas.
7. `Design > Annotate Designator`, depois ERC/DRC do esquemático.
8. Abra `Tools > Footprint Manager`; resolva qualquer símbolo sem footprint e
   qualquer divergência entre número do pino e pad.

## 6. Footprints e revisão de biblioteca

Para cada footprint imprima 1:1 em papel e coloque a peça sobre ele. Verifique:

- pitch, distância entre fileiras, diâmetro do pino e courtyard;
- pin 1, orientação do cabo e polaridade;
- dimensão real de capacitor eletrolítico e furação;
- altura do DevKit/shield e espaço para USB/EN/BOOT;
- posição da antena do ESP32.

O shield não deve ter cobre, plano, trilha, componente ou metal sobre/sob a
região da antena. Preferencialmente faça um recorte no contorno do shield para a
antena ficar fora da placa.

## 7. Converter e configurar a PCB

1. No esquemático: `Design > Schematic to PCB`; aplique todas as mudanças.
2. Desenhe `Board Outline` somente depois de fechar medidas do DevKit/case.
3. Camadas: 2 cobre, FR-4 1,6 mm, cobre 1 oz como ponto de partida.
4. Importe/replique as classes de [`../hardware/pcb/regras_pcb.csv`](../hardware/pcb/regras_pcb.csv).
5. Regras conservadoras para uma fabricação comum:

| Regra | Valor inicial |
|---|---:|
| trilha/espaço mínimo | 0,25/0,25 mm |
| via/puro | 0,60/0,30 mm |
| cobre até borda | >=0,30 mm |
| sinais | 0,25 mm |
| 3,3 V | 0,50 mm |
| 5 V/PMS | 1,00 mm, recalcular após corrente medida |

Confirme os limites no fabricante escolhido; regras de produção podem mudar.

## 8. Posicionamento

1. Trave os headers do ESP32 e o contorno.
2. Mantenha o recorte/keepout da antena.
3. Coloque entrada, fusível, TVS e bulk juntos na borda.
4. Coloque o LDO e seus capacitores conforme o datasheet.
5. Coloque divisor/RC junto do GPIO34 e longe de antena, UART e trilhas de carga.
6. Posicione conectores nas bordas conforme o fluxo do case; não atravesse a
   placa com cabos do PMS.
7. Afaste SHT31/SCD41 de ESP32, LDO, MiCS e exaustão do PMS.
8. Acrescente furos M3 e keepout mecânico; nenhum pad sob espaçador metálico.

## 9. Roteamento e planos

- Rotear 5 V primeiro, depois 3,3 V, UART/I2C/ADC e sinais restantes.
- Manter SDA/SCL curtos, juntos e sem stubs grandes; 100 kHz na Rev A.
- Não rotear ADC em paralelo com 5 V/PMS; cercar com GND se necessário.
- Plano GND nas duas camadas com stitching vias, sem criar ilhas.
- Revisar caminhos de retorno de PMS/LDO para que não passem pelo ADC.
- Aplicar teardrops apenas se suportado pelo fabricante e revisar manualmente.
- Serigrafar tensão, função, pin 1, direção de fluxo, revisão e pontos de teste.

## 10. Verificações antes do Gerber

- [ ] ERC e DRC sem erro não justificado.
- [ ] Netlist comparada com `hardware/pcb/netlist.csv`.
- [ ] Footprints impressos 1:1 e conferidos com peças reais.
- [ ] Antena livre e recorte correto.
- [ ] Nenhuma alimentação pode retornar à USB do computador.
- [ ] JP1 e os três modos de alimentação estão documentados na serigrafia.
- [ ] O pino VN/GPIO39 foi confirmado; não existe segundo VIN fictício.
- [ ] Polaridade de eletrolítico, TVS, diodo, LDO e conectores revisada.
- [ ] Tensão ADC máxima calculada e medida.
- [ ] Trilhas de corrente verificadas com corrente/pico medidos.
- [ ] Revisão independente de esquemático e PCB concluída.
- [ ] BOM sem `TBD` para os componentes que serão montados.
- [ ] [`CHECKLIST_REVISAO.md`](../hardware/pcb/CHECKLIST_REVISAO.md) assinado.

## 11. Exportação e fabricação

No PCB use `Export > Generate PCB Fabrication File` para Gerber. Exporte também
BOM, pick-and-place (se houver SMT), PDF de montagem, esquemático PDF e arquivo
fonte `.epro`. Abra os Gerbers em um visualizador independente e confira todas
as camadas, furos, contorno e polaridades antes do pedido.

Versione os entregáveis em `hardware/pcb/rev_a/` com README contendo fabricante,
stackup, cor, espessura, cobre e data. Não versione arquivos de pedido contendo
endereço ou dados pessoais.

## 12. Bring-up da PCB

Comece sem ESP32/sensores, com fonte limitada. Confirme resistência entre rails,
tensões, corrente e temperatura. Instale alimentação/LDO, depois ESP32, depois
um sensor por vez. A sequência completa e os critérios estão em
[`PLANO_TESTES.md`](PLANO_TESTES.md).
