# Roadmap do firmware e validação de sensores

## 1. Builds e configuração

| Ambiente | Fonte | Bibliotecas adicionais | Uso |
|---|---|---|---|
| `esp32-hil` | NDJSON na UART0/USB | nenhuma de sensor | integração e regressão |
| `esp32-fisico` | I2C, UART2 e ADC1 | SHT31, SCD4x, SGP40, Gas Index | bancada/protótipo |
| `esp32-aws` | sensores físicos | bibliotecas físicas + TLS/mTLS | IoT Core sandbox |

Passos:

1. Copiar `include/secrets.example.h` para `include/secrets.h`.
2. Configurar identidade, intervalos e pinos em `src/config.h`.
3. Compilar os três ambientes antes de qualquer release.
4. Confirmar flash física de 4 MB antes de usar a tabela OTA.
5. Nunca incluir `secrets.h`, certificados privados ou binários no commit.

## 2. Gate HIL

- Gravar `esp32-hil` e abrir a mesma porta com `central_sensores.py`.
- Confirmar que os logs do ESP32 aparecem no stderr do simulador.
- Verificar um payload de cada cenário no broker.
- Medir timeout: até 10 s `OK`, de 10 a 20 s degradado e após 20 s `ERROR`.
- Reiniciar o ESP32: `boot_id` deve mudar e `sequence` MQTT pode reiniciar sem
  deixar o backend preso em estado “reordenado”.
- Desligar NTP: o firmware não deve publicar timestamp 1970.

## 3. Bring-up físico por ordem de risco

### 3.1 Alimentação e I2C vazio

- Alimentar com fonte limitada a 100 mA, sem módulos, e procurar curto.
- Subir gradualmente o limite; medir 5 V e 3,3 V.
- Confirmar ausência de backfeed para USB.
- Rodar scanner I2C e medir SDA/SCL em repouso próximos de 3,3 V.

### 3.2 SHT31

- Conectar apenas o SHT31 e confirmar endereço `0x44`.
- Comparar por 30 min com termohigrômetro de referência.
- Critério inicial: erro médio documentado; não “corrigir” sem ensaio suficiente.

### 3.3 SGP40

- Confirmar self-test `0xD400`.
- Manter chamada em 1 Hz: o algoritmo VOC depende dessa cadência.
- Usar temperatura/umidade do SHT31 para compensação.
- Respeitar tempo de aprendizagem; não interpretar os primeiros minutos como
  concentração absoluta. `voc_index` é índice, não ppb.

### 3.4 SCD41

- Confirmar endereço `0x62`, número serial e medição pronta a cada ~5 s.
- Ensaiar ao ar livre de referência somente segundo procedimento do fabricante.
- Configurar altitude/pressão e offset térmico apenas após medir o case.
- Não executar recalibração forçada sem concentração de referência conhecida.

### 3.5 PMS7003

- Verificar conector/pinout do módulo comprado antes de energizar.
- Confirmar frames `0x42 0x4D`, comprimento 28 e checksum.
- Comparar os campos “atmospheric environment” usados pelo firmware.
- Testar orientação, entrada/saída e recirculação no case.

### 3.6 Canal MiCS

- Confirmar se a peça é sensor cru ou breakout condicionado; o circuito muda.
- Medir a saída com multímetro antes de ligá-la ao divisor/ADC.
- O firmware calcula média de 32 amostras e publica `gas_raw_v`.
- Manter `lpg_ppm=null` até obter curva do conjunto real com gás certificado,
  procedimento seguro, temperatura/umidade registradas e repetibilidade.

## 4. Robustez e memória

- Fila local de mensagens não publicadas em NVS/flash com limite e desgaste
  controlado; hoje falhas de publicação são observadas, não persistidas.
- Watchdog de tarefas e contadores de reset/brownout.
- Partições OTA/rollback já existem; faltam download, assinatura, confirmação
  de boot e rollback automático exercitados.
- mTLS direto já compila em `esp32-aws`; falta validar com certificado real e
  medir pico de heap do handshake.
- Provisionamento de identidade por dispositivo/frota sem claim permanente.
- Persistência opcional do estado do algoritmo VOC, conforme suporte oficial.
- Telemetria de heap, uptime e reset já existe; acrescentar tensão de alimentação
  e contador de falhas/reconexões.

Gates detalhados: [`MEMORIA_ESP32_WROOM32.md`](MEMORIA_ESP32_WROOM32.md).

## 5. Gate AWS

- Thing Name, `DEVICE_ID` e MQTT client ID idênticos.
- Atributo `siteId` igual ao `SITE_ID` e política sem wildcard de dispositivo.
- Endpoint ATS/porta 8883, CA, certificado e chave exclusivos.
- Publicação QoS 1, LWT/status e reconexão vistos no cliente de teste.
- Heap mínimo/maior bloco medidos antes/depois do handshake e após 24 h.
- Revogação do certificado impede reconexão; DLQ/alarme recebem falha induzida.
- Nenhum PEM, endpoint privado ou identificador de conta aparece no Git/log.

## 6. Critérios de release

- [ ] Os três ambientes compilam sem warning novo relevante.
- [ ] Teste HIL com quatro cenários e timeout aprovado.
- [ ] 24 h de execução física sem reset inesperado.
- [ ] Perda/reordenação explicadas em teste de Wi-Fi/broker.
- [ ] Todas as medições têm origem, unidade, precisão e estado documentados.
- [ ] Nenhum campo em ppm deriva de coeficiente “de exemplo”.
- [ ] Hash do firmware e configuração não secreta arquivados no relatório.
