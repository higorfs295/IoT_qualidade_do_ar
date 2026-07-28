# Estimativa de carga - fonte de calculo

A frequencia de 60 segundos representa a operacao planejada; a frequencia de cinco segundos usada na simulacao MQTT da Atividade 2 nao e usada para dimensionar producao.

## Premissas

| Parametro | Valor | Observacao |
|---|---:|---|
| Intervalo de envio | 60 s | uma leitura consolidada por sensor por minuto |
| Mensagens por sensor/dia | 1.440 | `86.400 / 60` |
| Payload para planejamento | 470 bytes | o exemplo JSON serializado ocupa 419 bytes; a reserva cobre crescimento de campos |
| Sobrecarga MQTT/TLS estimada | 70 bytes | margem de planejamento; o valor real deve ser medido no teste de carga |
| Tamanho trafegado por mensagem | 540 bytes | `470 + 70` |
| Margem de pico | 2x | reconexoes e sincronizacao de relogios podem concentrar envios |
| Periodo mensal | 30 dias | usado somente para comparacao de cenarios |

## Formulas

```text
mensagens_dia            = sensores * 1.440
mensagens_por_segundo    = sensores / 60
pico_mensagens_por_seg   = mensagens_por_segundo * 2
trafego_dia_bytes        = mensagens_dia * 540
telemetria_bruta_dia     = mensagens_dia * 470
```

Os volumes usam GB/TB decimais (1 GB = 1.000.000.000 bytes), adequados para comparacao de custo e trafego. A coluna de JSON bruto representa somente o payload antes de compressao/Parquet; o volume real no S3 pode diminuir apos a conversao.

## Cenários

| Sensores | Mensagens/dia | Média (msg/s) | Pico planejado (msg/s) | Tráfego de entrada/dia | JSON bruto/dia | Tráfego de entrada/mês | JSON bruto/ano |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 5.000 | 7.200.000 | 83,33 | 166,67 | 3,89 GB | 3,38 GB | 116,64 GB | 1,24 TB |
| 10.000 | 14.400.000 | 166,67 | 333,33 | 7,78 GB | 6,77 GB | 233,28 GB | 2,47 TB |
| 50.000 | 72.000.000 | 833,33 | 1.666,67 | 38,88 GB | 33,84 GB | 1,17 TB | 12,35 TB |
| 100.000 | 144.000.000 | 1.666,67 | 3.333,33 | 77,76 GB | 67,68 GB | 2,33 TB | 24,71 TB |

No maior cenário, um lote Lambda de 100 mensagens requer aproximadamente 17 invocações por segundo em média e 34 no pico, sem considerar reprocessamentos. O teste de carga deve confirmar tamanho de mensagem, percentual de mensagens inválidas, tempo de processamento e a distribuição real dos picos.
