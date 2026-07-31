# Plano de testes e critérios de aceite

## Matriz mínima

| ID | Camada | Ensaio | Evidência | Aceite |
|---|---|---|---|---|
| SW-01 | Python | `unittest discover` | log | todos passam |
| SW-02 | Node | `npm test` | log | todos passam |
| FW-01 | firmware | build HIL/físico | resumo PIO | ambos success |
| HIL-01 | serial | 4 cenários + timeout | payload/log | estado correto |
| NET-01 | MQTT | queda Wi-Fi/broker | sequência/métricas | reconecta; perdas contadas |
| API-01 | backend | válido, inválido, grande, duplicado | respostas/métricas | códigos corretos |
| ELE-01 | energia | curto, corrente, ripple, backfeed | fotos/medidas | dentro do orçamento |
| SEN-01 | sensores | comparação com referência | CSV/gráfico | erro documentado/aprovado |
| PCB-01 | placa | ERC/DRC + revisão | relatórios | zero erro não justificado |
| MEC-01 | case | interferência/temperatura/fluxo | desenho/ensaio | sem recirculação/viés excessivo |
| SYS-01 | sistema | soak 24 h e piloto 7 d | relatório | sem falha crítica |

## Testes automatizados atuais

```bash
python -m unittest discover -s poc/tests -v
python simulador/central_sensores.py --self-test
python -m compileall -q poc simulador
cd dashboard/backend
npm test
node --check src/server.js
cd ../../firmware
pio run -e esp32-hil -e esp32-fisico
```

## Teste integrado local

1. Subir broker, backend e um gerador com 5 dispositivos/intervalo de 3 s.
2. Esperar duas janelas completas.
3. Conferir `recebidas`, `invalidas`, `duplicadas`, `lacunas` e `reordenadas`.
4. Publicar fixture inválido e confirmar rejeição.
5. Repetir o mesmo `message_id` e confirmar deduplicação.
6. Derrubar broker por 30 s, religá-lo e explicar qualquer lacuna observada.

## Teste elétrico Rev A

- Inspeção óptica e continuidade com placa desligada.
- Fonte 5 V limitada: 50 mA sem módulos, depois aumento por etapas.
- Medir 5 V/3,3 V em vazio e carga; registrar ripple no Wi-Fi/PMS.
- Conectar ESP32 sem sensores, depois um módulo por vez.
- Testar USB + fonte externa simultaneamente e confirmar ausência de corrente
  regressando para a porta do computador.
- Medir tensão máxima do ADC antes de instalar o ESP32.

## Caracterização ambiental

- Registrar referência, localização, distância, cadência e tempo de estabilização.
- Usar pelo menos 30 min por ponto e repetir em dias diferentes.
- Separar precisão, repetibilidade, drift e atraso de resposta.
- Para PM/CO₂, não inferir conformidade de uma média temporal a partir de uma
  amostra isolada.
- Não gerar gases perigosos em ambiente improvisado. Calibração de gás exige
  laboratório/procedimento apropriado.

## Modelo de registro

Cada ensaio deve guardar: ID, data/hora/fuso, responsável, commit, firmware,
hardware/revisão, instrumentos e calibração, condições, passos, dados brutos,
resultado esperado/observado, fotos, anomalias e decisão.

## Severidade

- **Crítica:** risco elétrico, backfeed, superaquecimento, instrução de segurança
  indevida, perda silenciosa de integridade. Bloqueia uso.
- **Alta:** contrato divergente, reset, dado corrompido, autenticação quebrada.
- **Média:** indisponibilidade recuperável, UI incorreta, desvio de desempenho.
- **Baixa:** texto, ergonomia ou acabamento sem impacto funcional.
