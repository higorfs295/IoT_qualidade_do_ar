# Status auditado da base

Data de corte: 2 de agosto de 2026.

## Resultado executivo

A cadeia local está funcional: Mosquitto, demo, backend persistente, API/WS,
Web/PWA e app Flutter usam o mesmo contrato v1.1. O firmware possui três perfis
compilados para DevKit 30P USB-C com ESP-WROOM-32. A infraestrutura AWS está
codificada e empacotada, mas não foi aplicada a uma conta sem autorização de
custo/credenciais.

## Evidências reproduzidas

| Verificação | Resultado |
|---|---|
| Python | 13/13 testes; contrato, consumidor, CloudFormation e ZIP Lambda |
| Node/backend | 9/9 testes; API, CORS, segurança, PWA e restore |
| Flutter | 10/10 testes; `analyze` limpo; Web release e APK piloto |
| Android | minSdk 24, target/compile 36; APK V2 com certificado debug |
| Simulador | `--self-test` aprovado |
| Compose E2E | 2 devices, MQTT conectado/assinado, WS, série e 0 inválidas |
| Persistência | dois dispositivos e `last_saved_at` restaurados após restart |
| Firmware HIL | 50.608 B RAM; 788.553 B/slot (50,1%) |
| Firmware físico | 50.692 B RAM; 819.233 B/slot (52,1%) |
| Firmware AWS | 51.720 B RAM; 954.301 B/slot (60,7%) |
| AWS local | template validado; ZIP autocontido e determinístico |

## Estado por subsistema

- **Firmware 1.3.0:** HAL HIL/físico, NTP, ULID, boot/sequence, QoS 1, LWT,
  TLS/mTLS, watchdog, limites de heap/payload e fila offline fixa implementados.
- **Sensores:** drivers SHT31, SGP40, SCD41, PMS7003 e ADC GPIO34 compilam;
  operação e calibração ainda exigem bancada.
- **Backend 1.1.0:** contrato, deduplicação/lacunas, snapshot, REST/WS,
  Prometheus, CORS allowlist, heartbeat e readiness por assinatura concluídos.
- **Web/PWA:** Agora, Histórico, Alertas e Dispositivo completos, responsivos,
  live/demo/offline explícitos e shell instalável.
- **Mobile:** Android/iOS/Web, REST/WS, histórico, alertas, diagnóstico, pinout,
  temas e demo; APK piloto instalável localmente.
- **AWS:** IoT Rule, S3, SQS/DLQ, Lambda, DynamoDB, IAM, logs e alarmes em
  CloudFormation; deployment real continua bloqueado por decisão externa.
- **PCB/case:** BOM, netlist, regras, parâmetros e roteiros completos; arquivos
  nativos fabricáveis só podem ser fechados após medir as peças e revisar.

## Artefatos

| Arquivo | SHA-256 | Observação |
|---|---|---|
| `entrega/mobile/AirSense-piloto-1.0.0-release-debug-signed.apk` | `21862DAFDF4EFD277AB36C81C2FE8853D521FFA9F57D04D9B3A72726A03ADCEC` | piloto; assinatura debug |
| `entrega/aws/qar-lambda-ingest.zip` | `7ED1D4E4F27A4076C5132EEF4FB4809967928B2FCD3B4423C4BCF0299650A40D` | código Lambda autocontido |

## Gates externos honestamente abertos

1. confirmar flash/footprint/pinout e trazer sensores na bancada;
2. calibrar e caracterizar sem converter tensão MiCS em ppm fictício;
3. produzir e revisar projeto nativo EasyEDA Pro, ERC/DRC e PCB Rev A;
4. congelar dimensões, modelar SolidWorks e ensaiar fluxo/térmica;
5. instalar APK em aparelho real, testar acessibilidade e sessão prolongada;
6. aprovar orçamento/conta, aplicar change set AWS e testar mTLS/DLQ/revogação;
7. implementar/verificar OTA assinado antes de atualização remota.

“Compilado” e “testado localmente” não significam hardware, nuvem ou produto
certificado. Consulte [`RELATORIO_VERIFICACAO_FINAL.md`](RELATORIO_VERIFICACAO_FINAL.md)
e [`PLANO_TESTES.md`](PLANO_TESTES.md).
