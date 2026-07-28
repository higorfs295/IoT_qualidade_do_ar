1. Como garantir a escalabilidade da solução?

A escalabilidade será garantida por uma arquitetura baseada em serviços gerenciados e desacoplados da AWS. O AWS IoT Core receberá as conexões MQTT dos dispositivos, enquanto a Amazon SQS armazenará temporariamente as mensagens e absorverá picos de envio. A AWS Lambda processará os dados sob demanda e em lotes, sem a necessidade de manter servidores permanentemente ativos. O DynamoDB será utilizado para consultas rápidas, e o Amazon S3 armazenará o histórico de grande volume.

2. Como evitar a perda de mensagens?

A prevenção da perda de mensagens será realizada em diferentes etapas do fluxo. Os dispositivos utilizarão MQTT com QoS 1, o que garante que cada mensagem seja entregue pelo menos uma vez. Depois de recebida pelo AWS IoT Core, a mensagem será encaminhada para a SQS, onde permanecerá armazenada até que a Lambda conclua seu processamento. Caso ocorra uma falha temporária, a mensagem poderá ser processada novamente. Se as tentativas ultrapassarem o limite configurado, ela será enviada para uma fila de mensagens com falha, chamada DLQ, permitindo investigação e reprocessamento posterior.

3. Como armazenar grandes volumes de dados?

O armazenamento será dividido entre o DynamoDB e o Amazon S3, conforme a finalidade dos dados. O DynamoDB armazenará apenas as informações necessárias para consultas rápidas, como a última leitura de cada dispositivo e os agregados horários. O item que representa o estado atual será sobrescrito sempre que uma nova leitura chegar, evitando o acúmulo de todas as mensagens brutas no banco operacional. Os agregados poderão ser removidos automaticamente após 90 dias por meio de TTL. Já o Amazon S3 armazenará as mensagens JSON originais e o histórico convertido para o formato Parquet, particionado por ano, mês, dia, hora e local. Os dados antigos poderão ser movidos para classes de armazenamento mais econômicas, como o Glacier, e excluídos conforme a política de retenção de 5 anos.

4. Qual banco de dados foi escolhido e por quê?

O banco de dados operacional escolhido foi o Amazon DynamoDB, pois ele permite armazenar e consultar rapidamente o estado atual dos dispositivos e os agregados recentes. Esse tipo de acesso é adequado a um dashboard, que precisa localizar a leitura mais recente de um sensor sem pesquisar todo o histórico. O Amazon S3 complementará o DynamoDB, mas não exercerá a mesma função: ele será utilizado como armazenamento de objetos para o histórico bruto e analítico de longo prazo. Assim, a solução utiliza o DynamoDB para dados operacionais e o S3 para grandes volumes históricos.

5. Como monitorar a solução?

O monitoramento será realizado principalmente pelo Amazon CloudWatch, que centralizará métricas, logs e alarmes dos serviços. No AWS IoT Core, serão observados o número de conexões, as mensagens recebidas e as mensagens rejeitadas. Na SQS, serão monitoradas a quantidade de mensagens acumuladas, a idade da mensagem mais antiga e o número de mensagens enviadas para a DLQ. Na Lambda, serão acompanhados erros, duração das execuções e limitações de concorrência. No DynamoDB, serão avaliados a latência e o consumo de capacidade. Os logs deverão registrar identificadores como message_id, device_id e código da falha, sem expor credenciais ou conteúdos sensíveis completos. Alarmes poderão ser acionados quando houver acúmulo na fila, falhas repetidas ou mensagens rejeitadas.

6. Como reduzir os custos na nuvem?

A redução de custos será obtida pelo uso de serviços serverless e por políticas de armazenamento adequadas. A Lambda será executada apenas quando existirem mensagens para processar, evitando a manutenção de servidores permanentemente ligados. O processamento em lotes reduzirá a quantidade de invocações individuais. No DynamoDB, serão mantidos apenas o estado atual e os agregados recentes, com TTL para remover automaticamente dados antigos. O histórico completo ficará no S3, onde os arquivos poderão ser convertidos para Parquet, reduzindo espaço e custo de leitura. Políticas de ciclo de vida poderão mover dados antigos para o Glacier e eliminá-los após o período de retenção.

7. Como garantir a segurança da infraestrutura?

A segurança será garantida por autenticação, criptografia e controle de permissões. Cada dispositivo deverá possuir um certificado X.509 exclusivo para se autenticar no AWS IoT Core por meio de mTLS. As políticas do IoT Core limitarão cada dispositivo ao seu próprio tópico MQTT. Os dados serão protegidos com TLS durante a transmissão e com criptografia em repouso no S3, na SQS e no DynamoDB. O IAM aplicará o princípio do menor privilégio, permitindo que cada serviço execute somente as ações necessárias. Os ambientes de desenvolvimento, testes e produção deverão utilizar certificados, filas, credenciais e recursos separados, reduzindo o impacto de erros ou comprometimentos.