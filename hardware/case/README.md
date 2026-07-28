# Case (SolidWorks) — Especificação Paramétrica (Fase 4, scaffold)

Invólucro para o ESP32 + shield PCB + sensores. Este documento é a
**especificação para você modelar no SolidWorks** — os arquivos `.sldprt`/
`.sldasm` são binários proprietários e **não são gerados aqui**; modele-os a
partir dos parâmetros e requisitos abaixo.

## Requisitos funcionais (o que o case precisa garantir)

1. **Circulação de ar** para os sensores — sem fluxo, as leituras mentem.
2. **Isolamento térmico** entre o ESP32/regulador (que esquentam) e o
   SHT31/SCD41, para não contaminar temperatura/umidade.
3. **Entrada e saída de ar dedicadas à ventoinha do PMS7003** (o fluxo dele é
   direcional).
4. **Acesso ao conector USB** (alimentação + elo HIL).
5. **Fixação** do ESP32+shield e de cada módulo.
6. Montagem/manutenção fáceis (tampa removível).

## Parâmetros sugeridos (ajuste ao seu conjunto real)

| Parâmetro | Valor inicial | Nota |
|---|---|---|
| Dimensões internas | 100 × 70 × 40 mm | cabe DevKit + shield + módulos |
| Espessura de parede | 2.0 mm | rígido para impressão FDM |
| Furos de ventilação | Ø 4 mm, grade | nas faces dos sensores de gás/ambiente |
| Duto do PMS7003 | 2 aberturas alinhadas ao fluxo | entrada e exaustão |
| Recorte USB | 12 × 6 mm | lateral, alinhado ao conector do DevKit |
| Postes de fixação | M2.5 / M3 | para ESP32 e módulos |
| Folga da tampa | 0.2 mm | encaixe por pressão + parafusos M3 |

## Diretrizes de projeto (SolidWorks)

- Modele com **equações/parâmetros globais** (largura, altura, parede, folga)
  para ajustar tudo de uma vez quando medir as peças reais.
- Separe o **compartimento dos sensores** (ventilado) do **compartimento do
  ESP32** (com uma divisória), reduzindo o aquecimento cruzado.
- Oriente a **ventoinha do PMS7003** para puxar ar externo e exaurir pelo lado
  oposto (fluxo atravessa a câmara de medição).
- Prefira **impressão FDM**: paredes de 2 mm, sem overhangs agressivos.

## Entregáveis (a produzir no SolidWorks)

- `case.sldprt` (corpo) e `tampa.sldprt`, ou uma `case.sldasm`.
- Exportar **STL** para impressão e um **PDF de desenho** cotado.
- (Opcional) foto/renders para o `docs/` do projeto.

> Quando tiver os STL/desenhos, coloque-os aqui em `hardware/case/` e referencie
> no [`../../BASE_FINAL.md`](../../BASE_FINAL.md).
