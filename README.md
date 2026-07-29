# Atividade 3 - Planejamento da Arquitetura de Ingestão de Dados em IoT

## Descrição do projeto

Esse repositório contém a solução desenvolvida para a Atividade 3 da disciplina, cujo objetivo é propor e demonstrar uma arquitetura de Internet das Coisas capaz de receber, processar, armazenar e monitorar dados enviados por milhares de sensores.

O cenário considera o monitoramento da qualidade do ar, utilizando sensores para medir as seguintes variáveis:

- concentração de dióxido de carbono;
- compostos orgânicos voláteis totais;
- material particulado PM2.5;
- material particulado PM10;
- temperatura;
- umidade.

A solução contempla uma prova de conceito(PoC) local e um planejamento de implantação utilizando serviços da Amazon Web Services(AWS).

## Objetivos

- simular o envio simultâneo de mensagens por milhares de dispositivos IoT;
- definir uma estrutura padronizada para as mensagens;
- propor uma arquitetura escalável e tolerante a falhas;
- reduzir o risco de perda de mensagens;
- armazenar dados recentes e históricos;
- monitorar o funcionamento da solução;
- analisar aspectos de segurança, desempenho e custos.


## Arquitetura Proposta

Sensores IoT -> Broker Mosquitto(local) -> Fila Amazon SQS -> AWS Lambda -> Amazon DynamoDB e S3 -> Dashboard e monitoramento

[`Diagrama da arquitetura`](docs/arquitetura_solucao.pdf)
[`Documentação da arquitetura`](ARQUITETURA.md)


## Estrutura das mensagens


Exemplo de mensagem enviada pelos sensores: 

```json
{
  "payload_exemplo": {
    "schema_version": "1.0",
    "message_id": "01JQ7PK0P3R7V5BT7P0Q9YQ8A1",
    "device_id": "esp32-sala-01",
    "site_id": "campus-ufg-bloco-inf",
    "sent_at": "2026-07-27T14:20:00Z",
    "sequence": 428,
    "measurements": {
      "co2_ppm": 450,
      "tvoc_ppb": 100,
      "pm1_ugm3": 8.4,
      "pm25_ugm3": 15.0,
      "pm10_ugm3": 20.0,
      "temperature_c": 24.5,
      "humidity_pct": 50.0
    }
  }
}
```

## Tecnologias utilizadas

### PoC Local

- Python; 
- Paho MQTT 2.0+;
- MQTT;
- MQTT QoS 1;
- Eclipse Mosquitto;
- JSON;
- Docker;
- Docker Compose;
- CLI.

[`Documentação do PoC`](poc/README.md)


### Planejamento em nuvem

- AWS IoT Core;
- Amazon SQS + DLQ;
- AWS Lambda;
- Amazon DynamoDB;
- Amazon S3;
- Amazon API Gateway;
- Amazon CloudWatch;
- AWS IAM.

[`Documentação do planejamento AWS`](infra/aws/planejamento_servicos.md)


## Estimativa de Carga

Previsão do volume de dados gerado pelo sistema IoT considerando diferentes quantidades de sensores.

[`Estimativa de Carga`](docs/estimativa_carga.md)

## Slides da Apresentação

[`Apresentação`](docs/apresentacao_slides.pdf)


## Professor da matéria

IWENS GERVASIO SENE JUNIOR


## Participantes

- HIGOR FERREIRA SILVA;
- KHALIL ALVES MOTTA;
- LOURENÇO TABOSA PANIAGO;
- WILSON MARANHÃO RAMOS FILHO.

