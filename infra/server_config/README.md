# Infraestrutura Local — Broker e Plataforma

> Para instalar a aplicação completa, use o [`../../compose.yaml`](../../compose.yaml)
> da raiz ou `scripts/install.ps1`/`scripts/install.sh`. Este diretório permanece
> como configuração avançada do broker, benchmark e ThingsBoard opcional.

Automações para subir o ambiente que recebe a carga da PoC de ingestão
(Atividade 3). Reproduz localmente a borda da arquitetura de produção: onde o
plano da nuvem usa **AWS IoT Core**, aqui usamos um **Mosquitto** local; onde
usa **DynamoDB/S3 + dashboards**, aqui usamos **ThingsBoard CE + PostgreSQL**
(a plataforma definida na Atividade 1).

```text
infra/server_config/
├── docker-compose.yml            # Mosquitto + Sink + Gerador + ThingsBoard + PostgreSQL
├── setup_ubuntu_broker.sh        # provisiona um broker endurecido numa VM Ubuntu
├── gerar_certs.sh                # gera CA/certs de teste para o TLS 8883
├── .env.example                  # variáveis do compose
└── mosquitto/
    └── config/
        ├── mosquitto.conf        # configuração tunada do broker
        ├── aclfile.example       # modelo de ACL (menor privilégio)
        └── bridge.conf.example   # modelo de bridge borda→nuvem (AWS IoT Core)
```

> 📘 Visão completa da arquitetura, com cada serviço e parâmetro explicado, em
> [`../../ARQUITETURA.md`](../../ARQUITETURA.md) §10.

## Duas formas de subir o ambiente

Há dois caminhos, para dois propósitos:

1. **Docker Compose** — ambiente descartável na máquina do desenvolvedor, ideal
   para rodar a PoC e o ThingsBoard rapidamente.
2. **`setup_ubuntu_broker.sh`** — provisiona um broker **endurecido e ajustado**
   em uma VM Ubuntu, como seria um nó de borda real. É onde entram os ajustes de
   kernel e de limites para milhares de conexões.

---

## 1. Docker Compose

Pré-requisitos: Docker Engine + Docker Compose v2.

```bash
cp .env.example .env        # ajuste a senha do PostgreSQL se desejar

# Ambiente de ingestão pronto: broker + validador (sink) sempre observando
docker compose up -d mosquitto sink
docker compose logs -f sink                  # acompanhe a ingestão ao vivo

# Rodar um teste de carga conteinerizado, sob demanda (perfil "carga")
docker compose --profile carga run --rm gerador \
  ingestao_teste.py --host mosquitto --cenario 10000 --gateways 100 --duracao 120

# Broker + plataforma completa (mais pesado)
INSTALL_TB=true LOAD_DEMO=true docker compose --profile plataforma up -d
```

O uso de **perfis** é intencional: os testes de carga de milhares de sensores
precisam só do broker (+ o sink de observação). O ThingsBoard, que é pesado, e o
gerador ficam sob perfis próprios e só sobem quando você quer. Isso reduz o
consumo de recursos da máquina durante os experimentos de desempenho.

### Serviços

| Serviço | Imagem | Portas (host) | Papel | Perfil |
|---|---|---|---|---|
| `mosquitto` | `eclipse-mosquitto:2.0` | 1883, 8883 | broker MQTT (alvo do gerador) | núcleo |
| `sink` | build de `../../poc` | — | validador **sempre ativo** (assina e mede) | núcleo |
| `gerador` | build de `../../poc` | — | teste de carga **sob demanda** | `carga` |
| `postgres` | `postgres:16-alpine` | — | banco do ThingsBoard | `plataforma` |
| `thingsboard` | `thingsboard/tb-node:3.9.0` | 8080, 1884, 7070 | plataforma IoT (UI, alertas) | `plataforma` |

- Broker MQTT do projeto: **`localhost:1883`**.
- O **sink** é núcleo: subir o ambiente já o deixa validando a ingestão e
  detectando lacunas. Veja os números com `docker compose logs -f sink`.
- O **sink** e o **gerador** usam a **mesma imagem** (build do `poc/Dockerfile`)
  e só sobem depois que o Mosquitto está saudável.
- Interface do ThingsBoard: **http://localhost:8080** (credenciais padrão do
  ThingsBoard CE; troque no primeiro acesso).
- A porta MQTT do próprio ThingsBoard é mapeada em **1884** para não colidir com
  o Mosquitto em 1883.

### Primeira subida do ThingsBoard

Na primeira vez, o schema precisa ser instalado no PostgreSQL. Suba com
`INSTALL_TB=true` (e, se quiser dados de exemplo, `LOAD_DEMO=true`); depois volte
ambos para `false` no `.env` para não reinstalar a cada reinício. O
`depends_on: condition: service_healthy` garante que o ThingsBoard só sobe depois
que o PostgreSQL responde ao `pg_isready`.

### Verificação rápida

```bash
# Assinar toda a árvore do projeto (ferramentas do cliente Mosquitto)
docker exec -it qar-mosquitto mosquitto_sub -t 'qualidade-ar/#' -v

# Em outro terminal, do host: gerar carga
python ../../poc/ingestao_teste.py --host localhost --sensores 5000 --duracao 60
```

### Nota de fidelidade à arquitetura

O `docker-compose.yml` usa `postgres` e `thingsboard` como serviços **separados**,
espelhando a Atividade 1 (ThingsBoard CE **com** PostgreSQL). É a topologia mais
próxima de produção e a que a estimativa de custo original assume. Caso queira o
caminho de menor atrito para uma demonstração isolada, a imagem
`thingsboard/tb-postgres` embute o PostgreSQL em um único contêiner; a troca é
direta, mas perde a separação de responsabilidades entre banco e aplicação.

---

## 2. Provisionamento em VM Ubuntu — `setup_ubuntu_broker.sh`

Script **idempotente** (pode rodar novamente sem quebrar) que prepara um broker
Mosquitto de verdade, endurecido e ajustado para muitas conexões.

```bash
sudo ./setup_ubuntu_broker.sh                 # PoC: listener 1883 anônimo
sudo ./setup_ubuntu_broker.sh --auth          # exige usuário/senha + ACL
sudo ./setup_ubuntu_broker.sh --auth --tls    # também habilita TLS 8883
```

O que ele faz:

1. Instala `mosquitto`, `mosquitto-clients` e `openssl`.
2. **Ajuste de kernel e limites** para concorrência (o ponto central):
   - `fs.file-max`, `somaxconn`, `tcp_max_syn_backlog`, faixa de portas efêmeras;
   - `LimitNOFILE` do serviço elevado (padrão 200000) — cada conexão MQTT consome
     um descritor de arquivo, então esse teto define quantos sensores cabem.
3. Instala uma configuração tunada em `/etc/mosquitto/conf.d/qar-broker.conf`
   (mesmos parâmetros de desempenho do `mosquitto.conf` deste diretório).
4. Com `--auth`: cria usuário via `mosquitto_passwd` e uma **ACL de menor
   privilégio** — cada dispositivo só publica no próprio tópico, o ingestor só lê.
5. Com `--tls`: gera uma **CA de teste** e habilita o listener 8883.
6. Habilita e reinicia o serviço, validando ao final.

Variáveis úteis: `MQTT_USER`, `MQTT_PASSWORD`, `MAX_FDS`. Veja `--help`.

---

## 3. TLS e comunicação borda→nuvem

- **`gerar_certs.sh`** — gera uma CA e um certificado de servidor de **teste**
  em `mosquitto/config/certs/`, para habilitar o listener **8883 (TLS)** no
  Docker sem precisar da VM. Depois, descomente o bloco 8883 em `mosquitto.conf`
  e recrie o container. Teste com
  `--tls --tls-inseguro` no gerador/sink.

- **`mosquitto/config/bridge.conf.example`** — modelo de **bridge** (ponte): faz
  o broker local encaminhar `qualidade-ar/#` a um broker superior (regional ou
  **AWS IoT Core**). É a estratégia de comunicação distribuída que conecta esta
  PoC ao plano de nuvem: com `cleansession false`, a borda continua recebendo
  mesmo se o enlace com a nuvem cair, e reenvia depois.

---

## Ajuste de desempenho do broker

Os parâmetros de `mosquitto.conf` (e do script) foram escolhidos pensando em
milhares de conexões simultâneas e em rajadas:

| Parâmetro | Valor | Motivo |
|---|---|---|
| `max_connections` | -1 | sem teto artificial; o limite real é o `nofile` do SO |
| `max_inflight_messages` | 100 | vazão sob rajada mantendo QoS 1; casa com o cliente |
| `max_queued_messages` | 2000 | protege a memória quando um cliente fica lento |
| `queue_qos0_messages` | false | descarta o mais antigo, preservando o dado recente |
| `max_packet_size` | 8192 | contrato ocupa ~420 B; barra pacotes anômalos |
| `LimitNOFILE` (systemd) | 200000 | permite dezenas de milhares de conexões |

> Ao subir o Mosquitto com a config montada como somente leitura, o entrypoint
> da imagem imprime avisos `chown: ... Read-only file system`. São **inofensivos**
> (o broker sobe saudável) e resultado de proteger a config contra escrita.

## Segurança

- O listener **1883 anônimo** é apenas para PoC em rede isolada. Para expor o
  broker: habilite o listener 8883 (TLS), desabilite o anônimo e ative o arquivo
  de senhas + ACL (blocos comentados em `mosquitto.conf`; automatizados pelo
  `--auth`/`--tls` do script).
- Em produção, o padrão é **certificado por dispositivo (mTLS)** e política por
  `device_id`, coerente com o plano de AWS IoT Core em
  [`../aws/planejamento_servicos.md`](../aws/planejamento_servicos.md). A CA
  gerada pelo `--tls` é de **teste**; substitua por uma autoridade real.
- Nada de segredos no repositório: o `.gitignore` ignora `*.env`, `*.key`,
  `*.crt`, `*.pem`. Use o `.env` local (não versionado) e `aclfile` a partir do
  `aclfile.example`.
