# Pinout validado para o DevKit ESP-WROOM-32 de 30 pinos

## Identificação da placa

Alvo desta revisão: placa de desenvolvimento com módulo metálico marcado
**ESP-WROOM-32**, Wi-Fi 2,4 GHz, conector USB-C, botões **BOOT** e **EN** e duas
fileiras de 15 pinos. No PlatformIO ela permanece compatível com
`esp32doit-devkit-v1`; o conector USB-C e o conversor USB-UART do clone não
alteram a numeração GPIO.

> O segundo `VIN` informado, entre `D34` e `VP`, coincide fisicamente com
> **VN/GPIO39** nos DevKits de 30 pinos conhecidos. Ele é tratado como
> `VN/GPIO39 provável`, nunca como alimentação, até confirmar a serigrafia da
> própria placa e medir continuidade. Ligar 5 V nesse ponto sem confirmação
> pode destruir o ESP32.

Arquivo para conferência/entrada no EasyEDA:
[`../hardware/pcb/pinout_esp32_wroom32_30p.csv`](../hardware/pcb/pinout_esp32_wroom32_30p.csv).

## Vista fornecida, normalizada

Orientação: USB-C no topo, antena do ESP-WROOM-32 no lado oposto.

| Linha | Esquerda | Direita | Interpretação |
|---:|---|---|---|
| 1 | 3V3 | VIN | 3,3 V / entrada de 5 V |
| 2 | GND | GND | terra |
| 3 | D15 | D13 | GPIO15 / GPIO13 |
| 4 | D2 | D12 | GPIO2 / GPIO12 |
| 5 | D4 | D14 | GPIO4 / GPIO14 |
| 6 | D16 | D27 | GPIO16 / GPIO27 |
| 7 | D17 | D26 | GPIO17 / GPIO26 |
| 8 | D5 | D25 | GPIO5 / GPIO25 |
| 9 | D18 | D33 | GPIO18 / GPIO33 |
| 10 | D19 | D32 | GPIO19 / GPIO32 |
| 11 | D21 | D35 | GPIO21 / GPIO35 |
| 12 | RX0 | D34 | GPIO3/U0RX / GPIO34 |
| 13 | TX0 | `VIN` informado | GPIO1/U0TX / **VN/GPIO39 provável** |
| 14 | D22 | VP | GPIO22 / GPIO36 |
| 15 | D23 | EN | GPIO23 / CHIP_PU/reset |

## Alocação usada pelo projeto

| Função | Pino da placa | GPIO | Motivo |
|---|---|---:|---|
| I²C SDA | D21 | 21 | GPIO geral, barramento dos três sensores |
| I²C SCL | D22 | 22 | GPIO geral, sem função de boot |
| PMS7003 TX -> ESP RX | D16 | 16 | UART2 RX; disponível no ESP-WROOM-32 |
| ESP TX -> PMS7003 RX | D17 | 17 | UART2 TX; disponível no ESP-WROOM-32 |
| MiCS condicionado -> ADC | D34 | 34 | ADC1_CH6, funciona com Wi-Fi ativo |
| HIL/log/upload | RX0/TX0 | 3/1 | ponte USB-UART da placa |

Esse mapeamento não usa pinos de strapping como periférico e não usa ADC2, que
tem restrições quando o rádio Wi-Fi está ativo.

## Restrições que entram no esquemático

- GPIO34, GPIO35, VP/GPIO36 e VN/GPIO39 são **somente entrada** e não têm
  pull-up/pull-down interno; qualquer estado definido precisa de componente
  externo.
- GPIO0/BOOT, GPIO2, GPIO5, GPIO12 e GPIO15 participam da configuração de boot.
  Não conectar sensores que possam forçar nível nesses pinos durante reset.
- GPIO12 merece cuidado especial: nível inadequado no boot pode selecionar
  tensão incompatível para a flash. Ele fica sem uso neste shield.
- GPIO1/GPIO3 pertencem à UART0 e são compartilhados com USB, gravação e logs;
  ficam fora do shield de sensores.
- EN é reset/CHIP_PU, não GPIO. VP/VN são nomes analógicos, não trilhos de
  alimentação.
- GPIO6 a GPIO11 pertencem à flash interna do módulo e não devem ser usados.
- A região da antena deve ficar sem cobre, trilhas, plano, parafuso, bateria ou
  parede metalizada, inclusive nas camadas internas da PCB do shield.

## Gate obrigatório antes do footprint EasyEDA

1. Fotografar frente/verso com a placa na orientação acima.
2. Medir passo de 2,54 mm, distância entre as fileiras, comprimento total,
   largura, altura dos headers e posição da USB-C/botões/antena.
3. Em modo continuidade e **sem alimentação**, confirmar os dois GNDs.
4. Confirmar que o VIN superior chega ao barramento de 5 V da placa.
5. Confirmar que o pino ambíguo não tem continuidade com VIN/5 V; identificar
   como VN/GPIO39 usando a serigrafia ou um sketch de leitura.
6. Imprimir o footprint EasyEDA em escala 1:1 e encaixar a placa real antes de
   liberar a PCB.

Nenhuma biblioteca genérica de “ESP32 30 pin” substitui esse gate: clones USB-C
podem variar em largura, regulador, ponte USB e ordem física dos headers.
