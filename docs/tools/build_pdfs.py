from __future__ import annotations

from pathlib import Path

from reportlab.graphics.shapes import Drawing, Line, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
OUT_ARCH = DOCS / "arquitetura_solucao.pdf"
OUT_SLIDES = DOCS / "apresentacao_slides.pdf"

NAVY = colors.HexColor("#12324A")
TEAL = colors.HexColor("#147D72")
ORANGE = colors.HexColor("#E47D00")
PALE = colors.HexColor("#E9F3F4")
LIGHT = colors.HexColor("#F5F7F8")
INK = colors.HexColor("#17242C")
MUTED = colors.HexColor("#52636F")
RED = colors.HexColor("#A13B32")


styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="TitleQ", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=26, leading=31, textColor=NAVY, spaceAfter=8 * mm))
styles.add(ParagraphStyle(name="SubQ", parent=styles["Normal"], fontName="Helvetica", fontSize=12, leading=17, textColor=MUTED, spaceAfter=5 * mm))
styles.add(ParagraphStyle(name="H1Q", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=18, leading=22, textColor=NAVY, spaceBefore=2 * mm, spaceAfter=5 * mm))
styles.add(ParagraphStyle(name="H2Q", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=12.5, leading=16, textColor=TEAL, spaceBefore=4 * mm, spaceAfter=2 * mm))
styles.add(ParagraphStyle(name="BodyQ", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.5, leading=13.5, textColor=INK, spaceAfter=2.5 * mm))
styles.add(ParagraphStyle(name="SmallQ", parent=styles["BodyText"], fontName="Helvetica", fontSize=7.5, leading=10.5, textColor=MUTED))
styles.add(ParagraphStyle(name="CalloutQ", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=9, leading=13, textColor=RED))
styles.add(ParagraphStyle(name="SlideTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=25, leading=29, textColor=NAVY, spaceAfter=6 * mm))
styles.add(ParagraphStyle(name="SlideBody", parent=styles["BodyText"], fontName="Helvetica", fontSize=15, leading=21, textColor=INK, leftIndent=5 * mm, bulletIndent=0, spaceAfter=3 * mm))
styles.add(ParagraphStyle(name="SlideSmall", parent=styles["BodyText"], fontName="Helvetica", fontSize=10, leading=14, textColor=MUTED))


def p(text: str, style: str = "BodyQ") -> Paragraph:
    return Paragraph(text, styles[style])


def bullet(text: str, style: str = "BodyQ") -> Paragraph:
    return Paragraph(f"- {text}", styles[style])


def table(data, widths=None, font_size=8.5):
    t = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TEAL),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), font_size),
        ("LEADING", (0, 0), (-1, -1), font_size + 3),
        ("BACKGROUND", (0, 1), (-1, -1), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#B9C8CE")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#D6E0E4"))
    canvas.line(18 * mm, 14 * mm, A4[0] - 18 * mm, 14 * mm)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(18 * mm, 9 * mm, "Monitor IoT de qualidade do ar - arquitetura final do protótipo")
    canvas.drawRightString(A4[0] - 18 * mm, 9 * mm, f"Página {doc.page}")
    canvas.restoreState()


def arch_diagram() -> Drawing:
    d = Drawing(500, 190)
    boxes = [
        (5, 105, 100, 55, "Sensores", "SHT31 · SCD41\nSGP40 · PMS7003\nMiCS-5524 bruto"),
        (135, 105, 90, 55, "ESP-WROOM-32", "30 pinos · USB-C\nqualidade · ULID\nTLS/mTLS · QoS 1"),
        (255, 105, 95, 55, "Mensageria", "Mosquitto local\nou AWS IoT Core\ntelemetria v1.1"),
        (380, 105, 110, 55, "Aplicação", "Node.js\nWebSocket\ndashboard web"),
        (255, 15, 95, 55, "Persistência", "snapshot local\nTimescaleDB futuro\nretenção · backup"),
        (380, 15, 110, 55, "Operação", "métricas · alertas\ninventário\nrunbooks"),
    ]
    for x, y, w, h, title, body in boxes:
        d.add(Rect(x, y, w, h, rx=7, ry=7, fillColor=PALE if title != "ESP32" else colors.HexColor("#FFF2D9"), strokeColor=TEAL, strokeWidth=1))
        d.add(String(x + w / 2, y + h - 16, title, textAnchor="middle", fontName="Helvetica-Bold", fontSize=10, fillColor=NAVY))
        for i, line in enumerate(body.split("\n")):
            d.add(String(x + w / 2, y + h - 31 - i * 10, line, textAnchor="middle", fontName="Helvetica", fontSize=7.2, fillColor=INK))
    for x1, y1, x2, y2 in [(105,132,135,132),(225,132,255,132),(350,132,380,132),(302,105,302,70),(350,42,380,42)]:
        d.add(Line(x1, y1, x2, y2, strokeColor=ORANGE, strokeWidth=2))
    d.add(String(178, 166, "I2C / UART / ADC", textAnchor="middle", fontName="Helvetica", fontSize=7, fillColor=MUTED))
    d.add(String(302, 166, "Wi-Fi", textAnchor="middle", fontName="Helvetica", fontSize=7, fillColor=MUTED))
    d.add(String(365, 140, "MQTT", textAnchor="middle", fontName="Helvetica", fontSize=7, fillColor=MUTED))
    return d


def make_architecture_pdf():
    doc = BaseDocTemplate(str(OUT_ARCH), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=18 * mm, bottomMargin=20 * mm,
                          title="Arquitetura da solução - Monitor IoT de qualidade do ar", author="Projeto acadêmico UFG")
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="body")
    doc.addPageTemplates(PageTemplate(id="main", frames=[frame], onPage=footer))
    s = []
    s += [Spacer(1, 4 * mm), p("ARQUITETURA DA SOLUÇÃO", "TitleQ"),
          p("Monitor IoT de qualidade do ar · versão final do protótipo", "SubQ"),
          Spacer(1, 2 * mm), arch_diagram(), Spacer(1, 3 * mm),
          p("Objetivo", "H1Q"),
          p("Plataforma educacional para observar temperatura, umidade, CO2, material particulado e um índice de VOC. O projeto integra ESP-WROOM-32 DevKit 30P/USB-C, MQTT, backend/dashboard e uma trilha executável de evolução para AWS."),
          Table([[p("ESCOPO DE SEGURANÇA", "CalloutQ")], [p("Não é instrumento certificado, alarme de incêndio, detector de vazamento nem equipamento médico. Leituras exigem caracterização, calibração e comparação com referência antes de qualquer decisão crítica.")]], colWidths=[doc.width], style=TableStyle([("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#FFF1EF")),("BOX",(0,0),(-1,-1),1,RED),("LEFTPADDING",(0,0),(-1,-1),8),("RIGHTPADDING",(0,0),(-1,-1),8),("TOPPADDING",(0,0),(-1,-1),7),("BOTTOMPADDING",(0,0),(-1,-1),7)])),
          Spacer(1, 3 * mm), p("Estado desta entrega", "H2Q"),
          table([["Componente", "Estado verificado"], ["Firmware HIL/físico/AWS", "Três builds; maior imagem usa 60,7% do slot OTA"], ["Placa alvo", "ESP-WROOM-32 DevKit 30P/USB-C; GPIOs cruzados"], ["Contrato", "13 testes Python, 9 Node e JSON Schema v1.1"], ["Stack local", "Compose, MQTT, persistência, API, PWA e mobile testados"], ["AWS", "IaC e pacote Lambda testáveis; conta real não foi alterada"], ["CAD/EDA", "Roadmaps completos; arquivos nativos dependem das ferramentas e medições"]], [45*mm, 119*mm], 7.8)]
    s += [PageBreak(), p("1. Visão funcional", "H1Q"), arch_diagram(),
          p("Fluxo principal", "H2Q"),
          bullet("O ESP32 amostra barramentos I2C/UART e a entrada analógica em cadências independentes."),
          bullet("Cada publicação consolida a leitura mais recente, marca validade/qualidade e carrega identidade de boot."),
          bullet("O broker autentica o dispositivo e distribui mensagens; o backend rejeita tópico divergente, duplicidade e payload fora do contrato."),
          bullet("O dashboard recebe estado e séries curtas por WebSocket; snapshots atômicos restauram a instalação local."),
          p("Princípios adotados", "H2Q"),
          table([["Princípio", "Aplicação"], ["Contrato antes da interface", "Schema e validadores compartilhando limites e semântica"], ["Falha explícita", "Campo nulo + quality/status; não fabricar medida"], ["Segredo fora do código", "secrets.h e .env ignorados; certificados provisionados"], ["Evolução mensurável", "gates de teste e critérios de aceite por etapa"]], [48*mm, 116*mm]),
          p("Topologia MQTT", "H2Q"), p("Publicação: <b>qualidade-ar/{site_id}/{device_id}/telemetria</b>. Estado/LWT: <b>qualidade-ar/{site_id}/{device_id}/status</b>. No IoT Core, Thing Name, client ID e device_id devem coincidir; a política limita a publicação ao site/dispositivo.")]
    s += [PageBreak(), p("2. Nó de sensoriamento", "H1Q"),
          table([["Elemento", "Interface", "Saída no protótipo", "Tratamento"], ["SHT31", "I2C", "temperatura/umidade", "CRC no driver, faixa e stale"], ["SCD41", "I2C", "CO2/temperatura/umidade", "data-ready e aquecimento"], ["SGP40", "I2C", "VOC index", "compensação T/RH + Gas Index"], ["PMS7003", "UART", "PM1/PM2.5/PM10", "frame 32 B + checksum"], ["MiCS-5524", "ADC", "tensão bruta", "média, divisor e caracterização futura"]], [30*mm,20*mm,45*mm,69*mm], 7.8),
          p("Cadência e temporalidade", "H2Q"), p("A aquisição não deve bloquear o laço principal. O SGP40 precisa de amostragem periódica para estabilizar o algoritmo; o SCD41 publica quando há dado pronto; o PMS7003 é analisado por máquina de estados. A mensagem só é emitida após o relógio NTP produzir timestamp plausível."),
          p("Interpretação", "H2Q"),
          bullet("CO2 do SCD41 é uma medida física; respeitar tempo de aquecimento, instalação e condições ambientais."),
          bullet("VOC index é adimensional e relativo ao histórico do sensor; não equivale a ppm de um gás específico."),
          bullet("O divisor resistivo do MiCS-5524 protege/condiciona o ADC, mas não transforma tensão em ppm. Publicar apenas o sinal bruto até existir curva validada."),
          p("Pinagem, alimentação e integridade", "H2Q"), p("GPIO21/22 atendem I2C, GPIO16/17 a UART2 e GPIO34/ADC1 o canal analógico. GPIO0/2/5/12/15 não são usados porque afetam o boot. No modo USB, JP1 fica aberto; no modo autônomo, USB desconectado e JP1 fechado. A entrada externa é 5 V/2 A, com LDO 3,3 V dedicado. O segundo rótulo VIN na posição de VN/GPIO39 permanece bloqueado até conferência física."),
          p("Memória do módulo", "H2Q"), p("A tabela para flash de 4 MB reserva dois slots OTA de 1.572.864 bytes e LittleFS. O payload/buffer MQTT é limitado a 896 bytes e a publicação exige pelo menos 30 kB de heap livre; TLS precisa de soak test com os certificados PEM reais.")]
    s += [PageBreak(), p("3. Contrato de telemetria v1.1", "H1Q"),
          table([["Grupo", "Campos essenciais"], ["Identidade", "schema_version, message_id ULID, site_id, device_id, boot_id, sequence"], ["Tempo", "sent_at RFC 3339 com fuso"], ["Medidas", "temperature_c, humidity_pct, co2_ppm, voc_index, pm1/pm25/pm10, lpg_ppm e gas_raw_v"], ["Qualidade", "gas_status e sensor_status"], ["Metadados", "firmware, placa/revisão, modo, RSSI, uptime e heap"]], [38*mm,126*mm]),
          p("Regras de ingestão", "H2Q"),
          bullet("Rejeitar versão desconhecida, número não finito, sequência inválida, identidade fora do padrão ou tópico incompatível."),
          bullet("Aceitar nulo somente quando a qualidade indicar ausência/erro; status OK não pode esconder medida obrigatória nula."),
          bullet("Deduplicar por message_id com janela limitada; usar boot_id para distinguir reinício de reordenação."),
          bullet("Aplicar limites de corpo, quantidade de dispositivos e tamanho de séries antes de alocar memória."),
          p("Exemplo reduzido", "H2Q"),
          Table([[Paragraph("<font name='Courier' size='7'>{<br/>  \"schema_version\": \"1.1\",<br/>  \"message_id\": \"01J...\", \"sequence\": 42,<br/>  \"sent_at\": \"2026-07-31T15:00:00Z\",<br/>  \"site_id\": \"lab-ufg\", \"device_id\": \"qar-001\",<br/>  \"measurements\": {\"co2_ppm\": 612, \"voc_index\": 103},<br/>  \"quality\": {\"gas_status\": \"SAFE\", \"sensor_status\": \"OK\"}<br/>}</font>", styles["BodyQ"])]], colWidths=[doc.width], style=TableStyle([("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#F0F3F5")),("BOX",(0,0),(-1,-1),0.5,colors.HexColor("#BCC9CF")),("LEFTPADDING",(0,0),(-1,-1),9),("TOPPADDING",(0,0),(-1,-1),7),("BOTTOMPADDING",(0,0),(-1,-1),7)]))]
    s += [PageBreak(), p("4. Backend, dashboard e persistência", "H1Q"),
          p("Base local atual", "H2Q"), p("O serviço Node.js consome MQTT ou aceita HTTP apenas quando habilitado, valida o contrato, mantém séries limitadas, salva snapshots JSON atômicos e transmite atualizações por WebSocket. A PWA mostra cartões, histórico curto, conectividade e avisos de caráter experimental."),
          table([["Controle", "Implementado / direção"], ["Entrada", "Content-Type, body limit, token opcional, validação de tópico/payload"], ["Memória", "mapas limitados, deduplicação LRU e quantidade máxima por série"], ["Persistência", "snapshot versionado, gravação atômica, volume e restauração testada"], ["Web", "CSP, headers, PWA e caminho estático resolvido com segurança"], ["Transporte", "MQTT QoS 1; TLS no ambiente de produção"], ["Histórico longo", "TimescaleDB após definição de retenção e migrações"]], [42*mm,122*mm], 7.8),
          p("Modelo recomendado", "H2Q"), bullet("telemetry_raw: evento validado, chave de tempo/dispositivo e payload rastreável."), bullet("device_registry: identidade, local, versão e estado de provisionamento."), bullet("telemetry_5m/1h: agregados contínuos para visualização e custo controlado."), bullet("quality_events: transições de erro, ausência e recuperação para operação."),
          p("Capacidade", "H2Q"), p("A planilha <b>estimativa_carga.xlsx</b> calcula mensagens/s, pico, volume diário/mensal e headroom. Os números são premissas: medir payload, throughput, índices, WAL, compressão e retenção no ambiente escolhido antes de dimensionar produção.")]
    s += [PageBreak(), p("5. Segurança e operação", "H1Q"),
          table([["Camada", "Controles mínimos"], ["Dispositivo", "credencial única, secure boot/flash encryption quando aplicável, OTA assinado"], ["Rede", "Wi-Fi segregado, egress mínimo, NTP confiável"], ["Broker", "TLS, ACL por identidade, sem anônimo, limites de conexão/mensagem"], ["Aplicação", "segredo por ambiente, dependências fixadas, headers, limites e logs sanitizados"], ["Dados", "retenção definida, backup testado, acesso mínimo e trilha de auditoria"], ["Operação", "métricas, alertas, runbook, inventário e rotação de credenciais"]], [38*mm,126*mm]),
          p("Observabilidade", "H2Q"), bullet("Taxa de mensagens recebidas/rejeitadas/duplicadas e latência fim a fim."), bullet("Dispositivos online, último timestamp, boot_id, RSSI e versão de firmware."), bullet("Percentual de medidas válidas por sensor e tempo em estado de erro/stale."), bullet("Uso de CPU/memória/disco, conexões MQTT/WS e crescimento do banco."),
          p("Resposta a falhas", "H2Q"), p("Os runbooks devem separar perda de energia, Wi-Fi, DNS/NTP, TLS, ACL, sensor ausente, leitura fora de faixa e saturação de infraestrutura. Cada incidente precisa de evidência reproduzível e critério explícito de retorno ao serviço.")]
    s += [PageBreak(), p("6. Hardware, PCB e invólucro", "H1Q"),
          p("EasyEDA Pro", "H2Q"), p("O roadmap de hardware parte de requisitos e arquitetura de alimentação, converte a netlist funcional em esquemático hierárquico, associa footprints conferidos em escala 1:1, atualiza a PCB, define regras, posiciona por blocos e executa ERC/DRC antes de Gerbers e montagem."),
          bullet("Revisar datasheet, pinagem, tensão, corrente, footprint, orientação e disponibilidade de cada item da BOM."), bullet("Manter I2C curto com pull-ups calculados; afastar ADC de retornos de corrente e antena; respeitar keepout do ESP32."), bullet("Adicionar test points em trilhos, terra, UART, I2C e entrada analógica."), bullet("Fazer bring-up por estágios: inspeção, resistência, fonte limitada, trilhos, programação e sensores um a um."),
          p("SolidWorks", "H2Q"), p("O roadmap mecânico começa por um envelope medido da placa montada, usa variáveis globais, modela base/tampa parametrizadas, posiciona torres e recortes em contexto e valida ventilação, montagem, tolerâncias, interferências e impressão."),
          bullet("A entrada de ar não deve receber jato direto nem formar volume morto; separar termicamente regulador, ESP32 e sensores."), bullet("Proteger o PMS7003 contra recirculação entre entrada e saída."), bullet("Usar protótipos de ajuste antes do STL final; registrar material, orientação, altura de camada e compensações."),
          p("Entregáveis de fabricação", "H2Q"), table([["PCB", "Mecânica"], [".epro/.json do projeto; PDF do esquemático", "SLDPRT/SLDASM com parâmetros"], ["Gerber + drill + pick-and-place", "STEP de intercâmbio e desenhos cotados"], ["BOM revisada e relatório DRC", "STL/3MF testado e registro de revisão"]], [82*mm,82*mm])]
    s += [PageBreak(), p("7. AWS IoT Core e operação de frota", "H1Q"),
          p("Caminho direto", "H2Q"), p("O perfil esp32-aws usa endpoint ATS, porta 8883, CA, certificado e chave exclusivos. Thing Name, MQTT client ID e device_id coincidem; o atributo siteId restringe o tópico na política. TLS/mTLS está compilado, mas só o sandbox com certificado real comprova handshake, heap e política."),
          table([["Componente", "Responsabilidade"], ["IoT Core", "autenticação mTLS, MQTT QoS 1 e regra por tópico"], ["SQS Standard + DLQ", "desacoplamento, reentrega e quarentena; consumidor idempotente"], ["S3 bruto", "evento original criptografado, privado e com lifecycle"], ["Lambda de referência", "validação do contrato/tópico e falha parcial por lote"], ["DynamoDB", "estado atual condicionado por ULID"], ["CloudWatch", "alarme de DLQ; ampliar para custo, falhas e latência"]], [45*mm,119*mm]),
          p("Alternativa de borda", "H2Q"), p("Um gateway Mosquitto pode concentrar fila offline e a conexão mTLS, reduzindo pressão de memória nos nós. Em troca, ele se torna componente crítico e precisa de disco, observabilidade, backup, atualização e certificado próprio."),
          p("Provisionamento e OTA", "H2Q"), bullet("Um certificado por dispositivo; testar emissão, rotação e revogação antes da frota."), bullet("Os dois slots OTA permitem rollback, mas download, assinatura, confirmação da imagem e orquestração por Jobs ainda devem ser implementados."), bullet("Aplicar o CloudFormation apenas em conta sandbox com orçamento, revisão do change set e autorização explícita.")]
    s += [PageBreak(), p("8. Verificação e critérios de aceite", "H1Q"),
          table([["Gate", "Evidência exigida"], ["G0 - contrato", "testes Python e JavaScript; amostras válidas/inválidas"], ["G1 - software", "Compose, persistência, HTTP/WS/PWA, limites e reconexão"], ["G2 - firmware", "build HIL/físico/AWS, serial, heap TLS e logs"], ["G3 - elétrica", "pinout/flash confirmados, ERC/DRC, trilhos e consumo"], ["G4 - sensores", "coleta lado a lado, repetibilidade, stale/erro e referência"], ["G5 - AWS", "mTLS, menor privilégio, reentrega/DLQ e revogação"], ["G6 - sistema", "ensaio prolongado, recuperação, deduplicação e retenção"], ["G7 - entrega", "documentação, BOM/CAD/EDA, versões e riscos"]], [40*mm,124*mm], 8),
          p("O que já foi automatizado", "H2Q"), bullet("13 testes Python, 9 testes Node.js e 10 testes Flutter."), bullet("Autoteste do simulador, análise Flutter e compilação do código Python/JavaScript."), bullet("Build PlatformIO dos ambientes esp32-hil, esp32-fisico e esp32-aws."), bullet("Compose com MQTT, Web/PWA, ingestão, WebSocket e restauração após reinício."),
          p("O que depende de laboratório", "H2Q"), bullet("Validação elétrica, calibração/caracterização, comparação contra instrumentos e ensaio térmico."), bullet("Criação e revisão nativa do projeto EasyEDA Pro."), bullet("Modelagem, interferência e prototipagem nativa no SolidWorks."),
          p("Critério de encerramento", "H2Q"), p("A versão só deve ser promovida quando todos os gates aplicáveis tiverem evidências anexadas, riscos residuais aceitos e instruções de reprodução atualizadas. Aprovação acadêmica não converte o protótipo em equipamento certificado.")]
    s += [PageBreak(), p("9. Roadmap integrado", "H1Q"),
          table([["Fase", "Resultado", "Saída de controle"], ["A - congelar requisitos", "escopo, contrato, placa/pinout", "baseline v1.1"], ["B - bancada", "sensores reais e telemetria estável", "logs + relatório de teste"], ["C - PCB rev. A", "placa fabricável e montada", "Gerber/BOM/DRC/bring-up"], ["D - case rev. A", "fluxo de ar e montagem validados", "CAD/STEP/STL + ensaio"], ["E - dados", "persistência, retenção e dashboards", "migrações + benchmark"], ["F - sandbox AWS", "mTLS, regra, DLQ e estado", "evidências + custo"], ["G - operação", "provisionamento, OTA, métricas e runbooks", "checklist de liberação"], ["H - piloto", "uso controlado, análise e correções", "relatório e decisão go/no-go"]], [28*mm,77*mm,59*mm], 7.8),
          p("Documentos de execução", "H2Q"),
          bullet("ROADMAP_GERAL.md - sequência, gates e definição de pronto."), bullet("ROADMAP_FIRMWARE.md e ROADMAP_SOFTWARE.md - evolução por componente."), bullet("ROADMAP_HARDWARE_EASYEDA.md - esquemático, PCB, fabricação e bring-up."), bullet("ROADMAP_CASE_SOLIDWORKS.md - CAD paramétrico, ventilação e fabricação."), bullet("PLANO_TESTES.md - matriz de verificação do código à bancada."),
          p("Referências normativas e técnicas", "H2Q"), p("Usar as folhas de dados e bibliotecas oficiais dos fabricantes, documentação oficial do ESP-IDF/Arduino-ESP32, MQTT 3.1.1/5.0 conforme a implantação e as recomendações de qualidade do ar apenas como contexto de comunicação. O limite operacional do sistema deve nascer da aplicação e de validação metrológica, não de uma cor arbitrária no dashboard."),
          Spacer(1, 12 * mm), p("Documento gerado em 2 de agosto de 2026 · Consulte o repositório para código e revisões posteriores.", "SmallQ")]
    doc.build(s)


def slide_header(canvas, doc):
    w, h = landscape(A4)
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, h - 8 * mm, w, 8 * mm, stroke=0, fill=1)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(15 * mm, 8 * mm, "Monitor IoT de qualidade do ar · protótipo educacional")
    canvas.drawRightString(w - 15 * mm, 8 * mm, f"{doc.page}/12")
    canvas.restoreState()


def slide_bullets(items):
    return [Paragraph(f"- {x}", styles["SlideBody"]) for x in items]


def make_slides_pdf():
    ps = landscape(A4)
    doc = BaseDocTemplate(str(OUT_SLIDES), pagesize=ps, leftMargin=18*mm, rightMargin=18*mm, topMargin=17*mm, bottomMargin=16*mm,
                          title="Apresentação - Monitor IoT de qualidade do ar", author="Projeto acadêmico UFG")
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="slide")
    doc.addPageTemplates(PageTemplate(id="slides", frames=[frame], onPage=slide_header))
    s = []
    s += [Spacer(1, 30*mm), p("MONITOR IoT DE<br/>QUALIDADE DO AR", "SlideTitle"), p("Da bancada ao protótipo integrado", "SubQ"), Spacer(1, 8*mm),
          Table([[p("ESP32", "H2Q"), p("MQTT/TLS", "H2Q"), p("Dashboard", "H2Q"), p("PCB + case", "H2Q")]], colWidths=[doc.width/4]*4, style=TableStyle([("BACKGROUND",(0,0),(-1,-1),PALE),("BOX",(0,0),(-1,-1),1,TEAL),("INNERGRID",(0,0),(-1,-1),0.5,colors.white),("ALIGN",(0,0),(-1,-1),"CENTER"),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("TOPPADDING",(0,0),(-1,-1),12),("BOTTOMPADDING",(0,0),(-1,-1),12)])), Spacer(1, 10*mm), p("Versão final do repositório · 02/08/2026", "SlideSmall")]
    s += [PageBreak(), p("1. Problema e objetivo", "SlideTitle"), *slide_bullets(["Observar variáveis ambientais com um nó de baixo custo e uma cadeia de dados reproduzível.", "Unificar aquisição, identidade da mensagem, transporte, visualização e evolução para histórico.", "Transformar um protótipo acadêmico em uma base técnica testável - sem alegar certificação metrológica ou de segurança."]), Spacer(1, 8*mm), Table([[p("Resultado", "H2Q"), p("Firmware compilável + contrato v1.1 + backend/dashboard + documentação de fabricação e testes.", "SubQ")]], colWidths=[45*mm,190*mm], style=TableStyle([("BACKGROUND",(0,0),(-1,-1),PALE),("BOX",(0,0),(-1,-1),1,TEAL),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("LEFTPADDING",(0,0),(-1,-1),10),("RIGHTPADDING",(0,0),(-1,-1),10),("TOPPADDING",(0,0),(-1,-1),10),("BOTTOMPADDING",(0,0),(-1,-1),10)]))]
    s += [PageBreak(), p("2. Arquitetura ponta a ponta", "SlideTitle"), arch_diagram(), Spacer(1, 5*mm), p("O contrato v1.1 é a fronteira: firmware, simulador, backend e documentação validam a mesma identidade, temporalidade, medidas e qualidade.", "SubQ")]
    s += [PageBreak(), p("3. Sensores e significado", "SlideTitle"), table([["Sensor", "Grandeza", "Cuidado principal"], ["SHT31", "temperatura e umidade", "posição e autoaquecimento"], ["SCD41", "CO2", "aquecimento e comparação"], ["SGP40", "VOC index", "índice relativo, não ppm"], ["PMS7003", "PM1/2.5/10", "fluxo, checksum e limpeza"], ["MiCS-5524", "tensão bruta", "caracterizar antes de converter"]], [45*mm,65*mm,130*mm], 10), Spacer(1, 5*mm), p("A regra é simples: ausência ou incerteza vira qualidade explícita; nunca uma medida inventada.", "SubQ")]
    s += [PageBreak(), p("4. Firmware para ESP-WROOM-32", "SlideTitle"), *slide_bullets(["Três ambientes: HIL via Serial, físico com drivers e AWS com TLS/mTLS.", "Aquisição não bloqueante, checksum do PMS7003, algoritmo VOC e ADC1/GPIO34.", "ULID, boot_id, sequência, NTP, MQTT QoS 1, watchdog e fila offline estática.", "Partições 4 MB: dois slots OTA; payload/buffer de 896 B e gate de heap de 30 kB."]), Spacer(1,6*mm), table([["Build", "RAM", "Flash/slot OTA"], ["esp32-hil", "50.608 B - 15,4%", "788.553 B - 50,1%"], ["esp32-fisico", "50.692 B - 15,5%", "819.233 B - 52,1%"], ["esp32-aws", "51.720 B - 15,8%", "954.301 B - 60,7%"]], [75*mm,80*mm,80*mm], 9.5)]
    s += [PageBreak(), p("5. Dados e aplicação", "SlideTitle"), *slide_bullets(["Backend valida versão, ULID, faixas, sequência, tópico e consistência da qualidade.", "Deduplicação e séries são limitadas; snapshot atômico restaura o estado após reinício.", "PWA tem quatro telas, WebSocket, shell offline e sinalização live/demo/offline.", "Flutter usa a mesma API/WS e entrega histórico, alertas, diagnóstico e modo demo."]), Spacer(1,6*mm), p("A stack Docker local sobe broker, gerador, backend e painel em um comando; o APK piloto e o Web release foram gerados.", "SubQ")]
    s += [PageBreak(), p("6. AWS sem exceder o ESP32", "SlideTitle"), table([["Nó direto", "IoT Core", "Dados", "Operação"], ["mTLS individual\nbuffer 896 B\nheap monitorado", "política por Thing\nRule por tópico\nQoS 1", "SQS + DLQ\nS3 bruto\nDynamoDB atual", "CloudWatch\ncusto\nrevogação"]], [doc.width/4]*4, 10), Spacer(1,7*mm), *slide_bullets(["CloudFormation, política e consumidor Lambda de referência estão versionados; nenhuma conta foi alterada.", "Gateway Mosquitto é alternativa quando fila offline ou custo de TLS por nó justificar.", "OTA tem dois slots preparados; cliente assinado, rollback confirmado e provisioning ainda são gates."])]
    s += [PageBreak(), p("7. Segurança por camadas", "SlideTitle"), table([["Dispositivo", "Transporte", "Serviço", "Operação"], ["credencial única\nsegredos externos\nOTA assinado", "TLS/mTLS\nACL/política\nQoS 1", "limites de corpo\nCSP/headers\nIAM mínimo", "métricas\nbackup testado\nrotação e runbooks"]], [doc.width/4]*4, 10), Spacer(1, 9*mm), p("Produção: sem MQTT anônimo, sem HTTP de ingestão aberto e sem credencial compartilhada entre dispositivos.", "CalloutQ")]
    s += [PageBreak(), p("8. Da netlist à PCB no EasyEDA Pro", "SlideTitle"), *slide_bullets(["Criar símbolo próprio de duas fileiras 1x15 a partir do pinout físico do ESP-WROOM-32 30P.", "Confirmar o pad ambíguo VIN/VN, dimensões e footprint impresso em escala 1:1.", "Separar modo USB (JP1 aberto) e modo autônomo (USB fora, JP1 fechado); validar LDO e térmica.", "Executar ERC/DRC, revisar antena/ADC/retornos e fazer bring-up com fonte limitada."]), Spacer(1,5*mm), p("BOM, netlist, regras de PCB e checklist de liberação estão no repositório.", "SubQ")]
    s += [PageBreak(), p("9. Case paramétrica no SolidWorks", "SlideTitle"), *slide_bullets(["Medir placa 30P, headers, shield, USB-C, EN/BOOT, conectores e antena.", "Modelar torres, recortes e ventilação em contexto; manter acesso à manutenção.", "Separar fontes de calor dos sensores e impedir recirculação no PMS7003.", "Executar interferência, protótipo de ajuste, ensaio térmico e revisão antes de STEP/STL final."]), Spacer(1,5*mm), p("Os parâmetros iniciais são hipóteses - toda dimensão crítica deve ser substituída pela medição real.", "CalloutQ")]
    s += [PageBreak(), p("10. Verificação por gates", "SlideTitle"), table([["G0", "G1", "G2", "G3", "G4", "G5/G6"], ["contrato", "software", "firmware", "elétrica", "sensores", "AWS/sistema"], ["13 Py + 9 Node", "10 Flutter + APK", "3 builds + heap", "pinout + ERC/DRC", "comparação", "mTLS/DLQ/soak"]], [doc.width/6]*6, 9.2), Spacer(1,8*mm), *slide_bullets(["Automatizado: 13 Python, 9 Node, 10 Flutter, simulador, API/PWA e restore.", "Compilado: HIL, físico e AWS para esp32doit-devkit-v1/flash de 4 MB.", "Pendente físico/externo: flash e sensores reais, EasyEDA/SolidWorks nativos e sandbox AWS."])]
    s += [PageBreak(), p("11. Próximos marcos", "SlideTitle"), table([["1", "2", "3", "4", "5", "6"], ["HIL real", "bancada", "PCB A", "case A", "AWS", "piloto"], ["flash/serial", "sensores", "bring-up", "fluxo/térmica", "mTLS/DLQ", "go/no-go"]], [doc.width/6]*6, 9), Spacer(1,10*mm), p("Definição de pronto", "H1Q"), *slide_bullets(["Evidências dos gates anexadas e reproduzíveis.", "Riscos residuais registrados e aceitos.", "Documentação, código, BOM, CAD/EDA e versões sincronizados."]), Spacer(1,8*mm), p("Software local pronto; próxima evidência vem da bancada e do sandbox autorizado.", "SubQ")]
    doc.build(s)


if __name__ == "__main__":
    DOCS.mkdir(parents=True, exist_ok=True)
    make_architecture_pdf()
    make_slides_pdf()
    print(f"generated {OUT_ARCH} ({OUT_ARCH.stat().st_size} bytes)")
    print(f"generated {OUT_SLIDES} ({OUT_SLIDES.stat().st_size} bytes)")
