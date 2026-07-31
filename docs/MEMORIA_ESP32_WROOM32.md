# Orçamento de memória do ESP-WROOM-32

## Hipótese controlada

O ambiente foi configurado para um ESP-WROOM-32 com flash de **4 MB**, comum nos
DevKits de 30 pinos. Antes do primeiro upload, confirme a capacidade real com
`esptool.py flash_id`; clones podem usar outra flash. A compilação indica RAM
estática e tamanho do aplicativo, mas não mede o pico de heap durante Wi-Fi/TLS.

## Particionamento de 4 MB

Arquivo: [`../firmware/partitions_4mb_ota.csv`](../firmware/partitions_4mb_ota.csv).

| Região | Offset | Tamanho | Uso |
|---|---:|---:|---|
| NVS | `0x9000` | 20 KiB | configuração e estado pequeno |
| OTA data | `0xE000` | 8 KiB | seleção/rollback de imagem |
| app0 | `0x10000` | 1.536 KiB | firmware ativo |
| app1 | `0x190000` | 1.536 KiB | firmware OTA candidato |
| LittleFS | `0x310000` | 960 KiB | certificados/configuração futura |

As duas imagens OTA cabem porque o firmware atual está abaixo de 1 MiB. Uma
biblioteca nova só entra após confirmar que **ambas** as partições continuam com
margem; não trocar por partição “huge app” se rollback OTA fizer parte do escopo.

## Fontes de consumo em execução

- pilha TCP/IP, driver Wi-Fi e buffers do rádio;
- handshake TLS, cadeia X.509, certificado e chave privada;
- dois buffers do cliente MQTT e documento temporário do ArduinoJson;
- bibliotecas I²C e algoritmo Gas Index;
- pilhas de tarefas Arduino/FreeRTOS e buffers UART;
- fragmentação causada por alocações repetidas.

O firmware reduz risco com buffer MQTT/payload de 896 bytes, tópicos e ULIDs em
arrays fixos, payload global não reentrante, recusa de publicação abaixo de
30 KiB livres e telemetria de heap. O tamanho de 896 bytes é um limite do
dispositivo, muito menor que o limite do serviço AWS; um payload extremo
representativo mediu 747 bytes nesta revisão. Aumentar exige medir o
payload real e repetir teste TLS prolongado.

## Diagnóstico publicado

`metadata` inclui:

- `free_heap_bytes`;
- `min_free_heap_bytes` desde o boot;
- `max_alloc_heap_bytes` para detectar fragmentação;
- `uptime_s` e `reset_reason`;
- `board_model`, `hardware_revision` e `firmware_version`.

## Gates de memória

| Gate | Critério inicial |
|---|---|
| Build | cada imagem <= 75% do slot OTA de 1,5 MiB |
| RAM estática | <= 25% da RAM reportada pelo PlatformIO |
| Pós-handshake TLS | alvo >= 40 KiB; nunca cruzar o bloqueio de 30 KiB |
| Fragmentação | maior bloco alocável >= 32 KiB após 24 h |
| Payload | `measureJson < 896` e pelo menos 10% de margem em todos os estados |
| Soak | 24 h com Wi-Fi/TLS/reconexões, sem tendência de queda do heap mínimo |

Os valores de runtime são gates iniciais, não garantias universais. Se o
handshake do certificado real exigir mais memória, eleve o mínimo ou remova
funções; não silencie a proteção.

## Dados offline e desgaste

Hoje uma publicação que falha é contabilizada no log e não persiste a leitura.
Antes do piloto AWS, implementar fila limitada com versão/CRC e política de
descarte explícita. Preferir lote pequeno em LittleFS/NVS, limitar gravações e
testar perda de energia. Uma fila ilimitada em RAM não é aceitável; gravar a
cada amostra sem considerar desgaste também não é.

Certificados PEM em `secrets.h` servem apenas ao protótipo. Produção requer
credencial exclusiva, flash encryption/secure boot quando aplicável e processo
de rotação/revogação. Nunca colocar chave privada na telemetria ou nos logs.
