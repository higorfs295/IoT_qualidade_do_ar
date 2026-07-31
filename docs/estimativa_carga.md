# Estimativa de carga

Premissas editáveis na planilha `estimativa_carga.xlsx`:

- uma mensagem por dispositivo a cada 60 s;
- payload médio planejado de 470 bytes;
- pico de dimensionamento igual a 2 vezes a média;
- mês de 30 dias;
- valores abaixo usam GB decimal e não incluem TCP/TLS/MQTT, índices, réplicas,
  WAL, compressão, backups ou respostas de consulta.

## Fórmulas

```text
mensagens_por_segundo = dispositivos / intervalo_s
mensagens_por_dia = dispositivos * 86400 / intervalo_s
GB_por_dia = mensagens_por_dia * bytes_por_mensagem / 1e9
GB_por_mes = GB_por_dia * 30
```

## Cenários

| Dispositivos | Média msg/s | Pico 2× msg/s | Mensagens/dia | GB/dia | GB/30 dias |
|---:|---:|---:|---:|---:|---:|
| 5.000 | 83,33 | 166,67 | 7.200.000 | 3,384 | 101,52 |
| 10.000 | 166,67 | 333,33 | 14.400.000 | 6,768 | 203,04 |
| 50.000 | 833,33 | 1.666,67 | 72.000.000 | 33,840 | 1.015,20 |
| 100.000 | 1.666,67 | 3.333,33 | 144.000.000 | 67,680 | 2.030,40 |

## Como usar no dimensionamento

- Broker/consumidor: dimensionar pelo pico e testar rajadas/reconexões.
- Banco: somar overhead real medido, índices, réplica e margem de retenção.
- Data lake: medir compressão em amostra real antes de projetar custo.
- Rede do dispositivo: medir pacote no enlace; payload JSON não é o total.
- O cenário com “100 mil sensores” não implica necessariamente 100 mil conexões
  simultâneas na PoC: gateways virtuais multiplexam dispositivos para reproduzir
  taxa e formato sem fingir equivalência de conexões.
