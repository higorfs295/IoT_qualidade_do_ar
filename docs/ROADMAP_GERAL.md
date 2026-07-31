# Roadmap geral orientado por gates

O projeto deve avançar por evidência, não apenas por calendário. Uma fase só
fecha quando seus critérios de saída estão registrados.

## Fase 0 — congelar a base de desenvolvimento

Objetivo: qualquer integrante reproduz os testes.

- [ ] Instalar Python 3.10+, Node 20+, PlatformIO e Docker Compose v2.
- [ ] Copiar os arquivos `.env.example`/`secrets.example.h`, sem versionar segredos.
- [ ] Executar testes Python/Node e builds HIL/físico/AWS.
- [ ] Confirmar no módulo real: 4 MB de flash, variante ESP-WROOM-32, pinout de
  30 pinos e se o segundo rótulo `VIN` é, na verdade, `VN/GPIO39`.
- [ ] Registrar versões de ferramentas e hash do commit no relatório de ensaio.

Saída: todos os comandos do README passam em uma segunda máquina.

## Fase 1 — integração HIL ponta a ponta

- [ ] Subir Mosquitto e backend.
- [ ] Gravar `esp32-hil` no ESP32.
- [ ] Enviar `normal`, `pico_poluicao`, `incendio` e `vazamento_glp` pela USB.
- [ ] Confirmar ULID, sequência, `boot_id`, QoS 1, timestamps e WebSocket.
- [ ] Parar o simulador por mais de 20 s e confirmar `ERROR/UNKNOWN`.
- [ ] Derrubar Wi-Fi/broker e medir reconexão e perda.

Saída: relatório com capturas, payloads e nenhuma divergência de contrato.

## Fase 2 — protótipo em bancada sem PCB

- [ ] Comprar módulos e confirmar datasheets/pinouts exatos.
- [ ] Testar fonte 5 V com carga eletrônica antes de conectar o ESP32.
- [ ] Ligar um sensor por vez em protoboard/chicote curto.
- [ ] Rodar I2C scanner, frames PMS e tensão ADC.
- [ ] Comparar temperatura/umidade, CO₂ e PM com referências.
- [ ] Registrar aquecimento, tempo de estabilização e falhas.

Saída: cada sensor tem ficha de aceite; nenhuma conversão ppm é presumida.

## Fase 3 — esquemático e PCB Rev A

Seguir [`ROADMAP_HARDWARE_EASYEDA.md`](ROADMAP_HARDWARE_EASYEDA.md).

- [ ] Medir o DevKit e conectores reais.
- [ ] Fechar arquitetura de alimentação sem backfeed USB e registrar a posição
  de `JP1` para modo USB ou modo autônomo.
- [ ] Criar/revisar símbolos e footprints.
- [ ] ERC, revisão por pares, layout, DRC e Gerbers.
- [ ] Fabricar poucas unidades e executar bring-up com fonte limitada.

Saída: uma Rev A funcional e uma lista de correções para Rev B.

## Fase 4 — case e ensaio térmico/fluxo

Seguir [`ROADMAP_CASE_SOLIDWORKS.md`](ROADMAP_CASE_SOLIDWORKS.md).

- [ ] Modelar envelopes medidos, dutos e câmaras separadas.
- [ ] Verificar interferências e acesso à manutenção.
- [ ] Imprimir protótipo, instalar termopares e comparar com caixa aberta.
- [ ] Corrigir recirculação do PMS e viés térmico do SHT31.

Saída: STL revisado, desenho cotado e fotos da montagem.

## Fase 5 — software persistente e produto de demonstração

- [ ] PostgreSQL/TimescaleDB, migrações e retenção.
- [ ] Autenticação, autorização, TLS e gestão de dispositivos.
- [ ] Histórico, alertas com histerese e auditoria.
- [ ] Flutter com as mesmas regras/contrato, sem duplicar limiares.
- [ ] Observabilidade e backup/restauração testados.

Saída: release demonstrável por 7 dias sem intervenção manual.

## Fase 6 — sandbox AWS e operação de frota

- [ ] Aplicar o template de [`../infra/aws/`](../infra/aws/) em conta sandbox.
- [ ] Criar um Thing/certificado por unidade e anexar política de menor privilégio.
- [ ] Gravar `esp32-aws`, validar mTLS, QoS 1, SQS/DLQ, S3 e estado idempotente.
- [ ] Exercitar expiração/revogação de certificado, reprocessamento da DLQ e
  alarmes de custo antes de aumentar a frota.
- [ ] Definir provisioning em escala e OTA; a tabela de partições já suporta
  duas imagens, mas o cliente de atualização ainda deve ser implementado.

Saída: uma unidade opera no sandbox sem segredo no repositório e com recuperação
documentada de falhas.

## Fase 7 — piloto e revisão final

- [ ] Instalar em local controlado, com consentimento e aviso de protótipo.
- [ ] Operar 30 dias, acompanhar drift, disponibilidade e falsos alertas.
- [ ] Revisar ameaças, consumo, manutenção e custo total.
- [ ] Atualizar BOM, firmware, case e documentação para Rev B.

Saída: decisão documentada de continuar, reprojetar ou encerrar o piloto.

## Dependências críticas

```text
HIL validado -> bancada por sensor -> esquemático -> PCB Rev A -> case medido
      |                                  |              |
      +-> backend persistente -----------+--------------+-> piloto
```

Não modele o case final antes de congelar PCB/conectores. Não fabrique PCB antes
de confirmar pinout e corrente dos módulos comprados. Não habilite alertas de
segurança antes de calibração, ensaios e definição formal do uso pretendido.
