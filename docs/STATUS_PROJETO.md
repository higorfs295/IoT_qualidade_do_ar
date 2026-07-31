# Status auditado da base

Data da auditoria: 31 de julho de 2026.

## O que foi verificado nesta revisão

| Verificação | Resultado |
|---|---|
| Inventário de arquivos e estado Git | concluído; `.env` local preservado e agora ignorado |
| Testes Python | 11/11 aprovados, incluindo lote parcial do consumidor AWS |
| Self-test do simulador HIL | aprovado em todos os cenários |
| Compilação Python | aprovada |
| Testes Node do contrato | 6/6 aprovados |
| Sintaxe Node/browser | aprovada |
| Backend HTTP real | ingestão, métricas, dispositivo, estático e CSP aprovados |
| Firmware `esp32-hil` | compilado; 47.888 B RAM, 787.625 B/slot OTA |
| Firmware `esp32-fisico` | compilado; 47.996 B RAM, 818.353 B/slot OTA |
| Firmware `esp32-aws` | compilado; 49.024 B RAM, 953.429 B/slot OTA |
| Pinout ESP-WROOM-32 30P | GPIOs usados compatíveis; segundo VIN isolado como ambiguidade |
| Templates AWS | JSON válido; nenhum recurso de conta foi criado |
| PDFs finais | dossiê 10 páginas e apresentação 12 páginas; todas renderizadas e inspecionadas |

## Melhorias implementadas

- Validação consistente de ULID, IDs, timestamp, sequência, tipos, finitude,
  faixas plausíveis, `quality` e coerência tópico/payload em Python e Node.
- Testes automatizados para contrato, nulos/degradação, faixas e tópico.
- Backend protegido contra path traversal, corpo ilimitado, conteúdo incorreto,
  colisão de `device_id`, regressão de sequência e crescimento abrupto da
  deduplicação; ingestão HTTP desabilitável e token opcional.
- Dashboard com DOM seguro para IDs, reconexão sem multiplicar timers,
  prioridade correta para `UNSAFE`, responsividade e aviso de escopo.
- Três builds de firmware, QoS 1 real, ULID canônico, `boot_id`, NTP obrigatório,
  reconexão não bloqueante e segredos fora do código versionado.
- Tabela de partições 4 MB com dois slots OTA, buffers de 896 bytes, proteção de
  heap e diagnóstico de memória/reset na telemetria.
- Pinout 30P USB-C documentado, headers 1x15 corrigidos e jumper de alimentação
  que separa os modos USB, debug físico e autônomo.
- CloudFormation de sandbox, política IoT mínima, regra SQS/S3 e consumidor
  Lambda/DynamoDB com resposta parcial de lote.
- Fonte física implementada para SHT31, SGP40 + algoritmo VOC, SCD41, protocolo
  PMS7003 e ADC com média/calibração de tensão.
- Simulador passou a drenar a direção de logs da UART e validar argumentos.
- Documentação final, roadmaps, plano de testes, modelo de dados e artefatos.

## Limites que continuam exigindo mundo físico

- Nenhum sensor foi eletricamente conectado ou comparado a referência nesta
  execução; compilação não substitui bring-up.
- `lpg_ppm` fica `null` por projeto. O MiCS-5524 não entrega ppm pronto e a
  conversão depende do componente/breakout, circuito, gás, carga, temperatura e
  curva de calibração reais.
- Os limiares do dashboard são faixas operacionais do protótipo, não uma
  avaliação regulamentar instantânea. Diretrizes de PM normalmente usam médias
  temporais; uma amostra isolada não equivale a uma média de 24 horas.
- Persistência do backend, app Flutter, implantação AWS e arquivos nativos
  EasyEDA/SolidWorks ainda dependem de ambiente/ferramentas. Os templates AWS
  não foram aplicados a uma conta real nem geraram custo.
- Resultados de benchmark antigos permanecem como histórico em `ARQUITETURA.md`;
  devem ser reproduzidos na máquina-alvo antes de citação final.

## Definições de estado

- **Implementado e verificado:** teste ou build executado nesta revisão.
- **Implementado; requer bancada:** código compila, mas depende do hardware.
- **Especificado:** há requisitos e procedimento suficientes para produzir o
  artefato na ferramenta indicada.
- **Planejado:** arquitetura decidida, implementação ainda não iniciada.
