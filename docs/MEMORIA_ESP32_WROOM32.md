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
arrays fixos, fila circular estática de três payloads, documento global não
reentrante, recusa de publicação abaixo de
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

A versão 1.3.0 mantém até três mensagens em uma fila circular fixa na RAM. Ela
preserva ordem e descarta a mais antiga ao lotar; profundidade e total descartado
são publicados em `metadata`. Isso absorve falhas curtas sem fragmentação, mas a
fila é perdida em reset/brownout. Antes do piloto AWS, avaliar persistência com
versão/CRC, lote pequeno em LittleFS/NVS, limite de gravações e teste de perda de
energia. Não ampliar indefinidamente a RAM nem gravar cada amostra sem medir
desgaste.

## Resultado de build de 02/08/2026

| Ambiente | RAM estática | Flash/slot OTA |
|---|---:|---:|
| `esp32-hil` | 50.608 B (15,4%) | 788.553 B (50,1%) |
| `esp32-fisico` | 50.692 B (15,5%) | 819.233 B (52,1%) |
| `esp32-aws` | 51.720 B (15,8%) | 954.301 B (60,7%) |

Os três passam o gate estático. Heap pós-handshake, fragmentação e soak continuam
dependentes do ESP32 e dos certificados reais.

Certificados PEM em `secrets.h` servem apenas ao protótipo. Produção requer
credencial exclusiva, flash encryption/secure boot quando aplicável e processo
de rotação/revogação. Nunca colocar chave privada na telemetria ou nos logs.
