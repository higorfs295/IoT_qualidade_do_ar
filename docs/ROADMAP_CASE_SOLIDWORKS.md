# Roadmap do case paramétrico no SolidWorks

O case precisa proteger a eletrônica sem transformar o calor interno ou a
recirculação do PMS em “medição ambiental”. O modelo final só deve começar após
congelar a PCB Rev A e medir todos os módulos/cabos.

## 1. Entregáveis

```text
hardware/case/rev_a/
  QAR_CASE_MASTER.SLDPRT
  QAR_BASE.SLDPRT
  QAR_TAMPA.SLDPRT
  QAR_DUTO_PMS.SLDPRT
  QAR_MONTAGEM.SLDASM
  QAR_BASE.stl
  QAR_TAMPA.stl
  QAR_DUTO_PMS.stl
  QAR_CASE_DRAWING.pdf
  README.md
```

Inclua STEP dos sólidos finais para interoperabilidade. STL é saída de impressão,
não deve ser a única fonte editável.

## 2. Levantamento dimensional

Meça com paquímetro e registre em `hardware/case/parametros.csv`:

- PCB: X/Y/espessura, furos e componentes mais altos por lado;
- ESP32: envelope, antena, USB, EN/BOOT e raio de curvatura do cabo;
- PMS7003: envelope, entrada, exaustão, conector e cabo conectado;
- sensores I2C: envelope, abertura sensível e conectores;
- módulo analógico: zonas quentes e ventilação;
- fixadores, insertos térmicos e tolerância real da impressora.

Fotografe cada medição. Não use apenas dimensões de marketplace.

## 3. Arquitetura de câmaras

```text
[entrada ambiente] -> câmara passiva SHT31/SGP40/SCD41 -> saídas passivas

[entrada PMS] -> PMS7003 (duto selado) -> exaustão externa

[eletrônica ESP32/LDO] -- divisória térmica -- [sensores]
[módulo analógico quente] em zona própria, sem soprar sobre SHT31/SCD41
```

- O PMS deve captar e devolver ar externo sem recircular para sua entrada.
- O SHT31 não deve ficar na pluma térmica do ESP32/LDO/MiCS.
- SCD41/SGP40 precisam trocar ar com o ambiente, mas não receber jato direto do
  PMS ou poeira concentrada.
- A antena deve ficar junto a uma parede não metálica, afastada de PCB/cabos.
- USB, alimentação, botão e conectores devem ser acessíveis sem abrir o case.

## 4. Variáveis globais iniciais

No SolidWorks: `Tools > Equations`, crie variáveis com nomes estáveis. Valores
abaixo são pontos de partida, não dimensões finais.

| Variável | Inicial | Uso |
|---|---:|---|
| `WALL` | 2.0 mm | parede FDM |
| `BASE_FLOOR` | 2.4 mm | piso |
| `CLEAR_XY` | 0.5 mm | folga por lado para PCB/módulo |
| `CLEAR_Z` | 1.0 mm | folga vertical mínima |
| `LID_GAP` | 0.30 mm | folga por lado do encaixe |
| `LIP_H` | 3.0 mm | altura do lábio |
| `LIP_T` | 1.2 mm | espessura do lábio |
| `BOSS_OD` | 7.0 mm | poste M3 |
| `INSERT_HOLE` | conforme inserto | nunca adivinhar |
| `VENT_D` | 4.0 mm | furos passivos |
| `VENT_PITCH` | 7.0 mm | passo da matriz |
| `DUCT_GAP` | 0.4 mm | folga por lado do duto |
| `FILLET_EXT` | 2.0 mm | aresta externa |

Ligue dimensões dos sketches às variáveis; evite números soltos em features.

## 5. Fluxo de modelagem no SolidWorks

### 5.1 Skeleton/master

1. Novo `Part`, unidades MMGS.
2. Sketch no Top Plane com envelopes da PCB, PMS, câmara passiva e conectores.
3. Use blocos/sketches nomeados: `ENV_PCB`, `ENV_PMS`, `KEEP_USB`,
   `KEEP_ANTENNA`, `AIR_IN`, `AIR_OUT`.
4. Importe DXF do contorno da PCB se disponível, confira escala e fixe a origem.
5. Crie planos para piso, topo da PCB e maior componente.

### 5.2 Base

1. `Extruded Boss/Base` do contorno externo.
2. `Shell` removendo a face superior, espessura `WALL`.
3. Recortes de USB/alimentação com `Extruded Cut`; adicione folga de cabo, não
   apenas a dimensão do conector.
4. Postes com `Boss-Extrude`; furos por `Hole Wizard` ou dimensão do inserto.
5. Nervuras com `Rib`, espessura 1,2–1,6 mm, evitando criar massas térmicas junto
   dos sensores.
6. Divisórias entre eletrônica, câmara passiva e módulo quente.
7. Filetes internos pequenos e externos `FILLET_EXT`.

### 5.3 Tampa

1. Derive o contorno da base ou use top-down assembly.
2. Crie lábio periférico com `LID_GAP`; não use encaixe perfeito de CAD.
3. Escolha fixação: parafuso + inserto é preferível para manutenção repetida;
   snap-fit exige corpo de prova de material/orientação.
4. Acrescente setas de fluxo, revisão e aviso “PROTÓTIPO” em baixo-relevo.

### 5.4 Duto PMS

1. Modele peça separada para permitir iteração.
2. Transições de seção suaves; evite degrau diante da entrada do sensor.
3. Duto de entrada e saída não podem se comunicar dentro do case.
4. Preveja vedação por espuma de célula fechada fina ou encaixe com folga.
5. Use geometria imprimível sem suporte interno impossível de remover.

### 5.5 Ventilação passiva

1. Faça um furo mestre e use `Linear Pattern`/`Fill Pattern`.
2. Área aberta inicial: 20–35% da face da câmara, depois validar.
3. Evite furos diretamente sobre componentes, gotas/poeira ou dedos.
4. Se usar tela/filtro, registre sua queda de pressão e manutenção.

## 6. Montagem e verificações CAD

1. Inserir base, tampa, PCB e envelopes dos módulos em `QAR_MONTAGEM.SLDASM`.
2. Aplicar mates somente suficientes; não “forçar” peça com conflito.
3. `Evaluate > Interference Detection` incluindo cabeças de parafuso e cabos.
4. `Clearance Verification` com folgas de montagem.
5. Verificar curso de conectar/desconectar USB e PMS.
6. Criar configurações `OPEN`, `CLOSED`, `NO_LID` e vista explodida.
7. Se houver SolidWorks Flow Simulation, use apenas como comparação entre
   variantes; resultados dependem das condições de contorno e precisam de
   ensaio físico.

## 7. DFM para impressão FDM

- Parede >=2 mm; quatro perímetros como ponto de partida.
- Folga XY típica 0,25–0,40 mm por lado, calibrada em cupom da impressora.
- Furos impressos saem menores: criar corpos de prova para insertos/parafusos.
- Evitar overhang >45° ou criar chanfro; orientar para não exigir suporte em duto.
- PETG/ASA costuma tolerar mais calor que PLA; escolher conforme ambiente e
  registrar material/lote/parâmetros.
- Não instalar inserto térmico perto de parede fina ou sensor sem corpo de prova.

## 8. Exportação

1. Executar `Rebuild` e resolver referências pendentes.
2. Salvar STEP AP214/AP242 e STL binário em milímetros.
3. STL com desvio aproximado 0,05 mm e ângulo 5° como início; inspecionar tamanho.
4. Abrir cada STL no fatiador e procurar paredes ausentes, normais e unidades.
5. Gerar desenho A3/A4 com dimensões críticas, materiais, tolerâncias, revisão e
   vista explodida; exportar PDF.

## 9. Protótipos e ensaio

### Protótipo 0 — cupons

Imprimir apenas encaixe da tampa, poste/inserto, conector USB e trecho de duto.
Corrigir tolerâncias antes de gastar uma impressão completa.

### Protótipo 1 — forma/encaixe

Imprimir em baixa qualidade, montar peças inertes e verificar cabos, parafusos,
botões, antena e manutenção.

### Protótipo 2 — térmico/fluxo

- Rodar conjunto por pelo menos 2 h em caixa aberta e fechada.
- Registrar SHT31 e termômetro de referência fora/dentro, posição e condições.
- Comparar PMS com entrada/saída livres e no duto.
- Testar diferentes orientações e velocidades externas sem fumaça/gás perigoso.
- Aceitar somente após definir limite de viés térmico e repetibilidade.

## 10. Checklist de liberação

- [ ] PCB e todos os módulos medidos; nenhum envelope “estimado”.
- [ ] Interferência e clearance aprovados com cabos e fixadores.
- [ ] Antena desobstruída.
- [ ] Entrada/saída PMS sem recirculação.
- [ ] Sensor térmico isolado das fontes de calor.
- [ ] Tampa removível e conectores acessíveis.
- [ ] Cupons de tolerância aprovados no material/impressora finais.
- [ ] Ensaio térmico/fluxo registrado e comparado à caixa aberta.
- [ ] SLDPRT/SLDASM/STEP/STL/desenho/README versionados com revisão.
