# Roadmap geral orientado por gates

O projeto avança por evidência. A base local e os artefatos de desenvolvimento
estão prontos; fabricação, calibração e nuvem real continuam condicionadas aos
recursos físicos e às credenciais do proprietário.

## Fase 0 — base reprodutível: concluída

- [x] Stack local com um pré-requisito: Docker Compose.
- [x] `.env.example`, segredos ignorados e configurador seguro do firmware.
- [x] Testes Python/Node, CI e builds HIL/físico/AWS.
- [x] Persistência, PWA, healthchecks, OpenAPI e métricas.
- [ ] Confirmar no módulo real 4 MB, variante, pinout de 30 pinos e se o segundo
  `VIN` é `VN/GPIO39`.

Saída de software cumprida: Compose construído e testado com restauração após
reinício. A última pendência desta fase é uma identificação física da placa.

## Fase 1 — integração HIL com ESP32 real

- [ ] Executar `scripts/install.ps1` ou `scripts/install.sh`.
- [ ] Gerar `secrets.h`, gravar `esp32-hil` e ligar a UART USB.
- [ ] Enviar `normal`, `pico_poluicao`, `incendio` e `vazamento_glp`.
- [ ] Confirmar ULID, sequência, `boot_id`, QoS 1, timestamps e WebSocket.
- [ ] Parar a central por mais que o timeout e confirmar degradação explícita.
- [ ] Derrubar Wi-Fi/broker e medir reconexão, lacunas e heap mínimo.

Saída: relatório com payloads e nenhuma divergência de contrato.

## Fase 2 — protótipo em bancada sem PCB

- [ ] Comprar módulos e guardar datasheets/pinouts exatos.
- [ ] Testar a fonte 5 V com carga antes de conectar o ESP32.
- [ ] Ligar um sensor por vez em protoboard ou chicote curto.
- [ ] Rodar scanner I²C, inspecionar frames PMS e medir tensão ADC.
- [ ] Comparar temperatura/umidade, CO₂ e PM com referências.
- [ ] Registrar aquecimento, estabilização, corrente e falhas.

Saída: cada sensor tem ficha de aceite; nenhuma conversão ppm é presumida.

## Fase 3 — esquemático e PCB Rev A no EasyEDA Pro

Procedimento completo: [`ROADMAP_HARDWARE_EASYEDA.md`](ROADMAP_HARDWARE_EASYEDA.md).

- [ ] Medir DevKit, módulos e conectores comprados.
- [ ] Confirmar pinos, straps, níveis lógicos e orçamento de corrente.
- [ ] Fechar alimentação sem backfeed USB e posição segura de `JP1`.
- [ ] Criar/revisar símbolos e footprints vinculados à BOM.
- [ ] Executar ERC, revisão por pares, placement, roteamento e DRC.
- [ ] Exportar Gerbers/Drill/BOM/Pick-and-Place e revisar no visualizador.
- [ ] Fabricar poucas unidades e fazer bring-up com fonte limitada.

Saída: Rev A funcional, pacote de fabricação arquivado e correções da Rev B.

## Fase 4 — case no SolidWorks

Procedimento completo: [`ROADMAP_CASE_SOLIDWORKS.md`](ROADMAP_CASE_SOLIDWORKS.md).

- [ ] Modelar envelopes medidos e PCB Rev A congelada.
- [ ] Separar câmaras térmicas e fluxos; impedir recirculação do PMS.
- [ ] Verificar interferências, fixação, USB, botões e manutenção.
- [ ] Produzir conjunto, desenho cotado, STL/3MF e STEP.
- [ ] Imprimir protótipo e comparar temperaturas com caixa aberta.
- [ ] Corrigir viés do SHT31, ruído, entrada de poeira e montagem.

Saída: case revisado com arquivos nativos e evidência de ensaio.

## Fase 5 — produto de demonstração prolongada

A demonstração local curta já possui persistência e PWA. Para operar por dias ou
com múltiplos usuários:

- [ ] PostgreSQL/TimescaleDB, migrações, retenção e backup/restauração.
- [ ] Autenticação, autorização, TLS e gestão de dispositivos.
- [ ] Alertas com histerese, auditoria e validação de falsos alarmes.
- [ ] Observabilidade externa e soak de 7 dias.
- [x] Cliente Flutter local com REST/WS, histórico, alertas e diagnóstico.
- [ ] Validar Flutter em aparelhos Android/iOS e preparar publicação.

Saída: release demonstrável por 7 dias sem intervenção manual.

## Fase 6 — sandbox AWS e frota

- [ ] Criar orçamento e alarmes de custo.
- [ ] Aplicar [`../infra/aws/`](../infra/aws/) em conta sandbox.
- [ ] Criar Thing/certificado por unidade e anexar menor privilégio.
- [ ] Gravar `esp32-aws`; validar mTLS, IoT Rule, SQS/DLQ, S3 e DynamoDB.
- [ ] Exercitar revogação, reprocessamento, logs e teardown.
- [ ] Implementar OTA assinada; a partição já possui dois slots, mas o cliente de
  atualização ainda não faz parte desta base.

Saída: uma unidade opera sem segredo no repositório e com recuperação ensaiada.

## Fase 7 — piloto e Rev B

- [ ] Instalar em local controlado, com aviso de protótipo.
- [ ] Operar 30 dias e acompanhar drift, disponibilidade e falsos alertas.
- [ ] Revisar ameaças, consumo, manutenção e custo total.
- [ ] Atualizar BOM, firmware, PCB, case e documentação.

Saída: decisão registrada de continuar, reprojetar ou encerrar.

## Caminho crítico

```text
stack local -> HIL no ESP32 -> bancada por sensor -> PCB Rev A -> case medido
                     |                |                 |
                     +-> persistência longa/AWS --------+-> piloto
```

Não modele o case final antes de congelar PCB e conectores. Não fabrique PCB
antes de confirmar pinout e corrente dos módulos. Não habilite alertas de
segurança antes de calibração e definição formal do uso pretendido.
