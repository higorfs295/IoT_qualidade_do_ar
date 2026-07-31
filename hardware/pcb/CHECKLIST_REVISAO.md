# Checklist de liberação da PCB ESP-WROOM-32 30P

## Identidade e mecânica

- [ ] A placa real está marcada ESP-WROOM-32 e tem duas fileiras 1x15.
- [ ] USB-C, BOOT, EN e antena coincidem com o desenho de montagem.
- [ ] A distância entre fileiras e o passo foram medidos, não copiados de uma biblioteca.
- [ ] O pino duplicado `VIN` foi confirmado como VN/GPIO39 ou corrigido no símbolo.
- [ ] Impressão 1:1 do footprint encaixa sem esforço nos 30 pinos.

## Alimentação

- [ ] JP1 aberto no modo USB e fechado somente no modo externo sem USB.
- [ ] Não existe backfeed de USB/VIN para o rail de sensores.
- [ ] Polaridade de D1/D2, polyfuse e eletrolítico conferida.
- [ ] Queda em D1 e 5 V no VIN foram medidas sob pico de Wi-Fi.
- [ ] 3,3 V permanece dentro da tolerância no pico do SCD41.
- [ ] Dissipação de U2 não aquece a região dos sensores.

## Sinais

- [ ] D21/D22 = GPIO21/GPIO22; D16/D17 = GPIO16/GPIO17; D34 = GPIO34.
- [ ] GPIO34 não possui saída nem depende de pull-up interno.
- [ ] GPIO0/2/5/12/15 não recebem carga que altere o boot.
- [ ] UART0 RX0/TX0 não está conectada ao shield.
- [ ] Pull-ups I2C efetivos foram calculados considerando os breakouts.
- [ ] PMS7003 TX/RX não foram invertidos no conector físico.

## Layout e fabricação

- [ ] Zero cobre/trilha/via/componente sob ou à frente da antena.
- [ ] Plano GND contínuo, exceto keepout da antena, com retornos curtos.
- [ ] ADC separado de 5 V, UART, regulador e antena.
- [ ] Test points acessíveis com o shield e case montados.
- [ ] ERC/DRC sem erro não justificado; justificativas registradas.
- [ ] Gerber, drill, BOM, pick-and-place e desenho de montagem foram reabertos.

## Bring-up

- [ ] Resistência para GND medida em cada rail antes de energizar.
- [ ] Primeira alimentação feita sem ESP32/sensores e com limite de corrente.
- [ ] ESP32 instalado sozinho e boot/reset/upload testados.
- [ ] Sensores instalados um por vez; corrente e temperatura registradas.
