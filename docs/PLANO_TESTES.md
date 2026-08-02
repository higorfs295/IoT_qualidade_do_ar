# Plano de testes e critérios de aceite

## Matriz mínima

| ID | Camada | Ensaio | Evidência | Aceite |
|---|---|---|---|---|
| INS-01 | instalação | Compose do zero | health/logs | MQTT conectado e >= 1 dispositivo |
| INS-02 | persistência | reiniciar backend | API antes/depois | dispositivos restaurados |
| SW-01 | Python | `unittest discover` | log | todos passam |
| SW-02 | Node | `npm test` | log | todos passam |
| SW-03 | API/PWA | processo real | respostas/headers | API, manifest, SW e métricas corretos |
| FW-01 | firmware | build HIL/físico/AWS | resumo PIO | três success; flash < 80% |
| FW-02 | memória | TLS + publicação/soak | heap mínimo/reset | heap >= 30 kB; sem reset |
| HIL-01 | serial | 4 cenários + timeout | payload/log | estado correto |
| NET-01 | MQTT | queda Wi-Fi/broker | sequência/métricas | reconecta; perdas contadas |
| API-01 | backend | válido, inválido, grande, duplicado | respostas/métricas | códigos corretos |
| ELE-01 | energia | curto, corrente, ripple, backfeed | fotos/medidas | dentro do orçamento |
| SEN-01 | sensores | comparação com referência | CSV/gráfico | erro documentado/aprovado |
| PCB-01 | placa | ERC/DRC + revisão | relatórios | zero erro não justificado |
| PIN-01 | placa alvo | pinout/flash/straps | fotos + `flash_id` | 30 pinos/4 MB confirmados |
| AWS-01 | nuvem | mTLS, regra, DLQ, revogação | logs/métricas | menor privilégio e recuperação |
| MEC-01 | case | interferência/temperatura/fluxo | desenho/ensaio | sem recirculação/viés excessivo |
| SYS-01 | sistema | soak 24 h e piloto 7 d | relatório | sem falha crítica |

## Suite automatizada atual

Na raiz do repositório:

```bash
python -m unittest discover -s poc/tests -v
python simulador/central_sensores.py --self-test
python -m compileall -q poc simulador scripts

cd dashboard/backend
npm ci
npm test
node --check src/server.js
cd ../..

docker compose config --quiet
docker compose build backend demo

cd firmware
pio run -e esp32-hil -e esp32-fisico -e esp32-aws
```

Base auditada em 2 de agosto de 2026: 11 testes Python, 9 testes Node e os três
ambientes PlatformIO aprovados. O workflow em `.github/workflows/ci.yml` repete
essas verificações em Linux.

## Aceite da instalação local

1. Remover apenas uma instalação de teste isolada ou escolher outro project name;
   nunca usar `down -v` sobre dados que devam ser preservados.
2. Executar `scripts/install.ps1` no Windows ou `scripts/install.sh` em POSIX.
3. Confirmar que o instalador só conclui com `ready`, MQTT e ao menos um device.
4. Abrir `http://localhost:3001`, verificar cartões e atualização em tempo real.
5. Consultar `/api/health`, `/api/metricas` e `/metrics`.
6. Reiniciar somente `backend`, aguardar health e confirmar devices restaurados.
7. Parar com `docker compose down`; subir novamente e confirmar o volume.

## Teste integrado MQTT

1. Subir broker, backend e gerador com 5 dispositivos e intervalo de 3 s.
2. Esperar duas janelas e registrar contadores iniciais.
3. Publicar fixture inválida e confirmar rejeição sem queda do processo.
4. Repetir o mesmo `message_id` e confirmar deduplicação.
5. Forçar sequência com lacuna e reordenação e confirmar contadores.
6. Derrubar broker por 30 s, religá-lo e verificar reconexão.
7. Reiniciar o backend e confirmar restauração limitada e íntegra.

## Teste elétrico Rev A

- Inspeção óptica e continuidade com placa desligada.
- Fonte 5 V limitada: começar em 50 mA sem módulos e aumentar por etapas.
- Medir 5 V/3,3 V em vazio e carga; registrar ripple no Wi-Fi/PMS.
- Conectar ESP32 sem sensores e depois um módulo por vez.
- Com `JP1` aberto, testar USB; com `JP1` fechado e USB desconectado, testar a
  fonte autônoma. Não unir as fontes sem power-path validado.
- Confirmar D21/D22/D16/D17/D34 até I²C/UART/ADC e ausência de uso dos straps
  GPIO0/2/5/12/15.
- Medir a tensão máxima do ADC antes de instalar o ESP32.

## Caracterização ambiental

- Registrar referência, localização, distância, cadência e estabilização.
- Usar pelo menos 30 min por ponto e repetir em dias diferentes.
- Separar exatidão, repetibilidade, drift e atraso de resposta.
- Não inferir conformidade de média temporal a partir de amostra isolada.
- Não gerar gases perigosos em ambiente improvisado; calibração de gás exige
  laboratório e procedimento apropriado.

## Registro e severidade

Cada ensaio guarda ID, data/fuso, responsável, commit, firmware, revisão de
hardware, instrumentos/calibração, condições, passos, dados brutos, esperado,
observado, fotos, anomalias e decisão.

- **Crítica:** risco elétrico, backfeed, superaquecimento, orientação indevida ou
  perda silenciosa de integridade. Bloqueia uso.
- **Alta:** contrato divergente, reset, corrupção, autenticação quebrada.
- **Média:** indisponibilidade recuperável, UI incorreta, desvio de desempenho.
- **Baixa:** texto, ergonomia ou acabamento sem impacto funcional.
