# Air Sense — estação IoT de qualidade do ar

Projeto integrado para monitorar CO₂, partículas, VOC, temperatura e umidade
com um **ESP32 DevKit USB-C de 30 pinos equipado com ESP-WROOM-32**. A base
inclui firmware HIL/físico/AWS, simulador, MQTT, backend, dashboard web/PWA,
aplicativo Flutter, infraestrutura local e CloudFormation para AWS.

> **Segurança:** é um protótipo acadêmico/experimental. Não substitui detector
> certificado de gás, fumaça ou incêndio, instrumento calibrado, alarme
> regulamentar ou orientação profissional. O MiCS-5524 publica `gas_raw_v`;
> `lpg_ppm` permanece nulo até existir calibração rastreável do conjunto real.

## Comece por aqui

Para executar a solução local completa, instale Docker Desktop/Engine com
Compose e rode:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1
```

Em Linux/macOS:

```bash
sh ./scripts/install.sh
```

O instalador cria `.env` a partir de `.env.example`, constrói as imagens e só
conclui depois que broker, backend e dispositivos demonstrativos aparecem na
API. Abra **http://localhost:3001**.

Execução manual equivalente:

```bash
cp .env.example .env
docker compose up -d --build
docker compose ps
docker compose logs -f backend demo
```

Por padrão, MQTT e dashboard escutam apenas em `127.0.0.1`. Para conectar um
ESP32 ou celular da LAN, use `BIND_ADDRESS=0.0.0.0`, libere somente a rede local
no firewall e configure o IP do computador no dispositivo/app. O listener 1883
anônimo é destinado exclusivamente a laboratório isolado.

## Entregáveis prontos

| Área | Resultado atual |
|---|---|
| Firmware | HIL, sensores físicos e AWS TLS/mTLS compilados para ESP-WROOM-32; watchdog e fila offline fixa |
| Sensores | SHT31, SGP40, SCD41, PMS7003 e canal ADC GPIO34 implementados; validação elétrica ainda exige bancada |
| Backend | MQTT QoS 1, contrato v1.1, deduplicação, lacunas, persistência atômica, REST, WebSocket e Prometheus |
| Web/PWA | telas Agora, Histórico, Alertas e Dispositivo; live, demo identificada, offline shell e layout responsivo |
| Mobile | Flutter Android/iOS/Web com REST, WebSocket, histórico, alertas, diagnóstico, pinout e modo demo |
| Infra local | Compose com Mosquitto, backend, dashboard e gerador; restauração após reinício validada |
| AWS | CloudFormation com IoT Rule, SQS/DLQ, Lambda, S3, DynamoDB, IAM, logs e alarmes; pacote Lambda gerado |
| Hardware | pinout, BOM, netlist, regras e roteiro EasyEDA Pro; fabricação depende das medições físicas |
| Case | parâmetros e roteiro SolidWorks; CAD nativo depende da PCB congelada e de dimensões medidas |

Entregáveis instaláveis e relatório estão em [`entrega/`](entrega/). O APK de
piloto usa assinatura de depuração e **não deve ser enviado à Play Store**.
A apresentação final editável está em
[`entrega/Apresentacao_Final_Air_Sense.pptx`](entrega/Apresentacao_Final_Air_Sense.pptx).

## Evidências da revisão final

Auditoria executada em 2 de agosto de 2026:

- 13 testes Python aprovados, incluindo contrato, Lambda e pacote AWS;
- 9 testes Node aprovados, com API, CORS, PWA e persistência após reinício;
- 10 testes Flutter aprovados e `flutter analyze` sem ocorrência;
- Flutter Web release e APK Android release de piloto gerados;
- três builds PlatformIO aprovados;
- Compose validado e pilha isolada exercitada com 2 dispositivos, WebSocket,
  séries, zero mensagens inválidas e restauração do snapshot;
- simulador HIL aprovado no `--self-test`;
- JSON/XML/links locais e artefatos estruturados verificados.

Tamanhos do firmware por slot OTA de 1.572.864 bytes:

| Ambiente | RAM | Flash/slot |
|---|---:|---:|
| `esp32-hil` | 50.608 B (15,4%) | 788.553 B (50,1%) |
| `esp32-fisico` | 50.692 B (15,5%) | 819.233 B (52,1%) |
| `esp32-aws` | 51.720 B (15,8%) | 954.301 B (60,7%) |

O relatório completo separa “testado”, “compilado” e “dependente do mundo
físico/conta externa”: [`docs/RELATORIO_VERIFICACAO_FINAL.md`](docs/RELATORIO_VERIFICACAO_FINAL.md).

## Arquitetura

```text
Central HIL (PC) --NDJSON/USB--┐
                              ├─> ESP32/HAL ─> MQTT QoS 1 ─> Mosquitto
Sensores I²C/UART/ADC --------┘                         │
                                                       ├─> backend ─> Web/PWA
                                                       │            └─> Flutter
                                                       └─> AWS IoT Core (mTLS)
                                                            └─> Rule ─> SQS ─> Lambda ─> DynamoDB
                                                                    ├─> DLQ
                                                                    └─> S3 bruto
```

O padrão HAL/Strategy mantém a aplicação independente da fonte. Os ambientes
`esp32-hil`, `esp32-fisico` e `esp32-aws` produzem o mesmo contrato v1.1.

## Firmware ESP-WROOM-32

Gere `firmware/include/secrets.h` sem colocar credenciais no Git:

```bash
python scripts/configure_firmware.py --ssid MINHA_REDE \
  --mqtt-host 192.168.1.10 --device-id esp32-sala-01 --site-id campus-ufg
```

Compile e grave:

```bash
cd firmware
pio run -e esp32-hil
pio run -e esp32-fisico
pio run -e esp32-aws
pio run -e esp32-hil -t upload
```

Teste HIL por USB:

```bash
python ../simulador/central_sensores.py --porta COM5 --cenario auto
```

Características de robustez: NTP obrigatório, ULID, `boot_id`, sequência por
boot, QoS 1, LWT, TLS/mTLS, gate de heap, payload máximo de 896 bytes, watchdog
de 15 s, parser serial limitado e fila offline circular de três mensagens. Se a
fila encher, a mais antiga é descartada e o total fica em
`metadata.offline_dropped_total`.

Pinagem usada:

| Função | Serigrafia | GPIO |
|---|---|---:|
| I²C SDA/SCL | D21/D22 | 21/22 |
| PMS7003 RX/TX do ESP32 | D16/D17 | 16/17 |
| MiCS ADC | D34 | 34/ADC1_CH6 |
| HIL/upload/log | RX0/TX0 | 3/1 |

O segundo `VIN` informado na placa é tratado como **VN/GPIO39 provável** e não
pode receber alimentação sem confirmação por continuidade. Veja
[`docs/PINOUT_ESP32_WROOM32_30P.md`](docs/PINOUT_ESP32_WROOM32_30P.md) e
[`firmware/README.md`](firmware/README.md).

## Dashboard e API

Desenvolvimento sem Docker:

```bash
cd dashboard/backend
npm ci
MQTT_ENABLED=false ENABLE_HTTP_INGEST=true DATA_DIR=./data npm start
```

Recursos principais:

| Recurso | Uso |
|---|---|
| `GET /api/health` | processo, MQTT/assinatura e persistência |
| `GET /api/info` | versão da API, schemas e campos históricos |
| `GET /api/dispositivos` | dispositivos e último estado |
| `GET /api/dispositivos/:id/serie` | série limitada por grandeza |
| `GET /api/metricas` / `GET /metrics` | métricas JSON/Prometheus |
| `WS /ws` | telemetria em tempo real |
| `POST /api/ingest` | somente desenvolvimento, desabilitado no Compose de produção |

Para Flutter Web em outra origem, configure `CORS_ORIGINS` como lista explícita
separada por vírgulas. A especificação está em [`docs/openapi.yaml`](docs/openapi.yaml).

## Aplicativo mobile

O APK piloto está em
[`entrega/mobile/AirSense-piloto-1.0.0-release-debug-signed.apk`](entrega/mobile/AirSense-piloto-1.0.0-release-debug-signed.apk).
Na primeira abertura, informe:

- emulador Android: `http://10.0.2.2:3001`;
- aparelho físico: `http://IP_DO_COMPUTADOR:3001`;
- Web/iOS Simulator: `http://localhost:3001`.

Para desenvolver:

```bash
cd mobile
flutter pub get
flutter analyze
flutter test
flutter build apk --release
flutter build web --release
```

O release local usa a chave debug quando `android/key.properties` não existe.
Para distribuição, use keystore privado e backend HTTPS/WSS. Detalhes em
[`mobile/README.md`](mobile/README.md).

## AWS

O firmware `esp32-aws` conecta diretamente ao endpoint ATS com certificado por
Thing. A infraestrutura reproduzível está em
[`infra/aws/sandbox.template.json`](infra/aws/sandbox.template.json), e o ZIP do
consumidor em [`entrega/aws/qar-lambda-ingest.zip`](entrega/aws/qar-lambda-ingest.zip).

O projeto **não cria recursos automaticamente**: conta, região, orçamento,
bucket de artefatos e aprovação de custo precisam ser escolhidos pelo responsável.
Passo a passo: [`infra/aws/lambda_ingest/README.md`](infra/aws/lambda_ingest/README.md).

## Hardware e case

Não foram fabricados arquivos EasyEDA/SolidWorks “de aparência pronta” porque
o footprint do DevKit, o conector PMS7003 e o envelope mecânico ainda dependem
das peças físicas. Inventar essas dimensões tornaria a placa/case incorretos.
Estão prontos:

- [`docs/ROADMAP_HARDWARE_EASYEDA.md`](docs/ROADMAP_HARDWARE_EASYEDA.md): esquemático, bibliotecas, PCB, DRC e fabricação;
- [`hardware/pcb/`](hardware/pcb/): BOM, netlist, regras, pinout e checklist;
- [`docs/ROADMAP_CASE_SOLIDWORKS.md`](docs/ROADMAP_CASE_SOLIDWORKS.md): skeleton, base, tampa, dutos, DFM e ensaios;
- [`hardware/case/parametros.csv`](hardware/case/parametros.csv): dimensões a medir antes do CAD.

## Estrutura

```text
firmware/       firmware ESP32 HIL/físico/AWS
simulador/      central virtual de sensores por USB
poc/            gerador de carga, contrato e sink Python
dashboard/      backend Node e Web/PWA
mobile/         aplicativo Flutter Android/iOS/Web
infra/          Mosquitto/ThingsBoard e CloudFormation AWS
hardware/       especificações de PCB e case
scripts/        instalação e configuração segura
docs/           contrato, testes, roadmaps, status e relatórios
entrega/        APK, pacote Lambda e apresentação final
```

## Documentação essencial

- [`docs/STATUS_PROJETO.md`](docs/STATUS_PROJETO.md) — estado por componente;
- [`docs/PLANO_TESTES.md`](docs/PLANO_TESTES.md) — matriz e critérios de aceite;
- [`docs/CONTRATO_TELEMETRIA.md`](docs/CONTRATO_TELEMETRIA.md) — contrato v1.1;
- [`docs/ROADMAP_GERAL.md`](docs/ROADMAP_GERAL.md) — caminho crítico até o piloto;
- [`docs/ROADMAP_FIRMWARE.md`](docs/ROADMAP_FIRMWARE.md) — bancada, calibração e release;
- [`docs/ROADMAP_SOFTWARE.md`](docs/ROADMAP_SOFTWARE.md) — backend, web, mobile e AWS;
- [`docs/MEMORIA_ESP32_WROOM32.md`](docs/MEMORIA_ESP32_WROOM32.md) — flash/heap/OTA;
- [`ARQUITETURA.md`](ARQUITETURA.md) — arquitetura distribuída e histórico da PoC;
- [`BASE_FINAL.md`](BASE_FINAL.md) — blueprint consolidado do produto.

## O que ainda exige validação externa

Software compilado não equivale a produto físico certificado. A conclusão do
protótipo requer: confirmar a placa de 4 MB e o footprint 1:1, revisar
esquemático por segunda pessoa, ERC/DRC, testar alimentação sob pico, trazer
sensores um a um, calibrar/compare com referências, validar o case térmico e de
fluxo, instalar APK em aparelho real e executar o sandbox AWS com orçamento e
certificado autorizados. Os gates estão no plano de testes.

## Contexto

Projeto acadêmico da UFG para a disciplina de Internet das Coisas. A base
separa explicitamente resultado automatizado, compilação, validação local,
teste físico e implantação em nuvem para evitar alegações além das evidências.
