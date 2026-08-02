# Síntese do Projeto — em linguagem simples

> **Importante:** é um protótipo educacional, não um alarme certificado. Ele
> ajuda a observar tendências ambientais, mas não deve ser usado como única
> base para decisões de emergência ou para declarar um ambiente seguro.

> Uma explicação do projeto **inteiro** para qualquer pessoa, sem jargão, com
> analogias do dia a dia. Se você quer entender "o que é isso e como funciona"
> em 10 minutos, comece por aqui. Os detalhes técnicos estão no
> [`BASE_FINAL.md`](BASE_FINAL.md) e no [`ARQUITETURA.md`](ARQUITETURA.md).

---

## 1. Qual problema resolvemos?

Imagine uma sala fechada — uma sala de aula, um escritório, um quarto. Você não
enxerga, mas o ar ali pode estar ruim: gás carbônico acumulado, poeira fina ou
compostos voláteis. O problema é que **os nossos sentidos falham**: a gente se
acostuma com o ar viciado e não percebe o perigo.

Nosso projeto é como instalar um **"nariz eletrônico" que nunca dorme**. Ele
mede o ar o tempo todo e avisa, em linguagem simples, quando está na hora de
investigar a ventilação e possíveis fontes de poluição.

---

## 2. O que construímos, em uma frase

Um **aparelho** (do tamanho de uma caixinha) que cheira o ar e manda os dados
pela internet para **um painel no computador e no celular**, que mostram, com
cores e palavras fáceis, se o ar está bom ou ruim.

---

## 3. As peças do quebra-cabeça (com analogias)

**Os sensores — o nariz.**
São cinco "narizes" especializados, cada um sente uma coisa: gás carbônico,
poeira fina, cheiros/químicos (VOC), gás de cozinha (GLP), e temperatura/
umidade. Como um sommelier que separa os aromas de um vinho, cada sensor é
craque em uma pista.

**O ESP32 — o mensageiro.**
É um pequeno computador (do tamanho de um chiclete) que lê os cinco narizes,
junta tudo em um "bilhete" organizado e envia pela internet. Pense nele como um
carteiro que recolhe as cartas e as leva ao correio.

**O broker MQTT — o correio.**
É um servidor que recebe os bilhetes do mensageiro e entrega para quem estiver
interessado (o painel, o celular). Igual a uma agência dos Correios: quem manda
não precisa conhecer quem recebe; o correio faz a ponte.

**O painel e o app — o mostrador do carro.**
No painel do carro você não precisa ser mecânico para saber que a luz vermelha
significa "pare". Nossos painéis funcionam assim: uma tela grande diz **"Ar: BOM
/ ATENÇÃO / RUIM"** por cor, e sugere a ação ("abra a janela").

**A caixa e a placa — o corpo e o esqueleto.**
A **placa de circuito (PCB)** é o esqueleto que conecta tudo com organização (em
vez de um monte de fios soltos). A **caixa (case)** é o corpo que protege as
peças e, ao mesmo tempo, deixa o ar circular para o nariz funcionar — como as
narinas, que protegem mas deixam o ar entrar.

---

## 4. A sacada mais inteligente do projeto (o "dublê")

Normalmente, para programar um aparelho desses, você teria que **esperar todos
os sensores chegarem** pelo correio para só então começar a testar o software.
Isso trava o projeto por semanas.

Nós usamos um truque de cinema: um **dublê**. Assim como um filme grava as cenas
perigosas com um dublê no lugar do ator principal, aqui um **programa no
computador finge ser os sensores**. Ele inventa medições realistas — inclusive
situações de emergência, como um **incêndio** ou um **vazamento de gás** — e as
envia para o ESP32 **de verdade**, pelo cabo USB.

Assim, todo o resto (o envio pela internet, os painéis, os alertas) é construído
e testado **hoje**, com o ESP32 real rodando o programa real. Quando os sensores
de verdade chegarem, a gente troca **uma única chavezinha** no programa e o
aparelho passa a usar os sensores físicos — **sem reescrever nada**.

> Em termos técnicos isso se chama *Hardware-in-the-Loop* com o padrão
> *Strategy*. Mas a ideia é a do dublê: treinar com o substituto e trocar pelo
> titular na hora do jogo.

**A tomada universal.** Por que trocar de sensor (dublê → real) não quebra o
resto? Porque o programa foi feito como uma **tomada universal de viagem**: não
importa se o "plugue" é o sensor simulado ou o físico — o encaixe é o mesmo, e o
aparelho continua funcionando igual.

---

## 5. A viagem de um dado (do ar até a sua tela)

1. **O ar entra** na caixa e passa pelos sensores.
2. Cada sensor **mede** a sua grandeza (ex.: "gás carbônico: 800").
3. O ESP32 **junta tudo em um bilhete** padronizado (sempre no mesmo formato,
   como um formulário oficial — assim todo mundo entende).
4. O bilhete vai pela internet até o **correio (broker)**.
5. O **painel e o app** pegam o bilhete e mostram para você, traduzido:
   "Ar bom" (verde) ou "Ventile o ambiente" (amarelo) ou "Perigo" (vermelho).

**Carta registrada.** Para nenhum bilhete se perder no caminho, cada um leva um
**número de rastreio** (uma sequência) e um **selo único**. Se faltar o número
7 entre o 6 e o 8, o sistema sabe na hora que uma carta se perdeu. É como o
rastreamento de uma encomenda: você percebe se algo sumiu. Nos nossos testes,
**nenhum** bilhete se perdeu.

---

## 6. E a parte da energia? (por que tem um "redutor")

Alguns sensores são "comilões": a ventoinha do sensor de poeira e o aquecedor do
sensor de gás puxam bastante energia. Por isso recomendamos alimentar o aparelho
com um **carregador de celular (não a porta USB do PC)**, que aguenta mais.

Além disso, o sensor de gás fala numa "voz" que pode ser **alta demais** para o
ESP32 ouvir sem se machucar (a tensão passa do limite seguro). Colocamos então
um **redutor** — como aquela **válvula que transforma o jato forte de uma
mangueira num filete suave de bebedouro**. Ele diminui o sinal para um nível
seguro, e o programa "recalcula" o valor original. Assim o ESP32 escuta o sensor
sem correr risco.

---

## 7. Por que dá para confiar? (qualidade de engenharia)

- **Testado de verdade:** simulamos **milhares** de aparelhos ao mesmo tempo e
  medimos — sem perder mensagens, com baixa demora. Não é só teoria.
- **Cresce por etapas:** a arquitetura separa dispositivo, broker, ingestão e
  armazenamento; há um sandbox AWS reproduzível, mas a escala real precisa ser
  comprovada por testes e orçamento.
- **Seguro:** comunicação pode ser **criptografada**, cada aparelho tem sua
  identidade, e nada de senha no lugar errado.
- **Honesto:** o que ainda não foi montado fisicamente está claramente marcado
  como "a validar no hardware" — nada é vendido como pronto sem ter sido.

---

## 8. O que já existe e o que vem a seguir

**Já pronto e funcionando:**
- O "dublê" (simulador) que inventa cenários realistas, inclusive emergências.
- O miolo do programa do aparelho (a "tomada universal" que troca dublê ↔ real).
- O formulário padrão dos dados e o "correio" (broker) testado com milhares de
  aparelhos.
- Uma instalação local em um comando, com broker, gerador de dados, backend
  persistente e painel web instalável no computador ou celular.
- A planta da placa (PCB) e da caixa, prontas para você desenhar/imprimir.

**Próximos passos:**
- Montar o aparelho físico (placa + caixa + sensores reais).
- Validar o painel com usuários e, se houver necessidade comprovada, criar um
  aplicativo Flutter nativo além da PWA já funcional.
- Ligar avisos automáticos (ex.: mensagem no celular quando o ar ficar ruim).
- Validar no sandbox AWS o caminho IoT Core → SQS/DLQ → S3/DynamoDB.

---

## 9. Em uma frase, para guardar

> Construímos um **nariz eletrônico que nunca dorme** e avisa, em cores e
> palavras simples, quando é hora de cuidar do ar — e fomos espertos: treinamos
> tudo com um **dublê** para não depender de esperar as peças chegarem.

---

*Quer os detalhes? [`BASE_FINAL.md`](BASE_FINAL.md) (o projeto completo),
[`ARQUITETURA.md`](ARQUITETURA.md) (como os dados fluem em escala),
[`hardware/pcb`](hardware/pcb/README.md) (a placa) e
[`firmware`](firmware/README.md) (o programa do aparelho).*
