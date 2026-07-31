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
    canvas.drawString(18 * mm, 9 * mm, "Monitor IoT de qualidade do ar — arquitetura final do protótipo")
    canvas.drawRightString(A4[0] - 18 * mm, 9 * mm, f"Página {doc.page}")
    canvas.restoreState()


def arch_diagram() -> Drawing:
    d = Drawing(500, 190)
    boxes = [
        (5, 105, 100, 55, "Sensores", "SHT31 · SCD41\nSGP40 · PMS7003\nMiCS-5524 bruto"),
        (135, 105, 90, 55, "ESP32", "aquisição\nqualidade · ULID\nTLS/MQTT QoS 1"),
        (255, 105, 95, 55, "Broker", "Mosquitto\nACL · TLS\ntelemetria v1.1"),
        (380, 105, 110, 55, "Aplicação", "Node.js\nWebSocket\ndashboard web"),
        (255, 15, 95, 55, "Persistência", "TimescaleDB\nretenção · agregados\nbackup"),
        (380, 15, 110, 55, "Operação", "métricas · alertas\ninventário\nrunbooks"),
    ]
    for x, y, w, h, title, body in boxes:
        d.add(Rect(x, y, w, h, rx=7, ry=7, fillColor=PALE if title != "ESP32" else colors.HexColor("#FFF2D9"), strokeColor=TEAL, strokeWidth=1))
        d.add(String(x + w / 2, y + h - 16, title, textAnchor="middle", fontName="Helvetica-Bold", fontSize=10, fillColor=NAVY))
        for i, line in enumerate(body.split("\n")):
            d.add(String(x + w / 2, y + h - 31 - i * 10, line, textAnchor="middle", fontName="Helvetica", fontSize=7.2, fillColor=INK))
    for x1, y1, x2, y2 in [(105,132,135,132),(225,132,255,132),(350,132,380,132),(302,105,302,70),(350,42,380,42)]:
        d.add(Line(x1, y1, x2, y2, strokeColor=ORANGE, strokeWidth=2))
    d.add(String(178, 166, "I²C / UART / ADC", textAnchor="middle", fontName="Helvetica", fontSize=7, fillColor=MUTED))
    d.add(String(302, 166, "Wi-Fi", textAnchor="middle", fontName="Helvetica", fontSize=7, fillColor=MUTED))
    d.add(String(365, 140, "MQTT", textAnchor="middle", fontName="Helvetica", fontSize=7, fillColor=MUTED))
    return d


def make_architecture_pdf():
    doc = BaseDocTemplate(str(OUT_ARCH), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=18 * mm, bottomMargin=20 * mm,
                          title="Arquitetura da solução — Monitor IoT de qualidade do ar", author="Projeto acadêmico UFG")
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="body")
    doc.addPageTemplates(PageTemplate(id="main", frames=[frame], onPage=footer))
    s = []
    s += [Spacer(1, 19 * mm), p("ARQUITETURA DA SOLUÇÃO", "TitleQ"),
          p("Monitor IoT de qualidade do ar · versão final do protótipo", "SubQ"),
          Spacer(1, 7 * mm), arch_diagram(), Spacer(1, 8 * mm),
          p("Objetivo", "H1Q"),
          p("Plataforma educacional para observar temperatura, umidade, CO₂, material particulado e um índice de VOC. O projeto integra nó ESP32, mensageria MQTT, backend em Node.js, dashboard web e uma trilha de evolução para persistência e operação."),
          Table([[p("ESCOPO DE SEGURANÇA", "CalloutQ")], [p("Não é instrumento certificado, alarme de incêndio, detector de vazamento nem equipamento médico. Leituras exigem caracterização, calibração e comparação com referência antes de qualquer decisão crítica.")]], colWidths=[doc.width], style=TableStyle([("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#FFF1EF")),("BOX",(0,0),(-1,-1),1,RED),("LEFTPADDING",(0,0),(-1,-1),8),("RIGHTPADDING",(0,0),(-1,-1),8),("TOPPADDING",(0,0),(-1,-1),7),("BOTTOMPADDING",(0,0),(-1,-1),7)])),
          Spacer(1, 7 * mm), p("Estado desta entrega", "H2Q"),
          table([["Componente", "Estado verificado"], ["Firmware HIL", "Compila e aceita frames por Serial"], ["Firmware físico", "Compila com drivers SHT31, SCD41, SGP40 e PMS7003"], ["Contrato", "Validadores Python/JavaScript e JSON Schema v1.1"], ["Backend/dashboard", "Ingestão, WebSocket, limites e testes de integração"], ["Hardware mecânico", "Roadmaps de execução; arquivos CAD/EDA ainda dependem do projeto nas ferramentas"]], [45*mm, 119*mm])]
    s += [PageBreak(), p("1. Visão funcional", "H1Q"), arch_diagram(),
          p("Fluxo principal", "H2Q"),
          bullet("O ESP32 amostra barramentos I²C/UART e a entrada analógica em cadências independentes."),
          bullet("Cada publicação consolida a leitura mais recente, marca validade/qualidade e carrega identidade de boot."),
          bullet("O broker autentica o dispositivo e distribui mensagens; o backend rejeita tópico divergente, duplicidade e payload fora do contrato."),
          bullet("O dashboard recebe o estado atual e séries curtas por WebSocket. Persistência histórica é a evolução recomendada."),
          p("Princípios adotados", "H2Q"),
          table([["Princípio", "Aplicação"], ["Contrato antes da interface", "Schema e validadores compartilhando limites e semântica"], ["Falha explícita", "Campo nulo + quality/status; não fabricar medida"], ["Segredo fora do código", "secrets.h e .env ignorados; certificados provisionados"], ["Evolução mensurável", "gates de teste e critérios de aceite por etapa"]], [48*mm, 116*mm]),
          p("Topologia MQTT", "H2Q"), p("Publicação: <b>qualidade-ar/{site_id}/{device_id}/telemetria</b>. Estado/LWT: <b>qualidade-ar/{site_id}/{device_id}/status</b>. A identidade do certificado/ACL deve limitar cada dispositivo ao próprio prefixo.")]
    s += [PageBreak(), p("2. Nó de sensoriamento", "H1Q"),
          table([["Elemento", "Interface", "Saída no protótipo", "Tratamento"], ["SHT31", "I²C", "temperatura/umidade", "CRC no driver, faixa e stale"], ["SCD41", "I²C", "CO₂/temperatura/umidade", "data-ready e aquecimento"], ["SGP40", "I²C", "VOC index", "compensação T/RH + Gas Index"], ["PMS7003", "UART", "PM1/PM2.5/PM10", "frame 32 B + checksum"], ["MiCS-5524", "ADC", "tensão bruta", "média, divisor e caracterização futura"]], [30*mm,20*mm,45*mm,69*mm], 7.8),
          p("Cadência e temporalidade", "H2Q"), p("A aquisição não deve bloquear o laço principal. O SGP40 precisa de amostragem periódica para estabilizar o algoritmo; o SCD41 publica quando há dado pronto; o PMS7003 é analisado por máquina de estados. A mensagem só é emitida após o relógio NTP produzir timestamp plausível."),
          p("Interpretação", "H2Q"),
          bullet("CO₂ do SCD41 é uma medida física; respeitar tempo de aquecimento, instalação e condições ambientais."),
          bullet("VOC index é adimensional e relativo ao histórico do sensor; não equivale a ppm de um gás específico."),
          bullet("O divisor resistivo do MiCS-5524 protege/condiciona o ADC, mas não transforma tensão em ppm. Publicar apenas o sinal bruto até existir curva validada."),
          p("Alimentação e integridade", "H2Q"), p("A placa deve separar o domínio de 5 V de cargas (PMS e aquecedor do MiCS) do 3,3 V lógico, manter terra comum bem roteado, incluir proteção de entrada e capacitores locais. O orçamento de corrente, a queda do regulador e a temperatura da caixa precisam ser medidos no protótipo.")]
    s += [PageBreak(), p("3. Contrato de telemetria v1.1", "H1Q"),
          table([["Grupo", "Campos essenciais"], ["Identidade", "schema_version, message_id ULID, site_id, device_id, boot_id, seq"], ["Tempo", "timestamp RFC 3339 com fuso"], ["Medidas", "temperature_c, humidity_rh, co2_ppm, voc_index, pm1/pm2_5/pm10, gas_raw_v"], ["Qualidade", "status geral, erros e validade por sensor"], ["Metadados", "firmware, modo do sensor, RSSI e uptime"]], [38*mm,126*mm]),
          p("Regras de ingestão", "H2Q"),
          bullet("Rejeitar versão desconhecida, número não finito, sequência inválida, identidade fora do padrão ou tópico incompatível."),
          bullet("Aceitar nulo somente quando a qualidade indicar ausência/erro; status OK não pode esconder medida obrigatória nula."),
          bullet("Deduplicar por message_id com janela limitada; usar boot_id para distinguir reinício de reordenação."),
          bullet("Aplicar limites de corpo, quantidade de dispositivos e tamanho de séries antes de alocar memória."),
          p("Exemplo reduzido", "H2Q"),
          Table([[Paragraph("<font name='Courier' size='7'>{<br/>  \"schema_version\": \"1.1\",<br/>  \"message_id\": \"01J...\", \"seq\": 42,<br/>  \"timestamp\": \"2026-07-31T12:00:00-03:00\",<br/>  \"site_id\": \"lab-ufg\", \"device_id\": \"qar-001\",<br/>  \"measurements\": {\"co2_ppm\": 612, \"voc_index\": 103},<br/>  \"quality\": {\"status\": \"OK\"}<br/>}</font>", styles["BodyQ"])]], colWidths=[doc.width], style=TableStyle([("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#F0F3F5")),("BOX",(0,0),(-1,-1),0.5,colors.HexColor("#BCC9CF")),("LEFTPADDING",(0,0),(-1,-1),9),("TOPPADDING",(0,0),(-1,-1),7),("BOTTOMPADDING",(0,0),(-1,-1),7)]))]
    s += [PageBreak(), p("4. Backend, dashboard e persistência", "H1Q"),
          p("MVP atual", "H2Q"), p("O serviço Node.js consome MQTT ou aceita HTTP somente quando habilitado, valida o contrato, mantém séries limitadas em memória e transmite atualização via WebSocket. A interface web mostra cartões, histórico curto, conectividade e avisos de caráter experimental."),
          table([["Controle", "Implementado / direção"], ["Entrada", "Content-Type, body limit, token opcional, validação de tópico/payload"], ["Memória", "mapas limitados, deduplicação LRU e quantidade máxima por série"], ["Web", "CSP, headers de segurança, caminho estático resolvido com segurança"], ["Transporte", "MQTT QoS 1; TLS no ambiente de produção"], ["Histórico", "TimescaleDB previsto após definição de retenção e migrações"]], [42*mm,122*mm]),
          p("Modelo recomendado", "H2Q"), bullet("telemetry_raw: evento validado, chave de tempo/dispositivo e payload rastreável."), bullet("device_registry: identidade, local, versão e estado de provisionamento."), bullet("telemetry_5m/1h: agregados contínuos para visualização e custo controlado."), bullet("quality_events: transições de erro, ausência e recuperação para operação."),
          p("Capacidade", "H2Q"), p("A planilha <b>estimativa_carga.xlsx</b> calcula mensagens/s, pico, volume diário/mensal e headroom. Os números são premissas: medir payload, throughput, índices, WAL, compressão e retenção no ambiente escolhido antes de dimensionar produção.")]
    s += [PageBreak(), p("5. Segurança e operação", "H1Q"),
          table([["Camada", "Controles mínimos"], ["Dispositivo", "credencial única, secure boot/flash encryption quando aplicável, OTA assinado"], ["Rede", "Wi-Fi segregado, egress mínimo, NTP confiável"], ["Broker", "TLS, ACL por identidade, sem anônimo, limites de conexão/mensagem"], ["Aplicação", "segredo por ambiente, dependências fixadas, headers, limites e logs sanitizados"], ["Dados", "retenção definida, backup testado, acesso mínimo e trilha de auditoria"], ["Operação", "métricas, alertas, runbook, inventário e rotação de credenciais"]], [38*mm,126*mm]),
          p("Observabilidade", "H2Q"), bullet("Taxa de mensagens recebidas/rejeitadas/duplicadas e latência fim a fim."), bullet("Dispositivos online, último timestamp, boot_id, RSSI e versão de firmware."), bullet("Percentual de medidas válidas por sensor e tempo em estado de erro/stale."), bullet("Uso de CPU/memória/disco, conexões MQTT/WS e crescimento do banco."),
          p("Resposta a falhas", "H2Q"), p("Os runbooks devem separar perda de energia, Wi-Fi, DNS/NTP, TLS, ACL, sensor ausente, leitura fora de faixa e saturação de infraestrutura. Cada incidente precisa de evidência reproduzível e critério explícito de retorno ao serviço.")]
    s += [PageBreak(), p("6. Hardware, PCB e invólucro", "H1Q"),
          p("EasyEDA Pro", "H2Q"), p("O roadmap de hardware parte de requisitos e arquitetura de alimentação, converte a netlist funcional em esquemático hierárquico, associa footprints conferidos em escala 1:1, atualiza a PCB, define regras, posiciona por blocos e executa ERC/DRC antes de Gerbers e montagem."),
          bullet("Revisar datasheet, pinagem, tensão, corrente, footprint, orientação e disponibilidade de cada item da BOM."), bullet("Manter I²C curto com pull-ups calculados; afastar ADC de retornos de corrente e antena; respeitar keepout do ESP32."), bullet("Adicionar test points em trilhos, terra, UART, I²C e entrada analógica."), bullet("Fazer bring-up por estágios: inspeção, resistência, fonte limitada, trilhos, programação e sensores um a um."),
          p("SolidWorks", "H2Q"), p("O roadmap mecânico começa por um envelope medido da placa montada, usa variáveis globais, modela base/tampa parametrizadas, posiciona torres e recortes em contexto e valida ventilação, montagem, tolerâncias, interferências e impressão."),
          bullet("A entrada de ar não deve receber jato direto nem formar volume morto; separar termicamente regulador, ESP32 e sensores."), bullet("Proteger o PMS7003 contra recirculação entre entrada e saída."), bullet("Usar protótipos de ajuste antes do STL final; registrar material, orientação, altura de camada e compensações."),
          p("Entregáveis de fabricação", "H2Q"), table([["PCB", "Mecânica"], [".epro/.json do projeto; PDF do esquemático", "SLDPRT/SLDASM com parâmetros"], ["Gerber + drill + pick-and-place", "STEP de intercâmbio e desenhos cotados"], ["BOM revisada e relatório DRC", "STL/3MF testado e registro de revisão"]], [82*mm,82*mm])]
    s += [PageBreak(), p("7. Verificação e critérios de aceite", "H1Q"),
          table([["Gate", "Evidência exigida"], ["G0 — contrato", "testes Python e JavaScript; amostras válidas/inválidas"], ["G1 — software", "integração backend, HTTP/WS, limites e reconexão"], ["G2 — firmware", "build HIL/físico, teste serial e logs de bancada"], ["G3 — elétrica", "ERC/DRC limpos, inspeção, trilhos e consumo medidos"], ["G4 — sensores", "coleta lado a lado, repetibilidade, stale/erro e comparação de referência"], ["G5 — sistema", "ensaio prolongado, perda/recuperação de rede, deduplicação e retenção"], ["G6 — entrega", "documentação, BOM/CAD/EDA, versões, riscos e instruções reproduzíveis"]], [40*mm,124*mm]),
          p("O que já foi automatizado", "H2Q"), bullet("Validação unitária do contrato em Python e Node.js."), bullet("Autoteste do simulador e compilação do código Python/JavaScript."), bullet("Build PlatformIO dos ambientes esp32-hil e esp32-fisico."), bullet("Teste integrado do backend com ingestão válida, listagem, métricas e conteúdo web."),
          p("O que depende de laboratório", "H2Q"), bullet("Validação elétrica, calibração/caracterização, comparação contra instrumentos e ensaio térmico."), bullet("Criação e revisão nativa do projeto EasyEDA Pro."), bullet("Modelagem, interferência e prototipagem nativa no SolidWorks."),
          p("Critério de encerramento", "H2Q"), p("A versão só deve ser promovida quando todos os gates aplicáveis tiverem evidências anexadas, riscos residuais aceitos e instruções de reprodução atualizadas. Aprovação acadêmica não converte o protótipo em equipamento certificado.")]
    s += [PageBreak(), p("8. Roadmap integrado", "H1Q"),
          table([["Fase", "Resultado", "Saída de controle"], ["A — congelar requisitos", "escopo, contrato, requisitos elétricos/mecânicos", "baseline v1.1"], ["B — bancada", "sensores reais e telemetria estável", "logs + relatório de teste"], ["C — PCB rev. A", "placa fabricável e montada", "Gerber/BOM/DRC/bring-up"], ["D — case rev. A", "fluxo de ar e montagem validados", "CAD/STEP/STL + ensaio"], ["E — dados", "persistência, retenção e dashboards", "migrações + benchmark"], ["F — operação", "segurança, OTA, métricas e runbooks", "checklist de liberação"], ["G — piloto", "uso controlado, análise e correções", "relatório e decisão go/no-go"]], [28*mm,77*mm,59*mm]),
          p("Documentos de execução", "H2Q"),
          bullet("ROADMAP_GERAL.md — sequência, gates e definição de pronto."), bullet("ROADMAP_FIRMWARE.md e ROADMAP_SOFTWARE.md — evolução por componente."), bullet("ROADMAP_HARDWARE_EASYEDA.md — esquemático, PCB, fabricação e bring-up."), bullet("ROADMAP_CASE_SOLIDWORKS.md — CAD paramétrico, ventilação e fabricação."), bullet("PLANO_TESTES.md — matriz de verificação do código à bancada."),
          p("Referências normativas e técnicas", "H2Q"), p("Usar as folhas de dados e bibliotecas oficiais dos fabricantes, documentação oficial do ESP-IDF/Arduino-ESP32, MQTT 3.1.1/5.0 conforme a implantação e as recomendações de qualidade do ar apenas como contexto de comunicação. O limite operacional do sistema deve nascer da aplicação e de validação metrológica, não de uma cor arbitrária no dashboard."),
          Spacer(1, 12 * mm), p("Documento gerado em 31 de julho de 2026 · Consulte o repositório para código e revisões posteriores.", "SmallQ")]
    doc.build(s)


def slide_header(canvas, doc):
    w, h = landscape(A4)
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, h - 8 * mm, w, 8 * mm, stroke=0, fill=1)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(15 * mm, 8 * mm, "Monitor IoT de qualidade do ar · protótipo educacional")
    canvas.drawRightString(w - 15 * mm, 8 * mm, f"{doc.page}/11")
    canvas.restoreState()


def slide_bullets(items):
    return [Paragraph(f"- {x}", styles["SlideBody"]) for x in items]


def make_slides_pdf():
    ps = landscape(A4)
    doc = BaseDocTemplate(str(OUT_SLIDES), pagesize=ps, leftMargin=18*mm, rightMargin=18*mm, topMargin=17*mm, bottomMargin=16*mm,
                          title="Apresentação — Monitor IoT de qualidade do ar", author="Projeto acadêmico UFG")
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="slide")
    doc.addPageTemplates(PageTemplate(id="slides", frames=[frame], onPage=slide_header))
    s = []
    s += [Spacer(1, 30*mm), p("MONITOR IoT DE<br/>QUALIDADE DO AR", "SlideTitle"), p("Da bancada ao protótipo integrado", "SubQ"), Spacer(1, 8*mm),
          Table([[p("ESP32", "H2Q"), p("MQTT/TLS", "H2Q"), p("Dashboard", "H2Q"), p("PCB + case", "H2Q")]], colWidths=[doc.width/4]*4, style=TableStyle([("BACKGROUND",(0,0),(-1,-1),PALE),("BOX",(0,0),(-1,-1),1,TEAL),("INNERGRID",(0,0),(-1,-1),0.5,colors.white),("ALIGN",(0,0),(-1,-1),"CENTER"),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("TOPPADDING",(0,0),(-1,-1),12),("BOTTOMPADDING",(0,0),(-1,-1),12)])), Spacer(1, 10*mm), p("Versão final do repositório · 31/07/2026", "SlideSmall")]
    s += [PageBreak(), p("1. Problema e objetivo", "SlideTitle"), *slide_bullets(["Observar variáveis ambientais com um nó de baixo custo e uma cadeia de dados reproduzível.", "Unificar aquisição, identidade da mensagem, transporte, visualização e evolução para histórico.", "Transformar um protótipo acadêmico em uma base técnica testável — sem alegar certificação metrológica ou de segurança."]), Spacer(1, 8*mm), Table([[p("Resultado", "H2Q"), p("Firmware compilável + contrato v1.1 + backend/dashboard + documentação de fabricação e testes.", "SubQ")]], colWidths=[45*mm,190*mm], style=TableStyle([("BACKGROUND",(0,0),(-1,-1),PALE),("BOX",(0,0),(-1,-1),1,TEAL),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("LEFTPADDING",(0,0),(-1,-1),10),("RIGHTPADDING",(0,0),(-1,-1),10),("TOPPADDING",(0,0),(-1,-1),10),("BOTTOMPADDING",(0,0),(-1,-1),10)]))]
    s += [PageBreak(), p("2. Arquitetura ponta a ponta", "SlideTitle"), arch_diagram(), Spacer(1, 5*mm), p("O contrato v1.1 é a fronteira: firmware, simulador, backend e documentação validam a mesma identidade, temporalidade, medidas e qualidade.", "SubQ")]
    s += [PageBreak(), p("3. Sensores e significado", "SlideTitle"), table([["Sensor", "Grandeza", "Cuidado principal"], ["SHT31", "temperatura e umidade", "posição e autoaquecimento"], ["SCD41", "CO₂", "aquecimento e comparação"], ["SGP40", "VOC index", "índice relativo, não ppm"], ["PMS7003", "PM1/2.5/10", "fluxo, checksum e limpeza"], ["MiCS-5524", "tensão bruta", "caracterizar antes de converter"]], [45*mm,65*mm,130*mm], 10), Spacer(1, 5*mm), p("A regra é simples: ausência ou incerteza vira qualidade explícita; nunca uma medida inventada.", "SubQ")]
    s += [PageBreak(), p("4. Firmware finalizado para integração", "SlideTitle"), *slide_bullets(["Dois ambientes: HIL via Serial e físico com drivers oficiais.", "Aquisição não bloqueante, checksum do PMS7003, algoritmo VOC e leitura ADC em milivolts.", "ULID canônico, boot_id, sequência, timestamp após NTP, MQTT QoS 1 e suporte a TLS.", "Segredos saíram do código; existe modelo secrets.example.h."]), Spacer(1,6*mm), table([["Build", "RAM", "Flash"], ["esp32-hil", "14,3%", "59,9%"], ["esp32-fisico", "14,4%", "62,3%"]], [80*mm,70*mm,70*mm], 10)]
    s += [PageBreak(), p("5. Dados e aplicação", "SlideTitle"), *slide_bullets(["Backend valida versão, ULID, faixas, sequência, tópico e consistência da qualidade.", "Deduplicação limitada e tratamento de reboot evitam crescimento irrestrito e falsos descartes.", "Dashboard reage por WebSocket, reconecta com controle e sinaliza o caráter experimental.", "Próximo degrau: TimescaleDB, retenção, agregados, backup e observabilidade."]), Spacer(1,6*mm), p("A planilha de carga transforma dispositivos, intervalo, payload e pico em capacidade e armazenamento estimados.", "SubQ")]
    s += [PageBreak(), p("6. Segurança por camadas", "SlideTitle"), table([["Dispositivo", "Transporte", "Serviço", "Operação"], ["credencial única\nsegredos externos\nOTA assinado", "TLS\nACL por tópico\nQoS 1", "limites de corpo\nCSP/headers\ndependências fixadas", "métricas\nbackup testado\nrotação e runbooks"]], [doc.width/4]*4, 10), Spacer(1, 9*mm), p("Produção: sem MQTT anônimo, sem HTTP de ingestão aberto e sem credencial compartilhada entre dispositivos.", "CalloutQ")]
    s += [PageBreak(), p("7. Da netlist à PCB no EasyEDA Pro", "SlideTitle"), *slide_bullets(["Congelar requisitos elétricos e revisar BOM, símbolo, footprint e disponibilidade.", "Criar esquemático por blocos; executar ERC; associar footprints conferidos em escala 1:1.", "Atualizar a PCB, definir stack/regras, posicionar por função e respeitar antena, ADC e retornos de corrente.", "Rodar DRC, gerar Gerber/drill/pick-and-place e fazer bring-up com fonte limitada."]), Spacer(1,5*mm), p("O roadmap fornece netlist, sequência de cliques, checklist de revisão e critérios de aceite da revisão A.", "SubQ")]
    s += [PageBreak(), p("8. Case paramétrica no SolidWorks", "SlideTitle"), *slide_bullets(["Medir o conjunto montado e dirigir base/tampa por variáveis globais.", "Modelar torres, recortes e ventilação em contexto; manter acesso a USB, botões e manutenção.", "Separar fontes de calor dos sensores e impedir recirculação no PMS7003.", "Executar interferência, protótipo de ajuste, ensaio térmico e revisão antes de STEP/STL final."]), Spacer(1,5*mm), p("Os parâmetros iniciais são hipóteses — toda dimensão crítica deve ser substituída pela medição real.", "CalloutQ")]
    s += [PageBreak(), p("9. Verificação por gates", "SlideTitle"), table([["G0", "G1", "G2", "G3", "G4", "G5/G6"], ["contrato", "software", "firmware", "elétrica", "sensores", "sistema e entrega"], ["testes unitários", "integração", "build + bancada", "ERC/DRC + trilhos", "comparação", "ensaio + evidências"]], [doc.width/6]*6, 9.5), Spacer(1,8*mm), *slide_bullets(["Automatizado agora: 8 testes Python, 6 testes Node, autoteste do simulador e integração HTTP/WebSocket.", "Compilado agora: ambientes HIL e físico do ESP32.", "Pendente de laboratório/ferramenta: calibração, PCB nativa, case nativa e ensaios ambientais."])]
    s += [PageBreak(), p("10. Próximos marcos", "SlideTitle"), table([["1", "2", "3", "4", "5"], ["bancada física", "PCB rev. A", "case rev. A", "persistência", "piloto controlado"], ["logs e comparação", "bring-up", "fluxo e térmica", "retenção e backup", "go/no-go"]], [doc.width/5]*5, 10), Spacer(1,10*mm), p("Definição de pronto", "H1Q"), *slide_bullets(["Evidências dos gates anexadas e reproduzíveis.", "Riscos residuais registrados e aceitos.", "Documentação, código, BOM, CAD/EDA e versões sincronizados."]), Spacer(1,8*mm), p("Base pronta para a próxima etapa: validação física disciplinada.", "SubQ")]
    doc.build(s)


if __name__ == "__main__":
    DOCS.mkdir(parents=True, exist_ok=True)
    make_architecture_pdf()
    make_slides_pdf()
    print(f"generated {OUT_ARCH} ({OUT_ARCH.stat().st_size} bytes)")
    print(f"generated {OUT_SLIDES} ({OUT_SLIDES.stat().st_size} bytes)")
