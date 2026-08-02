# Status auditado da base

Data da auditoria: 2 de agosto de 2026.

## Resultado executivo

A aplicação local está empacotada para uso em um comando: Mosquitto, gerador de
telemetria, backend persistente e dashboard/PWA. A stack foi construída e
testada em contêineres isolados, inclusive com reinício do backend e restauração
dos dados. O firmware possui três perfis compiláveis para o DevKit USB-C de 30
pinos com módulo ESP-WROOM-32.

O que não pode ser concluído apenas em software continua explicitamente
separado: montagem elétrica, calibração, fabricação da PCB, modelagem mecânica a
partir das peças medidas e aplicação dos recursos em uma conta AWS real.

## Evidências desta revisão

| Verificação | Resultado |
|---|---|
| Instalação local | Compose validado; broker, backend, PWA e demo sobem juntos |
| Smoke test em contêiner | MQTT conectado, múltiplos dispositivos, manifest/service worker e API aprovados |
| Persistência | snapshot atômico restaurado após reinício do backend |
| Testes Python | 11/11 aprovados, incluindo lote parcial do consumidor AWS |
| Self-test do simulador HIL | aprovado em todos os cenários |
| Compilação Python | aprovada para `poc`, `simulador` e `scripts` |
| Testes Node | 9/9 aprovados, incluindo persistência e processo HTTP real |
| Backend | ingestão, deduplicação, limites, health, Prometheus, PWA e shutdown aprovados |
| Firmware `esp32-hil` | 47.888 B RAM; 787.625 B/slot OTA (50,1%) |
| Firmware `esp32-fisico` | 47.996 B RAM; 818.353 B/slot OTA (52,0%) |
| Firmware `esp32-aws` | 49.024 B RAM; 953.429 B/slot OTA (60,6%) |
| Pinout ESP-WROOM-32 30P | GPIOs usados compatíveis; segundo `VIN` mantido como ambiguidade crítica |
| Templates AWS | JSON e componentes locais disponíveis; nenhum recurso de conta foi criado |
| CI | workflow para Python, Node, Compose/Docker e os três builds PlatformIO |
| Mobile Flutter | app Android/iOS/Web, análise estática, testes e build Web em modo demo |

## Funcionalidade entregue

- Instaladores PowerShell e POSIX criam a configuração local sem sobrescrever
  `.env`, constroem a stack e aguardam MQTT e dados antes de concluir.
- Compose limita a exposição a `127.0.0.1` por padrão, usa volumes persistentes,
  healthchecks, filesystem somente leitura e serviços reiniciáveis.
- Backend valida o contrato v1.1, tópico/payload, IDs, faixas e coerência; limita
  corpo, dispositivos, séries e janela de deduplicação.
- Persistência JSON versionada, limitada e atômica mantém o estado local entre
  reinícios sem exigir um banco externo.
- API REST, WebSocket, `/api/health`, `/api/metricas`, `/metrics` Prometheus e
  especificação OpenAPI estão disponíveis.
- Dashboard responsivo possui atualização em tempo real, estados textuais,
  proteção de DOM, reconexão e instalação PWA com shell offline.
- Aplicativo Flutter possui conexão configurável, REST/WebSocket com reconexão,
  histórico, alertas da sessão, diagnóstico do ESP32, temas e modo demonstração.
- Configurador de firmware gera `secrets.h` sem imprimir senhas e suporta MQTT
  local ou certificados AWS IoT Core.
- Firmware implementa QoS 1, ULID, `boot_id`, NTP obrigatório, reconexão não
  bloqueante, limites de buffer/heap e partições de 4 MB com dois slots OTA.
- Fonte física inclui SHT31, SGP40/algoritmo VOC, SCD41, PMS7003 e ADC calibrável.
- EasyEDA Pro e SolidWorks têm roadmaps com gates, BOM/netlist e critérios de
  fabricação e ensaio, sem fingir que arquivos nativos foram validados.

## Limites que continuam exigindo mundo físico ou conta externa

- Nenhum sensor foi conectado ou comparado a uma referência nesta execução;
  compilação não substitui bring-up nem calibração.
- `lpg_ppm` permanece `null`: o MiCS-5524 não fornece ppm diretamente e a curva
  depende do componente, breakout, circuito, gás e ensaio reais.
- O segundo rótulo `VIN` da placa informada é provavelmente `VN/GPIO39`, mas
  deve ser confirmado por foto, continuidade ou documentação do fabricante.
- A persistência local é apropriada a uma única instância e retenção curta.
  PostgreSQL/TimescaleDB continua recomendado para histórico longo, HA e frota.
- O app Flutter já cobre o uso em primeiro plano. Push em segundo plano, contas,
  alertas persistentes e publicação nas lojas continuam como evolução.
- CloudFormation e firmware AWS estão prontos para configuração, mas exigem
  conta, endpoint, certificados e custos autorizados pelo proprietário.
- EasyEDA Pro e SolidWorks exigem medidas das peças reais e revisão humana antes
  de fabricação; documentação textual não equivale a ERC/DRC ou interferência.
- O sistema é experimental, não é detector certificado nem deve orientar sozinho
  decisões de emergência ou conformidade ambiental.

## Definições de estado

- **Implementado e verificado:** teste, build ou smoke test executado.
- **Implementado; requer bancada:** código compila, mas depende do hardware.
- **Especificado:** há entradas, passos e critérios para produzir o artefato.
- **Planejado:** evolução não necessária para a instalação local atual.
