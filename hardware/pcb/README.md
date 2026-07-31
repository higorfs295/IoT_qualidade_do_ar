# Shield PCB Rev A — especificação

O shield organiza alimentação externa, sensores I2C, UART do PMS7003 e entrada
analógica protegida para o DevKit USB-C de 30 pinos com módulo ESP-WROOM-32.

> O arquivo EasyEDA ainda deve ser criado a partir das peças físicas medidas.
> Bibliotecas públicas de DevKit/conectores não devem ser aceitas sem conferir
> pinout e footprint 1:1.

- Guia completo de esquemático/PCB:
  [`../../docs/ROADMAP_HARDWARE_EASYEDA.md`](../../docs/ROADMAP_HARDWARE_EASYEDA.md)
- BOM inicial: [`BOM.csv`](BOM.csv)
- Netlist de revisão: [`netlist.csv`](netlist.csv)
- Pinout físico: [`pinout_esp32_wroom32_30p.csv`](pinout_esp32_wroom32_30p.csv)
- Regras iniciais: [`regras_pcb.csv`](regras_pcb.csv)
- Checklist de revisão: [`CHECKLIST_REVISAO.md`](CHECKLIST_REVISAO.md)
- Plano de bring-up: [`../../docs/PLANO_TESTES.md`](../../docs/PLANO_TESTES.md)

Decisões principais da Rev A:

- fonte externa regulada 5 V/2 A para o modo físico;
- jumper JP1: aberto durante USB/debug; alimentação externa do ESP32 só é
  habilitada sem USB. O diodo sozinho não autoriza duas fontes simultâneas;
- LDO 3,3 V dedicado aos sensores;
- GPIO21/22 para I2C, GPIO16/17 para PMS7003 e GPIO34/ADC1;
- divisor ADC 15 kΩ/10 kΩ (ganho 0,4; fator de firmware 2,5);
- `gas_raw_v` diagnóstico e `lpg_ppm=null` até calibração real;
- recorte/keepout total sobre a antena do ESP32;
- dois headers fêmea 1x15; distância entre fileiras definida após medição;
- o segundo `VIN` informado é tratado como VN/GPIO39 provável e não pode
  receber alimentação antes de confirmação física.
