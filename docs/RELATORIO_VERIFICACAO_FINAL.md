# Relatório de verificação final — Air Sense

**Data:** 2 de agosto de 2026  
**Alvo:** ESP-WROOM-32 DevKit 30P USB-C, software local, Flutter e AWS sandbox  
**Contrato:** telemetria v1.1; leitura compatível v1.0 no backend

## Conclusão

O repositório foi revisado de ponta a ponta e está próximo de uma entrega final
instalável dentro do que pode ser comprovado sem hardware montado e sem alterar
uma conta AWS. A instalação local funciona em Compose; firmware, backend, Web,
mobile e IaC compartilham tópico, identidade, campos e estados. Não foram
fabricados números de calibração, dimensões de PCB/case ou resultados de nuvem.

## Escopo auditado

Foram inspecionados código e configuração de `firmware`, `simulador`, `poc`,
`dashboard`, `mobile`, `infra`, `hardware`, `scripts`, `docs`, raiz/Compose e CI.
Também foram verificados os artefatos em `entrega` e os templates usados para a
apresentação final.

## Resultado por verificação

| Camada | Comando/evidência | Resultado |
|---|---|---|
| Python | `unittest discover -s poc/tests -v` | 13 aprovados |
| Python | `compileall` em PoC/simulador/scripts/Lambda | aprovado |
| HIL | `central_sensores.py --self-test` | aprovado |
| Node | `npm test` | 9 aprovados |
| Front web | `node --check` em JS/SW | aprovado |
| Compose | config + stack isolada + API/WS | aprovado |
| Restore | restart do backend | 2 devices e timestamp recuperados |
| Flutter | `analyze` | nenhuma ocorrência |
| Flutter | `test` | 10 aprovados |
| Flutter | build Web release | aprovado |
| Android | APK release piloto | aprovado; assinatura V2 debug |
| PlatformIO | HIL/físico/AWS | três SUCCESS |
| AWS local | template + empacotador | aprovado |

## Ajustes efetivados

### Firmware

- atualização para 1.3.0 e watchdog de 15 s;
- parser HIL descarta a linha inteira quando excede o buffer;
- fila offline circular e estática de três payloads, em ordem;
- descarte explícito do mais antigo e métricas de profundidade/perda;
- sequência só avança quando a mensagem foi enviada ou aceita na fila;
- compatibilidade do watchdog com a versão atual do ESP-IDF.

### Backend e Web

- API 1.1.0 com `/api/info`, campos históricos estritos e erros consistentes;
- CORS por allowlist, métodos 405, URLs malformadas protegidas e headers;
- readiness exige conexão e assinatura MQTT; métrica Prometheus correspondente;
- persistência restaura também a data do último snapshot;
- Web/PWA redesenhada em quatro telas, com histórico, alertas e diagnóstico;
- WebSocket com heartbeat e limite; demo/live/offline sempre diferenciados.

### Mobile

- projeto Flutter analisado, testado e compilado com o SDK Android fornecido;
- integração REST/WS, modo demo, histórico, alertas, hardware e configurações;
- APK piloto copiado para `entrega/mobile`, com limitação de assinatura descrita.

### Infraestrutura

- Compose configurável, persistente, com healthchecks e exposição local segura;
- CloudFormation com IoT Rule, S3 raw, SQS/DLQ, Lambda, DynamoDB, IAM,
  retenção de logs e alarmes;
- empacotador determinístico inclui `handler.py` e `qar_poc` no ZIP;
- CI cobre software, pacote AWS, firmware e mobile.

## Contrato entre componentes

```text
qualidade-ar/{site_id}/{device_id}/telemetria
  schema_version: 1.1
  message_id: ULID
  device_id/site_id: iguais ao tópico
  sent_at: RFC 3339 com fuso
  sequence + metadata.boot_id: ordem por inicialização
  measurements: nulo quando indisponível
  quality: SAFE/UNSAFE/UNKNOWN e OK/DEGRADED/ERROR
```

O firmware produz v1.1; Python, Node, Web e Flutter consomem a mesma semântica.
A Lambda reutiliza o validador Python e só atualiza o estado DynamoDB quando a
ordem ULID é mais nova. S3 guarda o evento bruto antes do consumidor.

## Limites e riscos residuais

- O segundo rótulo `VIN` informado é tratado como `VN/GPIO39 provável`; confirmar
  fisicamente antes de energizar.
- `lpg_ppm` permanece nulo até calibração rastreável do conjunto MiCS real.
- A fila offline em RAM não sobrevive a reset; persistência em flash exige ensaio
  de desgaste e perda de energia.
- Os dois slots preparam OTA, mas download/assinatura/rollback ainda não foram
  implementados e exercitados.
- O APK piloto usa certificado debug; publicação requer keystore privado,
  HTTPS/WSS, política de privacidade e testes em aparelhos.
- AWS gera custos e não foi implantada. Revisar change set, tags e orçamento.
- PCB/case dependem das dimensões reais; os roteiros não substituem ERC/DRC,
  revisão elétrica, interferência e ensaios térmicos/de fluxo.

## Reprodução rápida

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1
```

```bash
python -m unittest discover -s poc/tests -v
python simulador/central_sensores.py --self-test
cd dashboard/backend && npm test
cd ../../firmware && pio run -e esp32-hil -e esp32-fisico -e esp32-aws
cd ../mobile && flutter analyze && flutter test
```

## Artefatos e hashes

- APK: `21862DAFDF4EFD277AB36C81C2FE8853D521FFA9F57D04D9B3A72726A03ADCEC`
- Lambda ZIP: `7ED1D4E4F27A4076C5132EEF4FB4809967928B2FCD3B4423C4BCF0299650A40D`
- PPTX: `22CDD8F708BD138F99F33A5BB56D7E4A6FA35F02D0763F3CB1F730CFE935E607`
- PDF de arquitetura: `4AD7E0371744DF924934244EE3DA276652E7D70312C6393B00046AAEBBAE05F2`
- PDF de slides resumidos: `66714FF6968DD085D20B6C696E705E886C0136177DA0EC97B15A7C491A4CDD32`

A apresentação possui 11 slides editáveis em 4:3, segue a sequência do modelo
da disciplina, mantém a identidade visual azul, inclui notas com fontes e teve
renderização integral, zero overflow e fidelidade ao template aprovados.
