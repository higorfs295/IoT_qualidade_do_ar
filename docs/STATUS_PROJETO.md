# Status auditado da base

Data da auditoria: 31 de julho de 2026.

## O que foi verificado nesta revisão

| Verificação | Resultado |
|---|---|
| Inventário de arquivos e estado Git | concluído; `.env` local preservado e agora ignorado |
| Testes Python | 8/8 aprovados |
| Self-test do simulador HIL | aprovado em todos os cenários |
| Compilação Python | aprovada |
| Testes Node do contrato | 6/6 aprovados |
| Sintaxe Node/browser | aprovada |
| Backend HTTP real | ingestão, métricas, dispositivo, estático e CSP aprovados |
| Firmware `esp32-hil` | compilado; 46.984 B RAM, 785.569 B flash |
| Firmware `esp32-fisico` | compilado; 47.076 B RAM, 816.437 B flash |
| PDFs e planilha anteriores | encontrados com 0 bytes; substituídos por artefatos reais |

## Melhorias implementadas

- Validação consistente de ULID, IDs, timestamp, sequência, tipos, finitude,
  faixas plausíveis, `quality` e coerência tópico/payload em Python e Node.
- Testes automatizados para contrato, nulos/degradação, faixas e tópico.
- Backend protegido contra path traversal, corpo ilimitado, conteúdo incorreto,
  colisão de `device_id`, regressão de sequência e crescimento abrupto da
  deduplicação; ingestão HTTP desabilitável e token opcional.
- Dashboard com DOM seguro para IDs, reconexão sem multiplicar timers,
  prioridade correta para `UNSAFE`, responsividade e aviso de escopo.
- Dois builds de firmware, QoS 1 real, ULID canônico, `boot_id`, NTP obrigatório,
  reconexão não bloqueante e segredos fora do código versionado.
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
- Persistência do backend, app Flutter, AWS, arquivos EasyEDA e SolidWorks são
  entregas futuras guiadas pelos roadmaps; não são apresentados como prontos.
- Resultados de benchmark antigos permanecem como histórico em `ARQUITETURA.md`;
  devem ser reproduzidos na máquina-alvo antes de citação final.

## Definições de estado

- **Implementado e verificado:** teste ou build executado nesta revisão.
- **Implementado; requer bancada:** código compila, mas depende do hardware.
- **Especificado:** há requisitos e procedimento suficientes para produzir o
  artefato na ferramenta indicada.
- **Planejado:** arquitetura decidida, implementação ainda não iniciada.
