from pathlib import Path
from datetime import date
from PIL import Image, ImageDraw, ImageFont
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.section import WD_SECTION
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "relatorio" / "Relatorio_Tecnico_Cientifico_JurisDocs.docx"
ASSETS = ROOT / "relatorio" / "assets"
ASSETS.mkdir(parents=True, exist_ok=True)

BLUE = "#172034"
ORANGE = "#BF4D31"
GRAY = "#D9D9D9"


def font(size, bold=False):
    for path in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/liberation2/LiberationSans-Regular.ttf"]:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def create_architecture_image(path):
    image = Image.new("RGB", (1600, 720), "white")
    draw = ImageDraw.Draw(image)
    title = font(38, True); regular = font(28); small = font(22)
    draw.text((60, 35), "Arquitetura do JurisDocs", fill=BLUE, font=title)
    boxes = [(80, 255, 310, 445, "Navegador", "127.0.0.1:5174"), (440, 255, 730, 445, "React + Nginx", "interface e proxy /api"), (850, 255, 1110, 445, "Flask + Gunicorn", "API REST"), (1240, 130, 1530, 315, "MongoDB", "dados persistentes"), (1240, 410, 1530, 595, "Redis", "cache-aside TTL 60s")]
    for x1, y1, x2, y2, name, desc in boxes:
        draw.rounded_rectangle((x1, y1, x2, y2), radius=22, outline=BLUE, width=4, fill="#F7F8FA")
        w = draw.textbbox((0, 0), name, font=regular)[2]
        draw.text((x1 + (x2 - x1 - w) / 2, y1 + 55), name, fill=BLUE, font=regular)
        w = draw.textbbox((0, 0), desc, font=small)[2]
        draw.text((x1 + (x2 - x1 - w) / 2, y1 + 115), desc, fill="#555555", font=small)
    for start, end in [((310,350),(440,350)), ((730,350),(850,350)), ((1110,350),(1240,220)), ((1110,350),(1240,505))]:
        draw.line((*start,*end), fill=ORANGE, width=7)
        x, y = end
        draw.polygon([(x,y), (x-18,y-10), (x-18,y+10)], fill=ORANGE)
    image.save(path)


def create_terminal_image(path):
    source = ROOT / "evidencias" / "marcos-4-6" / "validacao-final.log"
    text = source.read_text(encoding="utf-8") if source.exists() else "Evidência não encontrada."
    lines = text.strip().splitlines()
    img = Image.new("RGB", (1540, max(420, 62 + 32 * (len(lines) + 2))), "#10141c")
    draw = ImageDraw.Draw(img); mono = font(20); heading = font(23, True)
    draw.rounded_rectangle((0, 0, 1540, 52), radius=0, fill="#273142")
    draw.text((22, 14), "Terminal — validação final do JurisDocs", fill="white", font=heading)
    y = 78
    for line in lines:
        color = "#7ee787" if "passed" in line or "healthy" in line else "#e6edf3"
        draw.text((28, y), line[:142], fill=color, font=mono)
        y += 32
    img.save(path)


def set_cell_shading(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr(); shd = OxmlElement("w:shd"); shd.set(qn("w:fill"), fill); tc_pr.append(shd)


def set_cell_margins(cell, top=120, start=120, bottom=120, end=120):
    tc = cell._tc; tc_pr = tc.get_or_add_tcPr(); tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar"); tc_pr.append(tc_mar)
    for m, v in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{m}"))
        if node is None:
            node = OxmlElement(f"w:{m}"); tc_mar.append(node)
        node.set(qn("w:w"), str(v)); node.set(qn("w:type"), "dxa")


def set_repeat_table_header(row):
    tr_pr = row._tr.get_or_add_trPr(); el = OxmlElement("w:tblHeader"); el.set(qn("w:val"), "true"); tr_pr.append(el)


def add_page_number(paragraph):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run("Página ")
    fld = OxmlElement("w:fldSimple"); fld.set(qn("w:instr"), "PAGE"); paragraph._p.append(fld)


def setup_styles(doc):
    section = doc.sections[0]
    section.page_width, section.page_height = Cm(21), Cm(29.7)
    section.top_margin, section.bottom_margin = Cm(3), Cm(2)
    section.left_margin, section.right_margin = Cm(3), Cm(2)
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"; normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    normal.font.size = Pt(12); normal.paragraph_format.line_spacing = 1.5; normal.paragraph_format.space_after = Pt(6)
    for name, size in [("Title", 18), ("Heading 1", 14), ("Heading 2", 12)]:
        style = doc.styles[name]; style.font.name = "Times New Roman"; style._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
        style.font.size = Pt(size); style.font.bold = True; style.font.color.rgb = RGBColor(0,0,0)
        style.paragraph_format.space_before = Pt(12); style.paragraph_format.space_after = Pt(8)
    caption = doc.styles.add_style("Legenda", WD_STYLE_TYPE.PARAGRAPH)
    caption.font.name = "Times New Roman"; caption.font.size = Pt(10); caption.paragraph_format.space_after = Pt(12)
    caption.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for s in doc.sections:
        footer = s.footer.paragraphs[0]; add_page_number(footer)


def p(doc, text, align=WD_ALIGN_PARAGRAPH.JUSTIFY, first=1.25, bold_lead=None):
    paragraph = doc.add_paragraph(); paragraph.alignment = align; paragraph.paragraph_format.first_line_indent = Cm(first) if first else Cm(0)
    if bold_lead and text.startswith(bold_lead):
        paragraph.add_run(bold_lead).bold = True; paragraph.add_run(text[len(bold_lead):])
    else: paragraph.add_run(text)
    return paragraph


def h(doc, text, level=1): return doc.add_heading(text, level=level)


def figure(doc, path, caption, width=15.5):
    doc.add_picture(str(path), width=Cm(width))
    para = doc.add_paragraph(caption, style="Legenda"); para.alignment = WD_ALIGN_PARAGRAPH.CENTER


def table(doc, headers, rows, widths=None):
    tbl = doc.add_table(rows=1, cols=len(headers)); tbl.alignment = WD_TABLE_ALIGNMENT.CENTER; tbl.style = "Table Grid"
    hdr = tbl.rows[0]; set_repeat_table_header(hdr)
    for i, text in enumerate(headers):
        cell = hdr.cells[i]; cell.text = text; set_cell_shading(cell, BLUE.lstrip("#")); set_cell_margins(cell)
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        for run in cell.paragraphs[0].runs: run.font.color.rgb = RGBColor(255,255,255); run.font.bold = True; run.font.size = Pt(10)
    for row in rows:
        cells = tbl.add_row().cells
        for i, text in enumerate(row):
            cells[i].text = str(text); set_cell_margins(cells[i]); cells[i].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            for run in cells[i].paragraphs[0].runs: run.font.size = Pt(10)
    if widths:
        for row in tbl.rows:
            for i, width in enumerate(widths): row.cells[i].width = Cm(width)
    doc.add_paragraph()
    return tbl


def page(doc): doc.add_page_break()


def main():
    architecture = ASSETS / "arquitetura-jurisdocs.png"; terminal = ASSETS / "validacao-final.png"
    create_architecture_image(architecture); create_terminal_image(terminal)
    ui = ROOT / "evidencias" / "capturas" / "01-interface-jurisdocs.png"
    infra = ROOT / "evidencias" / "infraestrutura" / "02-containers-e-healthcheck.png"
    volumes = ROOT / "evidencias" / "infraestrutura" / "03-volumes-e-rede.png"
    doc = Document(); setup_styles(doc)

    # Capa
    for text, size, space in [("4º ANO CIÊNCIA DA COMPUTAÇÃO", 20, 40), ("Faculdades Integradas de Bauru", 17, 54), ("Banco de Dados NoSQL", 14, 65), ("JURISDOCS GERENCIAMENTO DE DOCUMENTOS FICTÍCIOS COM MONGODB REDIS FLASK REACT E PODMAN", 16, 65), ("Luan Alves Camargo Marques", 14, 0)]:
        para = doc.add_paragraph(); para.alignment = WD_ALIGN_PARAGRAPH.CENTER; para.paragraph_format.space_after = Pt(space)
        run = para.add_run(text); run.bold = True; run.font.name = "Times New Roman"; run.font.size = Pt(size)
    for _ in range(5): doc.add_paragraph()
    para = doc.add_paragraph(); para.alignment = WD_ALIGN_PARAGRAPH.CENTER; para.add_run("Bauru\n2026").bold = True
    page(doc)

    # Folha rosto
    para = doc.add_paragraph(); para.alignment = WD_ALIGN_PARAGRAPH.CENTER; para.paragraph_format.space_after = Pt(90); para.add_run("LUAN ALVES CAMARGO MARQUES").bold = True
    para = doc.add_paragraph(); para.alignment = WD_ALIGN_PARAGRAPH.CENTER; para.paragraph_format.space_after = Pt(70); para.add_run("JURISDOCS GERENCIAMENTO DE DOCUMENTOS FICTÍCIOS COM MONGODB REDIS FLASK REACT E PODMAN").bold = True
    para = doc.add_paragraph("Relatório técnico científico apresentado ao curso de Ciência da Computação das Faculdades Integradas de Bauru, na disciplina de Banco de Dados NoSQL, como registro do desenvolvimento de uma aplicação acadêmica para estudo de bancos orientados a documentos e cache em memória.")
    para.paragraph_format.left_indent = Cm(7); para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    for _ in range(10): doc.add_paragraph()
    para = doc.add_paragraph(); para.alignment = WD_ALIGN_PARAGRAPH.CENTER; para.add_run("Bauru\n2026").bold = True
    page(doc)

    # resumo
    h(doc, "RESUMO", 1)
    p(doc, "Este trabalho apresenta o JurisDocs, uma aplicação acadêmica para gerenciamento de documentos jurídicos fictícios desenvolvida com tecnologias NoSQL e executada integralmente em contêineres. O MongoDB foi selecionado como banco de dados principal por representar registros em documentos flexíveis e por suportar índices de unicidade, filtros e busca textual. Redis foi empregado como camada complementar de cache-aside, com tempo de vida de sessenta segundos, invalidação após escrita e degradação controlada quando indisponível. A arquitetura integra Flask e Gunicorn na API, React e Nginx na interface, além de Podman Compose para orquestração. Foram criados cinco registros fictícios, endpoints CRUD, filtros, healthchecks e testes automatizados. A validação demonstrou a sequência de cache MISS, HIT e MISS após atualização, bem como a continuidade de leitura pelo MongoDB com o cache temporariamente indisponível. Conclui-se que a combinação permite demonstrar, de forma reproduzível e segura, a separação entre persistência principal e aceleração de leituras em um cenário de laboratório.")
    p(doc, "Palavras-chave: banco de dados NoSQL; MongoDB; Redis; cache-aside; contêineres; Podman.", first=0, bold_lead="Palavras-chave: ")
    page(doc)

    h(doc, "SUMÁRIO", 1)
    for item in ["1 INTRODUÇÃO", "2 FUNDAMENTAÇÃO TÉCNICA", "3 METODOLOGIA E ARQUITETURA", "4 IMPLEMENTAÇÃO DA SOLUÇÃO", "5 RESULTADOS E VALIDAÇÃO", "6 LIMITAÇÕES E TRABALHOS FUTUROS", "7 CONCLUSÃO", "REFERÊNCIAS", "APÊNDICE A COMANDOS PRINCIPAIS"]:
        para = doc.add_paragraph(item); para.paragraph_format.left_indent = Cm(1.2); para.paragraph_format.space_after = Pt(10)
    page(doc)

    h(doc, "1 INTRODUÇÃO", 1)
    p(doc, "Sistemas de informação lidam com conjuntos de documentos que variam em tamanho, classificação e metadados. O armazenamento relacional pode atender parte desse cenário, porém a modelagem em documentos é adequada quando o registro precisa reunir campos textuais, listas de etiquetas e datas em uma única estrutura. O JurisDocs foi delimitado como ambiente acadêmico: todos os documentos, números, pessoas e descrições são fictícios.")
    p(doc, "O objetivo geral foi implementar e validar uma aplicação web com banco de dados NoSQL que realizasse operações de criar, consultar, atualizar e excluir documentos. Como objetivos específicos, buscou-se: selecionar e justificar uma tecnologia NoSQL principal; modelar uma coleção com índices; disponibilizar uma API; criar uma interface web; utilizar Redis como cache; e produzir evidências de configuração, persistência e testes.")
    p(doc, "O escopo não inclui dados pessoais, processos judiciais reais, autenticação de usuários ou orientação jurídica. Essa delimitação reduz riscos de exposição e mantém o foco pedagógico nas estruturas de dados, nas consultas e no comportamento do cache.")
    h(doc, "2 FUNDAMENTAÇÃO TÉCNICA", 1)
    h(doc, "2.1 MongoDB como base principal", 2)
    p(doc, "MongoDB é um banco de documentos que armazena estruturas semelhantes a JSON, em BSON, e permite que o modelo acompanhe objetos utilizados na aplicação [1]. No JurisDocs, cada documento possui número, título, tipo, descrição, status, etiquetas e datas. A flexibilidade não elimina o controle da aplicação: a API valida os campos obrigatórios e o índice único protege a identificação do documento.")
    h(doc, "2.2 Redis e o padrão cache-aside", 2)
    p(doc, "No padrão cache-aside, a aplicação consulta primeiro o cache; em caso de ausência, consulta a base principal e grava o resultado em memória para leituras posteriores. Atualizações ocorrem na base principal e invalidam as chaves relacionadas [2]. Esse foi o padrão escolhido porque MongoDB continua sendo a fonte de verdade e uma falha de Redis não precisa impedir consultas ao catálogo.")
    page(doc)

    h(doc, "3 METODOLOGIA E ARQUITETURA", 1)
    p(doc, "A pesquisa aplicada foi organizada como laboratório controlado em Fedora Linux. A execução ocorreu com Podman Compose e quatro serviços isolados em uma rede bridge privada: MongoDB, Redis, API e frontend. As portas dos bancos foram vinculadas a loopback, evitando exposição na rede local. A preparação consistiu em subir a infraestrutura, criar usuário de aplicação com escopo restrito, criar índices, inserir massa fictícia e construir os serviços web.")
    figure(doc, architecture, "Figura 1 – Arquitetura de execução do JurisDocs. Fonte: elaboração própria.")
    h(doc, "3.1 Fluxo de dados", 2)
    p(doc, "O navegador acessa o frontend em Nginx. Requisições iniciadas com /api são encaminhadas internamente à API Flask. Para leitura, a API verifica Redis; se a chave não existir, consulta MongoDB e armazena o JSON com TTL de sessenta segundos. Para escrita, MongoDB é atualizado primeiro e as chaves de documento e de listagem são invalidadas. A resposta HTTP explicita a condição da cache no cabeçalho X-Cache.")
    table(doc, ["Elemento", "Função", "Persistência"], [["MongoDB 8.0", "coleção documentos, índices e busca", "volume mongodb-data"], ["Redis 7.4", "cache-aside com AOF", "volume redis-data"], ["Flask + Gunicorn", "API REST e regras de negócio", "imagem API"], ["React + Nginx", "interface e proxy reverso", "imagem frontend"]], [4, 7, 3])
    page(doc)

    h(doc, "4 IMPLEMENTAÇÃO DA SOLUÇÃO", 1)
    h(doc, "4.1 Modelagem e preparação do MongoDB", 2)
    p(doc, "A coleção documentos é inicializada pelo script scripts/02_configurar_bancos.sh. Foram implementados os índices uq_documentos_numero, que impede números repetidos; idx_documentos_texto, que oferece busca por título, descrição e etiquetas; e idx_tipo_status_data, utilizado nos filtros de classificação e ordenação. Cinco registros de demonstração são inseridos somente quando inexistentes, tornando a inicialização idempotente.")
    h(doc, "4.2 API e CRUD", 2)
    p(doc, "A API possui GET /api/health, GET e POST /api/documentos e GET, PUT e DELETE em /api/documentos/<id>. Entradas inválidas recebem HTTP 400, identificadores inexistentes recebem HTTP 404 e tentativa de número duplicado recebe HTTP 409. A resposta de listagem inclui itens e paginação; filtros por texto, tipo, status e etiqueta são interpretados pela API antes da consulta ao MongoDB.")
    figure(doc, infra, "Figura 2 – Serviços MongoDB, Redis, API e frontend em execução com healthchecks. Fonte: evidência local do projeto.")
    page(doc)

    h(doc, "4.3 Cache e tolerância a falhas", 2)
    p(doc, "As chaves de documento usam o prefixo jurisdocs:documento e as listagens usam jurisdocs:listagem:v1 com um resumo hash dos parâmetros. O TTL estabelecido é de sessenta segundos. Uma leitura sem chave responde MISS e popula Redis; leitura repetida responde HIT. Após POST, PUT ou DELETE, a aplicação remove as chaves relevantes usando SCAN, evitando o comando KEYS. Caso o Redis não responda, a API consulta MongoDB e sinaliza BYPASS, preservando a funcionalidade de leitura.")
    figure(doc, terminal, "Figura 3 – Resultado do teste automatizado e healthchecks. Fonte: evidência local do projeto.")
    h(doc, "4.4 Interface web", 2)
    p(doc, "A interface foi implementada com React e compilada por Vite em uma imagem Node. A imagem final usa Nginx para servir os arquivos estáticos e encaminhar /api para o serviço Flask, sem expor a comunicação interna ao navegador. A tela apresenta indicadores de quantidade, filtros, cartões dos documentos, formulário lateral para inclusão ou edição, confirmação de exclusão e indicação do último estado de cache recebido.")
    figure(doc, ui, "Figura 4 – Interface web do JurisDocs com catálogo de registros fictícios. Fonte: captura local do projeto.", 15.5)
    page(doc)

    h(doc, "5 RESULTADOS E VALIDAÇÃO", 1)
    p(doc, "A validação final foi composta por healthchecks dos quatro contêineres, chamada ao endpoint de saúde, inspeção da interface, teste automatizado e simulação de indisponibilidade do cache. Os resultados confirmaram que MongoDB, Redis, API e frontend ficaram no estado healthy e que a página local respondeu HTTP 200.")
    table(doc, ["Cenário", "Procedimento", "Resultado observado"], [["Saúde", "GET /api/health", "api, mongodb e redis com estado ok"], ["CRUD", "Pytest no contêiner API", "criação, leitura, atualização e exclusão aprovadas"], ["Cache", "duas leituras consecutivas", "MISS na primeira e HIT na segunda"], ["Invalidação", "PUT seguido de leitura", "nova leitura com MISS"], ["Fallback", "Redis temporariamente parado", "GET preservado com X-Cache: BYPASS"], ["Persistência", "volumes nomeados e reinício", "massa fictícia preservada"]], [3.1, 6.2, 4.7])
    p(doc, "O teste automatizado retornou 1 passed. Além disso, o script de fallback parou apenas Redis, verificou explicitamente o cabeçalho X-Cache: BYPASS e restaurou o serviço até o estado healthy. Dessa forma, a evidência não se limita ao carregamento da interface: inclui comportamento observável da API sob uma falha controlada.")
    figure(doc, volumes, "Figura 5 – Volumes persistentes e rede isolada definidos pelo Compose. Fonte: evidência local do projeto.")
    page(doc)

    h(doc, "6 LIMITAÇÕES E TRABALHOS FUTUROS", 1)
    p(doc, "Por ser um laboratório local, a solução não implementa autenticação, controle de acesso por perfil, criptografia de tráfego, auditoria de ações, backups automatizados ou observabilidade centralizada. As credenciais existem no arquivo .env local, que é ignorado pelo Git; elas não representam uma política adequada para produção. A invalidação da cache cobre o escopo de uma aplicação única, mas sistemas distribuídos podem exigir eventos, locks ou estratégias adicionais contra picos simultâneos de cache miss.")
    p(doc, "Como continuidade, recomenda-se criar autenticação com papéis, registrar trilha de auditoria, adicionar testes de carga, implementar paginação visual, produzir backup do MongoDB e aplicar secrets de um orquestrador. Também seria possível adicionar anexos armazenados externamente, mantendo no MongoDB apenas metadados e referências.")
    h(doc, "7 CONCLUSÃO", 1)
    p(doc, "O JurisDocs cumpriu a proposta de demonstrar uma aplicação NoSQL funcional baseada em documentos. MongoDB concentrou a persistência e os índices necessários ao catálogo, enquanto Redis acelerou leituras repetidas sem substituir a fonte de verdade. Flask, React, Nginx e Podman permitiram separar responsabilidades e tornar a execução reproduzível. A validação por healthchecks, testes de CRUD, cabeçalhos de cache e fallback confirmou que as funcionalidades essenciais operam corretamente no ambiente definido.")
    page(doc)

    h(doc, "REFERÊNCIAS", 1)
    for ref in ["[1] MONGODB. What is MongoDB? MongoDB Documentation. Disponível em: https://www.mongodb.com/docs/manual/. Acesso em: 02 nov. 2026.", "[2] REDIS. Redis cache-aside. Redis Documentation. Disponível em: https://redis.io/docs/latest/develop/use-cases/cache-aside/. Acesso em: 02 nov. 2026.", "[3] PALLETS. Flask Documentation. Disponível em: https://flask.palletsprojects.com/. Acesso em: 02 nov. 2026.", "[4] REACT. Describing the UI. Disponível em: https://react.dev/learn/describing-the-ui. Acesso em: 02 nov. 2026.", "[5] PODMAN. Podman Documentation. Disponível em: https://docs.podman.io/. Acesso em: 02 nov. 2026.", "[6] PROFESSOR. Projeto Bancos de Dados NoSQL. Material disponibilizado para a disciplina, 2026."]:
        p(doc, ref, first=0)
    h(doc, "APÊNDICE A COMANDOS PRINCIPAIS", 1)
    for command in ["./scripts/01_subir_infraestrutura.sh", "./scripts/02_configurar_bancos.sh", "podman compose -p jurisdocs up -d --build", "podman compose -p jurisdocs ps", "podman compose -p jurisdocs exec -T api python -m pytest -q", "./scripts/03_validar_fallback_redis.sh"]:
        para = doc.add_paragraph(); para.paragraph_format.left_indent = Cm(1); run = para.add_run(command); run.font.name = "Courier New"; run.font.size = Pt(10)
    doc.save(OUT)
    print(OUT)

if __name__ == "__main__": main()
