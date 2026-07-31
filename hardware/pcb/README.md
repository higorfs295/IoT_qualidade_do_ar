# Shield PCB Rev A — especificação

O shield organiza alimentação externa, sensores I2C, UART do PMS7003 e entrada
analógica protegida para o ESP32 DevKit V1 de 30 pinos.

> O arquivo EasyEDA ainda deve ser criado a partir das peças físicas medidas.
> Bibliotecas públicas de DevKit/conectores não devem ser aceitas sem conferir
> pinout e footprint 1:1.

- Guia completo de esquemático/PCB:
  [`../../docs/ROADMAP_HARDWARE_EASYEDA.md`](../../docs/ROADMAP_HARDWARE_EASYEDA.md)
- BOM inicial: [`BOM.csv`](BOM.csv)
- Netlist de revisão: [`netlist.csv`](netlist.csv)
- Plano de bring-up: [`../../docs/PLANO_TESTES.md`](../../docs/PLANO_TESTES.md)

Decisões principais da Rev A:

- fonte externa regulada 5 V/2 A para o modo físico;
- isolamento para impedir alimentação reversa da USB;
- LDO 3,3 V dedicado aos sensores;
- GPIO21/22 para I2C, GPIO16/17 para PMS7003 e GPIO34/ADC1;
- divisor ADC 15 kΩ/10 kΩ (ganho 0,4; fator de firmware 2,5);
- `gas_raw_v` diagnóstico e `lpg_ppm=null` até calibração real;
- recorte/keepout total sobre a antena do ESP32;
- conectores e distância dos headers definidos somente após medição.
