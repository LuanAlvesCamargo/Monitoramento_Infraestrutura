from copy import deepcopy
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "modelo_de_trabalhos.docx"
OUTPUT = ROOT / "relatorio" / "Relatorio_Tecnico_Cientifico_Monitoramento_Infraestrutura.docx"
EVIDENCES = ROOT / "evidencias" / "relatorio"
ARCHITECTURE = EVIDENCES / "arquitetura-laboratorio.png"
EVIDENCE_COMPOSITE = EVIDENCES / "evidencia-prometheus-node-grafana.png"


def set_cell_shading(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shading = OxmlElement("w:shd")
    shading.set(qn("w:fill"), fill)
    tc_pr.append(shading)


def set_cell_border(cell, color="D9D9D9"):
    tc_pr = cell._tc.get_or_add_tcPr()
    borders = tc_pr.first_child_found_in("w:tcBorders")
    if borders is None:
        borders = OxmlElement("w:tcBorders")
        tc_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = f"w:{edge}"
        element = borders.find(qn(tag))
        if element is None:
            element = OxmlElement(tag)
            borders.append(element)
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), "4")
        element.set(qn("w:color"), color)


def set_repeat_table_header(row):
    tr_pr = row._tr.get_or_add_trPr()
    header = OxmlElement("w:tblHeader")
    header.set(qn("w:val"), "true")
    tr_pr.append(header)


def set_run_font(run, size=12, bold=False, italic=False, color="000000"):
    run.font.name = "Times New Roman"
    run._element.rPr.rFonts.set(qn("w:ascii"), "Times New Roman")
    run._element.rPr.rFonts.set(qn("w:hAnsi"), "Times New Roman")
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = RGBColor.from_string(color)


def clear_paragraph(paragraph):
    p = paragraph._element
    for child in list(p):
        p.remove(child)


def delete_paragraph(paragraph):
    paragraph._element.getparent().remove(paragraph._element)


def make_architecture():
    EVIDENCES.mkdir(parents=True, exist_ok=True)
    canvas = Image.new("RGB", (1600, 900), "white")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
    small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
    bold = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)

    def box(x, y, w, h, title, subtitle, fill):
        draw.rounded_rectangle((x, y, x + w, y + h), radius=18, fill=fill, outline="#334155", width=3)
        draw.text((x + w / 2, y + 28), title, font=bold, fill="#111827", anchor="ma")
        draw.multiline_text((x + w / 2, y + 78), subtitle, font=small, fill="#1f2937", anchor="ma", align="center", spacing=4)

    def arrow(a, b, text=""):
        draw.line((a[0], a[1], b[0], b[1]), fill="#475569", width=5)
        draw.polygon([(b[0], b[1]), (b[0] - 15, b[1] - 8), (b[0] - 15, b[1] + 8)], fill="#475569")
        if text:
            mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            draw.text((mx, my - 22), text, font=small, fill="#334155", anchor="ms")

    draw.text((800, 38), "Arquitetura do Laboratório de Monitoramento", font=bold, fill="#111827", anchor="ma")
    box(80, 180, 270, 140, "Juice Shop", "Aplicação web\nporta 3100", "#FDE68A")
    box(80, 470, 270, 140, "Clientes e Bot", "Requisições HTTP\ntráfego controlado", "#BFDBFE")
    box(510, 180, 280, 140, "Node Exporter", "Métricas do Fedora\nporta 9101", "#BBF7D0")
    box(510, 470, 280, 140, "Prometheus", "Coleta e séries temporais\nporta 9091", "#FECACA")
    box(1000, 130, 280, 140, "Grafana", "Dashboard técnico\nporta 3200", "#FDE68A")
    box(1000, 350, 280, 140, "Zabbix", "Servidor, web e banco\nporta 8081", "#DDD6FE")
    box(1000, 570, 280, 280, "Dashboard Flask", "Visão unificada\nPrometheus + Zabbix +\nverificação Juice Shop\nporta 3300", "#CFFAFE")
    arrow((350, 540), (510, 540), "HTTP")
    arrow((650, 320), (650, 470), "scrape")
    arrow((790, 540), (1000, 420), "consulta HTTP")
    arrow((790, 540), (1000, 200), "datasource")
    arrow((1140, 270), (1140, 350), "API")
    arrow((1140, 490), (1140, 570), "API")
    arrow((350, 250), (510, 250), "execução no Fedora")
    draw.text((800, 860), "Fonte: elaborado pelo autor (2026).", font=small, fill="#334155", anchor="ma")
    canvas.save(ARCHITECTURE)


def make_evidence_composite():
    """Organiza três capturas fornecidas pelo autor em uma única figura técnica."""
    canvas = Image.new("RGB", (1800, 1520), "#f8fafc")
    label_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 34)

    sources = [
        (EVIDENCES / "usuario-prometheus-up.png", "Prometheus: targets UP", (40, 80, 840, 530)),
        (EVIDENCES / "usuario-node-exporter-metrics.png", "Node Exporter: endpoint /metrics", (920, 80, 840, 530)),
        (EVIDENCES / "usuario-grafana-dashboard.png", "Grafana: dashboard de infraestrutura", (40, 730, 1720, 735)),
    ]
    for path, label, (x, y, w, h) in sources:
        image = Image.open(path).convert("RGB")
        thumb = ImageOps.contain(image, (w, h - 45), method=Image.Resampling.LANCZOS)
        panel = Image.new("RGB", (w, h), "#ffffff")
        panel.paste(thumb, ((w - thumb.width) // 2, 45 + (h - 45 - thumb.height) // 2))
        draw = ImageDraw.Draw(panel)
        draw.rectangle((0, 0, w, 45), fill="#1f4e78")
        draw.text((18, 8), label, font=label_font, fill="white")
        canvas.paste(panel, (x, y))
    canvas.save(EVIDENCE_COMPOSITE)


def add_paragraph(doc, text="", style=None, alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, bold_prefix=None):
    p = doc.add_paragraph(style=style)
    p.alignment = alignment
    p.paragraph_format.first_line_indent = Cm(1.25) if alignment == WD_ALIGN_PARAGRAPH.JUSTIFY and text else None
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.space_after = Pt(6)
    if bold_prefix and text.startswith(bold_prefix):
        first = p.add_run(bold_prefix)
        set_run_font(first, 12, bold=True)
        rest = p.add_run(text[len(bold_prefix):])
        set_run_font(rest)
    else:
        run = p.add_run(text)
        set_run_font(run)
    return p


def add_heading(doc, text, level=1):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(14 if level == 1 else 10)
    p.paragraph_format.space_after = Pt(8)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    set_run_font(run, 13 if level == 1 else 12, bold=True)
    return p


def add_list(doc, items):
    for item in items:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.left_indent = Cm(0.8)
        p.paragraph_format.first_line_indent = Cm(-0.45)
        p.paragraph_format.line_spacing = 1.5
        p.paragraph_format.space_after = Pt(3)
        run = p.add_run("• " + item)
        set_run_font(run)


def add_table(doc, headers, rows, widths=None):
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    header = table.rows[0]
    set_repeat_table_header(header)
    for idx, text in enumerate(headers):
        cell = header.cells[idx]
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        set_cell_shading(cell, "1F4E78")
        set_cell_border(cell)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(text)
        set_run_font(r, 10, bold=True, color="FFFFFF")
    for row_idx, values in enumerate(rows):
        cells = table.add_row().cells
        for idx, value in enumerate(values):
            cell = cells[idx]
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            set_cell_border(cell)
            if row_idx % 2:
                set_cell_shading(cell, "F2F6FA")
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            r = p.add_run(str(value))
            set_run_font(r, 10)
    if widths:
        for row in table.rows:
            for idx, width in enumerate(widths):
                row.cells[idx].width = Cm(width)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return table


def add_figure(doc, path, number, title, source, width_cm=15.5):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    run.add_picture(str(path), width=Cm(width_cm))
    p.paragraph_format.space_after = Pt(3)
    caption = doc.add_paragraph()
    caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption.paragraph_format.space_after = Pt(2)
    r = caption.add_run(f"Figura {number} – {title}")
    set_run_font(r, 10, bold=True)
    source_p = doc.add_paragraph()
    source_p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    source_p.paragraph_format.space_after = Pt(10)
    source_r = source_p.add_run(f"Fonte: {source}")
    set_run_font(source_r, 10)


def add_page_break(doc):
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def configure_cover(doc):
    mapping = {
        9: "Tópicos Especiais II",
        14: "MONITORAMENTO DE INFRAESTRUTURA COM PROMETHEUS GRAFANA ZABBIX E PODMAN",
        19: "Luan Camargo",
        20: "Matrícula: 51310",
        39: "2026",
    }
    for idx, text in mapping.items():
        p = doc.paragraphs[idx]
        clear_paragraph(p)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(text)
        set_run_font(r, 15 if idx == 14 else 13, bold=True)
    for p in list(doc.paragraphs[40:]):
        delete_paragraph(p)


def make_document():
    make_architecture()
    make_evidence_composite()
    doc = Document(TEMPLATE)
    configure_cover(doc)
    section = doc.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.left_margin = Cm(3)
    section.right_margin = Cm(2)
    section.top_margin = Cm(3)
    section.bottom_margin = Cm(2)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Luan Camargo")
    set_run_font(r, 12, bold=True)
    for _ in range(5):
        doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("MONITORAMENTO DE INFRAESTRUTURA COM PROMETHEUS GRAFANA ZABBIX E PODMAN")
    set_run_font(r, 14, bold=True)
    for _ in range(6):
        doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.left_indent = Cm(8)
    p.paragraph_format.right_indent = Cm(0.5)
    p.paragraph_format.line_spacing = 1.5
    r = p.add_run("Relatório técnico-científico apresentado à disciplina de Tópicos Especiais II do curso de Ciência da Computação das Faculdades Integradas de Bauru, como registro do planejamento, implementação e avaliação de um laboratório de monitoramento de infraestrutura.")
    set_run_font(r)
    for _ in range(7):
        doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Bauru\n2026")
    set_run_font(r, 12, bold=True)

    add_page_break(doc)
    add_heading(doc, "RESUMO", 1)
    add_paragraph(doc, "Este trabalho apresenta o planejamento, a implementação e a avaliação de um laboratório controlado de monitoramento de infraestrutura executado em uma estação Fedora. A solução utiliza Podman Compose para orquestrar a aplicação OWASP Juice Shop, clientes automatizados de tráfego, Node Exporter, Prometheus, Grafana, Zabbix e um dashboard próprio em Flask. O objetivo foi observar CPU, memória, disco, rede e disponibilidade, comparando o modelo de coleta por scraping do Prometheus com a visualização e o gerenciamento de eventos do Zabbix. O Node Exporter foi configurado para observar o host Fedora e não apenas os containers. O Prometheus coletou as métricas a cada 15 segundos, avaliou uma regra de CPU alta e forneceu dados ao Grafana e ao dashboard centralizado. O Zabbix foi instalado em containers e preparado para consultar as métricas por HTTP por meio da API do Prometheus, alternativa adotada devido à indisponibilidade direta do pacote zabbix-agent2 nos repositórios usados no Fedora. As evidências demonstram a execução simultânea dos serviços, a disponibilidade dos targets monitorados e a consolidação das fontes de dados em uma interface própria. Conclui-se que a composição proposta é reproduzível, de baixo acoplamento com o host e adequada para fins didáticos de DevOps e monitoramento de infraestrutura.")
    add_paragraph(doc, "Palavras-chave: monitoramento de infraestrutura; Prometheus; Grafana; Zabbix; Podman; DevOps.", bold_prefix="Palavras-chave: ")

    add_page_break(doc)
    add_heading(doc, "SUMÁRIO", 1)
    for item in [
        "1 INTRODUÇÃO",
        "2 FUNDAMENTAÇÃO TÉCNICA",
        "3 METODOLOGIA E ARQUITETURA DO LABORATÓRIO",
        "4 IMPLEMENTAÇÃO DA SOLUÇÃO",
        "5 RESULTADOS E DISCUSSÃO",
        "6 LIMITAÇÕES E TRABALHOS FUTUROS",
        "7 CONCLUSÃO",
        "REFERÊNCIAS",
        "APÊNDICE A – COMANDOS PRINCIPAIS",
    ]:
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Cm(1)
        p.paragraph_format.space_after = Pt(7)
        r = p.add_run(item)
        set_run_font(r, 12)

    add_page_break(doc)
    add_heading(doc, "1 INTRODUÇÃO", 1)
    add_paragraph(doc, "O monitoramento de infraestrutura é uma prática indispensável para observar o estado operacional de servidores, aplicações e redes. Sem métricas e eventos confiáveis, problemas de capacidade, indisponibilidade ou degradação de desempenho tendem a ser identificados tardiamente. Em ambientes de DevOps, a instrumentação e a visualização contínua reduzem a dependência de verificações manuais e apoiam decisões fundamentadas durante incidentes e mudanças de configuração.")
    add_paragraph(doc, "A proposta inicial da disciplina previa a instalação de serviços em uma máquina virtual Ubuntu Server. Após alinhamento com o professor, o escopo foi adaptado para uma estação Fedora, sem máquina virtual, mantendo os objetivos de coleta de CPU, memória RAM, disco, rede e disponibilidade. A decisão preservou a natureza controlada do laboratório e permitiu concentrar o estudo na orquestração de containers, na observabilidade e na comparação entre ferramentas livres.")
    add_paragraph(doc, "A questão orientadora foi: como integrar Prometheus, Grafana e Zabbix para observar o mesmo ambiente local, gerar tráfego controlado para uma aplicação web e apresentar os resultados de forma compreensível? Para respondê-la, foi construído um ambiente reprodutível com Podman Compose, uma aplicação OWASP Juice Shop, containers clientes, um bot de tráfego e uma camada adicional de consolidação em Flask.")
    add_heading(doc, "1.1 Objetivos", 2)
    add_list(doc, [
        "implementar um laboratório reproduzível de monitoramento no Fedora usando containers;",
        "coletar métricas de CPU, memória, disco, rede e disponibilidade do host;",
        "gerar tráfego HTTP contínuo contra a aplicação monitorada;",
        "comparar os papéis de Prometheus, Grafana e Zabbix;",
        "centralizar indicadores e identificar, em cada visualização, a fonte do dado exibido.",
    ])

    add_page_break(doc)
    add_heading(doc, "2 FUNDAMENTAÇÃO TÉCNICA", 1)
    add_heading(doc, "2.1 Monitoramento e séries temporais", 2)
    add_paragraph(doc, "Uma métrica representa uma observação numérica associada a um instante de tempo. Em monitoramento de infraestrutura, exemplos frequentes são porcentagem de CPU ocupada, memória disponível, bytes transmitidos por interface e estado de disponibilidade. O armazenamento em séries temporais permite correlacionar alterações de comportamento com eventos operacionais, como o início de uma carga de requisições ou a parada de um serviço.")
    add_heading(doc, "2.2 Prometheus e Node Exporter", 2)
    add_paragraph(doc, "O Prometheus é um sistema de monitoramento e alerta que coleta dados por scraping de endpoints HTTP e os armazena como séries temporais identificadas por rótulos. Sua arquitetura se adapta bem a métricas numéricas e ambientes orientados a serviços (PROMETHEUS AUTHORS, 2026). No laboratório, o Node Exporter expõe métricas do Fedora em formato Prometheus; o servidor Prometheus as coleta periodicamente e disponibiliza consultas em PromQL.")
    add_heading(doc, "2.3 Zabbix", 2)
    add_paragraph(doc, "O Zabbix é uma solução de monitoramento open source que acompanha parâmetros de servidores, serviços, aplicações e redes, oferecendo histórico, problemas, triggers e frontend web (ZABBIX SIA, 2026). Neste projeto, o Zabbix foi executado com PostgreSQL e frontend próprios. Para evitar instalar dependências adicionais no Fedora, os itens do Zabbix foram projetados como consultas HTTP à API do Prometheus, mantendo o mesmo host como referência de comparação.")
    add_heading(doc, "2.4 Grafana e dashboards", 2)
    add_paragraph(doc, "Grafana organiza fontes de dados em painéis e dashboards, permitindo apresentar gráficos, indicadores e tabelas em uma única interface (GRAFANA LABS, 2026). O seu uso no laboratório é complementar ao Prometheus: o primeiro fornece visualização, enquanto o segundo fornece armazenamento e consulta de métricas. Um dashboard Flask adicional foi criado para explicitar a origem de cada dado e combinar status de Prometheus, Zabbix e Juice Shop.")
    add_heading(doc, "2.5 Containers e Podman", 2)
    add_paragraph(doc, "Podman é uma ferramenta para criar e manter containers, podendo ser utilizada sem daemon central e em modo não privilegiado. A documentação recomenda a referência explícita das imagens, prática adotada neste trabalho para tornar a origem dos componentes clara (PODMAN, 2026). O arquivo compose.yaml descreve os serviços, a rede interna e os volumes persistentes do laboratório.")

    add_page_break(doc)
    add_heading(doc, "3 METODOLOGIA E ARQUITETURA DO LABORATÓRIO", 1)
    add_paragraph(doc, "A pesquisa caracteriza-se como aplicada e experimental, pois constrói uma solução funcional e a observa em ambiente controlado. O cenário foi limitado à máquina local para reduzir variáveis de infraestrutura externa. A validação foi realizada por meio de verificações HTTP, estado dos containers, targets do Prometheus e inspeção das interfaces web.")
    add_heading(doc, "3.1 Ambiente de execução", 2)
    add_table(doc, ["Componente", "Versão ou característica", "Finalidade"], [
        ["Sistema operacional", "Fedora 44, kernel 7.2.5", "Host monitorado e plataforma de execução"],
        ["Podman", "5.8.4", "Execução de containers"],
        ["podman-compose", "1.6.0", "Leitura do arquivo Compose"],
        ["Prometheus", "Container oficial", "Scraping, consultas e regra de alerta"],
        ["Node Exporter", "Container oficial", "Exposição de métricas do Fedora"],
        ["Grafana", "Container oficial", "Dashboard técnico"],
        ["Zabbix", "Server, web e PostgreSQL", "Eventos, itens e frontend"],
        ["OWASP Juice Shop", "Imagem oficial", "Aplicação web monitorada"],
    ], [3.0, 4.5, 7.5])
    add_heading(doc, "3.2 Arquitetura", 2)
    add_paragraph(doc, "A Figura 1 apresenta o fluxo principal. Clientes e bot enviam requisições à aplicação. O Node Exporter acessa informações do host por montagens somente leitura de /proc, /sys e /, e o Prometheus coleta o endpoint exposto. Grafana e dashboard Flask consultam o Prometheus. O Zabbix utiliza consultas HTTP para obter os valores necessários e apresenta itens e eventos em seu frontend.")
    add_figure(doc, ARCHITECTURE, 1, "Arquitetura do laboratório", "elaborado pelo autor (2026)", 11.5)
    add_heading(doc, "4 IMPLEMENTAÇÃO DA SOLUÇÃO", 1)
    add_heading(doc, "4.1 Orquestração dos serviços", 2)
    add_paragraph(doc, "Todos os componentes foram descritos no compose.yaml e conectados à rede interna denominada monitoramento. As portas do host foram escolhidas para evitar colisão com serviços já existentes na máquina: 3100 para Juice Shop, 3200 para Grafana, 3300 para o dashboard Flask, 8081 para Zabbix Web, 9091 para Prometheus e 9101 para Node Exporter. O PostgreSQL do Zabbix permaneceu restrito à rede interna.")
    add_table(doc, ["Serviço", "Porta local", "Função"], [
        ["Juice Shop", "3100", "Aplicação web monitorada"],
        ["Grafana", "3200", "Dashboard técnico"],
        ["Dashboard Flask", "3300", "Visão centralizada com fontes identificadas"],
        ["Zabbix Web", "8081", "Frontend de monitoramento e eventos"],
        ["Prometheus", "9091", "Consultas, targets e alertas"],
        ["Node Exporter", "9101", "Métricas brutas do Fedora"],
    ], [4.2, 3.0, 7.8])
    add_heading(doc, "4.2 Coleta de métricas", 2)
    add_paragraph(doc, "O Prometheus foi configurado com intervalo de coleta e avaliação de 15 segundos. Dois jobs foram definidos: o próprio Prometheus e o host Fedora, identificado como fedora-node. A regra CPUAlta calcula a média de tempo não ocioso do processador usando node_cpu_seconds_total e gera condição de alerta acima de 80% durante dois minutos.")
    add_heading(doc, "4.3 Geração de tráfego", 2)
    add_paragraph(doc, "Dois containers Alpine executam buscas periódicas por apple e banana na API do Juice Shop. Um terceiro serviço, bot-trafego, simula navegação básica, requisitando a página inicial e termos de busca distintos aproximadamente uma vez por segundo. Essa estratégia produz tráfego de rede e atividade de aplicação sem instalar ferramentas de carga no host Fedora.")
    add_heading(doc, "4.4 Dashboard centralizado", 2)
    add_paragraph(doc, "O serviço Flask consulta a API do Prometheus para indicadores instantâneos, séries de CPU e memória, além dos targets ativos. Também realiza uma verificação HTTP do Juice Shop. A consulta da API do Zabbix é opcional e depende de credencial local no arquivo .env, que não é versionado. Cada cartão, gráfico ou tabela informa explicitamente sua fonte, evitando que o usuário confunda métricas brutas, agregações PromQL e eventos do Zabbix.")

    add_heading(doc, "5 RESULTADOS E DISCUSSÃO", 1)
    add_heading(doc, "5.1 Visão centralizada", 2)
    add_paragraph(doc, "A Figura 2 registra o dashboard Flask em execução. Na captura, a disponibilidade do Node Exporter aparece como UP e a verificação HTTP do Juice Shop também aparece como UP. O painel mostra indicadores de CPU, memória, disco e rede, gráficos de CPU e memória e a tabela de targets do Prometheus. A captura registra CPU de 27,5%, memória de 52,6% e disco de 20,5%; esses valores representam um instante do laboratório e não devem ser interpretados como média de longo prazo.")
    add_figure(doc, EVIDENCES / "usuario-dashboard-flask.png", 2, "Dashboard centralizado em Flask", "captura do ambiente local fornecida pelo autor (2026)", 12.0)
    add_heading(doc, "5.2 Targets do Prometheus e disponibilidade", 2)
    add_paragraph(doc, "A tabela de targets do dashboard confirma que os jobs prometheus e fedora-node estavam ativos. O endpoint do host foi resolvido internamente como host.containers.internal:9101/metrics. Esse resultado demonstra que o Prometheus conseguiu alcançar o exporter exposto pelo host e que a coleta não ficou limitada ao container da aplicação.")
    add_paragraph(doc, "A regra CPUAlta foi mantida como evidência de alerta baseado em série temporal. Sua lógica exige permanência da condição acima do limiar por dois minutos, reduzindo o risco de alertas provocados por picos transitórios. O comportamento é adequado para a demonstração prática prevista no laboratório, na qual uma carga controlada pode ser aplicada e posteriormente interrompida.")

    add_heading(doc, "5.3 Métricas expostas pelo Node Exporter", 2)
    add_paragraph(doc, "A Figura 3 reúne as evidências de coleta e visualização. O painel superior esquerdo mostra os targets do Prometheus, ambos com valor 1; o painel superior direito apresenta parte do endpoint /metrics do Node Exporter, em formato textual com linhas HELP e TYPE; e o painel inferior mostra o Grafana. Nesse dashboard, a série de CPU registra um pico próximo de 95%, produzido pelo experimento controlado de carga, enquanto memória, disco, rede e a quantidade de targets permanecem visíveis.")
    add_figure(doc, EVIDENCE_COMPOSITE, 3, "Evidências de coleta e visualização com Prometheus, Node Exporter e Grafana", "capturas do ambiente local fornecidas pelo autor (2026)", 12.0)
    add_heading(doc, "5.4 Aplicação e tráfego", 2)
    add_paragraph(doc, "A aplicação OWASP Juice Shop foi escolhida como alvo por ser uma aplicação web pronta para execução em container e apropriada para laboratórios. A OWASP descreve o projeto como aplicação deliberadamente insegura voltada a treinamento; por esse motivo, ela foi mantida restrita ao ambiente local, sem exposição pública (OWASP FOUNDATION, 2026). A verificação HTTP usada pelo dashboard mede a disponibilidade da aplicação, enquanto os containers clientes e o bot produzem requisições internas ao Compose.")
    add_figure(doc, EVIDENCES / "usuario-juice-shop.png", 4, "Interface da aplicação OWASP Juice Shop", "captura do ambiente local fornecida pelo autor (2026)", 11.0)
    add_heading(doc, "5.5 Zabbix e comparação entre as ferramentas", 2)
    add_paragraph(doc, "A Figura 5 confirma o cadastro do host Fedora-monitorado no frontend do Zabbix, com dois itens associados e estado habilitado. A solução foi instalada com servidor, interface web e banco PostgreSQL em containers. Os itens podem ser criados pelo script configurar_zabbix.py, que utiliza a API do Zabbix e não armazena senhas no repositório. A integração do dashboard Flask com a API do Zabbix depende da definição de ZABBIX_API_PASSWORD no arquivo .env local.")
    add_figure(doc, EVIDENCES / "usuario-zabbix-hosts.png", 5, "Host Fedora-monitorado cadastrado no Zabbix", "captura do ambiente local fornecida pelo autor (2026)", 11.0)
    add_table(doc, ["Aspecto", "Prometheus", "Zabbix"], [
        ["Modelo principal", "Scraping periódico de endpoints HTTP", "Itens, histórico, triggers e frontend"],
        ["Consulta", "PromQL e API HTTP", "Interface web e API JSON-RPC"],
        ["Uso no laboratório", "Coleta primária do Node Exporter", "Eventos e consulta HTTP ao Prometheus"],
        ["Visualização", "Grafana e dashboard Flask", "Frontend próprio e dashboard Flask"],
        ["Alerta de CPU", "Regra CPUAlta com condição temporal", "Trigger baseada no item fedora.cpu.usage"],
    ], [3.5, 6.0, 5.5])
    add_paragraph(doc, "A comparação deve considerar que os dados do Zabbix foram projetados para consulta ao Prometheus neste laboratório. Assim, as ferramentas não operam com coletores completamente independentes: o Prometheus é a fonte primária da telemetria do Fedora e o Zabbix agrega a camada de itens, triggers e histórico a partir de consultas HTTP. Essa escolha foi tecnicamente adequada ao Fedora utilizado e mantém a comparação focada na organização e apresentação dos dados, não em uma disputa de precisão entre coletores distintos.")

    add_heading(doc, "6 LIMITAÇÕES E TRABALHOS FUTUROS", 1)
    add_paragraph(doc, "A principal limitação é a dependência da credencial local para a leitura autenticada da API do Zabbix no dashboard Flask. A credencial foi propositalmente mantida fora do repositório, no arquivo .env ignorado pelo Git. Como consequência, uma captura do dashboard pode apresentar a mensagem de que a credencial não está configurada até que o usuário defina a senha localmente.")
    add_paragraph(doc, "Outra limitação é que o teste de alta CPU registrado neste relatório utiliza o estado observado no momento da captura. Uma avaliação futura pode executar uma carga com duração controlada, registrar o instante de disparo dos alertas e exportar gráficos de ambas as ferramentas. A instrumentação nativa da aplicação, com métricas específicas de requisições HTTP, também permitiria quantificar o tráfego do bot de modo mais direto do que a observação de bytes de rede do host.")
    add_list(doc, [
        "configurar um serviço systemd de usuário para inicializar o Compose no login;",
        "finalizar a credencial do Zabbix no .env e validar os itens no dashboard Flask;",
        "registrar um experimento de carga de CPU com início, duração e recuperação;",
        "adicionar métricas específicas da aplicação ou um exporter de requisições HTTP;",
        "exportar o host, itens e triggers do Zabbix para anexação ao repositório.",
    ])

    add_heading(doc, "7 CONCLUSÃO", 1)
    add_paragraph(doc, "O laboratório implementado demonstrou uma abordagem reproduzível de monitoramento de infraestrutura em Fedora sem necessidade de máquina virtual. O uso de Podman Compose reuniu a aplicação, os geradores de tráfego e os componentes de observabilidade em uma rede interna organizada, com portas locais controladas e volumes persistentes para dados relevantes.")
    add_paragraph(doc, "O Node Exporter permitiu observar o host Fedora e o Prometheus confirmou a disponibilidade dos targets e a coleta de séries temporais. Grafana foi preparado como dashboard técnico, enquanto o dashboard Flask consolidou indicadores e tornou explícita a origem de cada informação. A disponibilidade do Juice Shop e o tráfego contínuo dos clientes e do bot tornam o cenário adequado para demonstrações práticas de disponibilidade, CPU, memória, disco e rede.")
    add_paragraph(doc, "A integração com Zabbix preserva seu papel de gerenciamento de itens e eventos, utilizando consultas HTTP como alternativa viável para o ambiente Fedora. Embora a configuração final da credencial da API permaneça uma etapa local, o desenho, os scripts e a documentação necessários foram entregues. Portanto, a solução atende ao objetivo didático de comparar tecnologias open source e demonstrar como dashboards facilitam a interpretação de métricas de infraestrutura.")

    add_heading(doc, "REFERÊNCIAS", 1)
    references = [
        "GRAFANA LABS. Grafana dashboards overview. Disponível em: <https://grafana.com/docs/grafana/latest/fundamentals/dashboards-overview/>. Acesso em: 27 out. 2026.",
        "OWASP FOUNDATION. OWASP Juice Shop. Disponível em: <https://owasp.org/projects/juice-shop>. Acesso em: 27 out. 2026.",
        "PODMAN. Getting Started with Podman. Disponível em: <https://podman.io/docs>. Acesso em: 27 out. 2026.",
        "PROMETHEUS AUTHORS. Overview. Disponível em: <https://prometheus.io/docs/introduction/overview/>. Acesso em: 27 out. 2026.",
        "PROMETHEUS AUTHORS. First steps with Prometheus. Disponível em: <https://prometheus.io/docs/introduction/first_steps/>. Acesso em: 27 out. 2026.",
        "ZABBIX SIA. What is Zabbix. Disponível em: <https://www.zabbix.com/documentation/current/en/manual/introduction/about>. Acesso em: 27 out. 2026.",
        "FACULDADES INTEGRADAS DE BAURU. Aula 07 Infraestrutura de TI Tópicos Especiais II. Material didático disponibilizado para a disciplina, 2026.",
    ]
    for ref in references:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.first_line_indent = Cm(-1.0)
        p.paragraph_format.left_indent = Cm(1.0)
        p.paragraph_format.space_after = Pt(8)
        r = p.add_run(ref)
        set_run_font(r, 11)

    add_heading(doc, "APÊNDICE A – COMANDOS PRINCIPAIS", 1)
    add_paragraph(doc, "Os comandos a seguir foram utilizados para iniciar, validar e inspecionar o ambiente. Senhas e dados privados não são incluídos.")
    commands = [
        "podman compose up -d",
        "podman compose ps",
        "curl http://localhost:3300/health",
        "curl http://localhost:9091/-/ready",
        "curl http://localhost:9101/metrics",
        "podman logs --tail=100 monitoramento-dashboard",
        "podman compose up -d --build dashboard",
        "podman compose stop juice-shop",
        "podman compose start juice-shop",
    ]
    for command in commands:
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Cm(1)
        p.paragraph_format.space_after = Pt(3)
        r = p.add_run(command)
        set_run_font(r, 10)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    make_document()
