# -*- coding: utf-8 -*-
"""Monta o artigo StayScore no template IEEE (Conference-template-A4), preservando os estilos do modelo."""
import os, re, shutil, subprocess, sys
from xml.sax.saxutils import escape
from PIL import Image

TPL = sys.argv[1]            # pasta 'un' do template descompactado
FIGS = sys.argv[2]           # pasta com as figuras
OUT = sys.argv[3]            # caminho do .docx final
WORK = OUT + ".work"
shutil.rmtree(WORK, ignore_errors=True); shutil.copytree(TPL, WORK)

# ---------- helpers XML ----------
def r(text, i=False, b=False, sup=False, sz=None, font=None):
    rpr = ""
    if font: rpr += f'<w:rFonts w:ascii="{font}" w:hAnsi="{font}" w:cs="{font}"/>'
    if b: rpr += "<w:b/><w:bCs/>"
    if i: rpr += "<w:i/><w:iCs/>"
    if sz: rpr += f'<w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/>'
    if sup: rpr += '<w:vertAlign w:val="superscript"/>'
    return f'<w:r><w:rPr>{rpr}</w:rPr><w:t xml:space="preserve">{escape(text)}</w:t></w:r>'

def runs(text):
    """Marcação leve: *itálico*, **negrito**."""
    out = []
    for part in re.split(r"(\*\*.+?\*\*|\*.+?\*)", text):
        if not part: continue
        if part.startswith("**"): out.append(r(part[2:-2], b=True))
        elif part.startswith("*"): out.append(r(part[1:-1], i=True))
        else: out.append(r(part))
    return "".join(out)

def p(style, content, ppr_extra=""):
    return f'<w:p><w:pPr><w:pStyle w:val="{style}"/>{ppr_extra}<w:rPr></w:rPr></w:pPr>{content}</w:p>'

def body(text): return p("BodyText", runs(text))
def h1(text): return p("Heading1", r(text))
def h2(text): return p("Heading2", r(text))
def bullet(text): return p("bulletlist", runs(text))
def caption(text): return p("figurecaption", r(" " + text))
def tablehead(text): return p("tablehead", r(text))
def equation(lhs, number):
    return (f'<w:p><w:pPr><w:pStyle w:val="equation"/><w:rPr></w:rPr></w:pPr><w:r><w:rPr></w:rPr><w:tab/></w:r>'
            f'{r(lhs, font="Times New Roman")}<w:r><w:rPr></w:rPr><w:tab/></w:r>{r("(" + str(number) + ")", font="Times New Roman")}</w:p>')

SECT_TITLE = ('<w:p><w:pPr><w:sectPr><w:footerReference w:type="default" r:id="rId2"/><w:footerReference w:type="first" r:id="rId3"/>'
              '<w:type w:val="nextPage"/><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:left="893" w:right="893" w:gutter="0" w:header="0" w:top="540" w:footer="720" w:bottom="1440"/>'
              '<w:pgNumType w:fmt="decimal"/><w:formProt w:val="false"/><w:titlePg/><w:textDirection w:val="lrTb"/><w:docGrid w:type="default" w:linePitch="360" w:charSpace="0"/></w:sectPr></w:pPr></w:p>')
def sect(cols, space, margin=907):
    c = f'<w:cols w:num="{cols}" w:space="{space}" w:equalWidth="true" w:sep="false"></w:cols>' if cols > 1 else ""
    return (f'<w:p><w:pPr><w:sectPr><w:type w:val="continuous"/><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:left="{margin}" w:right="{margin}" w:gutter="0" w:header="0" w:top="540" w:footer="720" w:bottom="1440"/>'
            f'{c}<w:formProt w:val="false"/><w:titlePg/><w:textDirection w:val="lrTb"/><w:docGrid w:type="default" w:linePitch="360" w:charSpace="0"/></w:sectPr></w:pPr></w:p>')
SECT_FINAL = ('<w:sectPr><w:type w:val="continuous"/><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:left="907" w:right="907" w:gutter="0" w:header="0" w:top="540" w:footer="720" w:bottom="1440"/>'
              '<w:cols w:num="2" w:space="360" w:equalWidth="true" w:sep="false"></w:cols><w:formProt w:val="false"/><w:titlePg/><w:textDirection w:val="lrTb"/><w:docGrid w:type="default" w:linePitch="360" w:charSpace="0"/></w:sectPr>')

# ---------- imagens ----------
rels_path = os.path.join(WORK, "word/_rels/document.xml.rels")
rels = open(rels_path, encoding="utf-8").read()
os.makedirs(os.path.join(WORK, "word/media"), exist_ok=True)
img_count = [0]
def image(fname, width_in):
    img_count[0] += 1
    n = img_count[0]; rid = f"rIdImg{n}"
    src = os.path.join(FIGS, fname); dst = f"word/media/image{n}.png"
    shutil.copy(src, os.path.join(WORK, dst))
    w, h = Image.open(src).size
    cx = int(width_in * 914400); cy = int(cx * h / w)
    global rels
    rels = rels.replace("</Relationships>", f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image{n}.png"/></Relationships>')
    return (f'<w:p><w:pPr><w:spacing w:before="120" w:after="0"/><w:jc w:val="center"/></w:pPr><w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0">'
            f'<wp:extent cx="{cx}" cy="{cy}"/><wp:docPr id="{n}" name="Figura {n}"/><a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
            f'<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            f'<pic:nvPicPr><pic:cNvPr id="{n}" name="image{n}.png"/><pic:cNvPicPr/></pic:nvPicPr><pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
            f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>')

# ---------- tabelas ----------
B = '<w:tcBorders><w:top w:val="single" w:sz="2" w:space="0" w:color="000000"/><w:start w:val="single" w:sz="2" w:space="0" w:color="000000"/><w:bottom w:val="single" w:sz="2" w:space="0" w:color="000000"/><w:end w:val="single" w:sz="2" w:space="0" w:color="000000"/></w:tcBorders>'
def table(widths, header, rows, align=None):
    total = sum(widths)
    def cell(w, text, style, jc):
        jcx = f'<w:jc w:val="{jc}"/>' if jc else ""
        return (f'<w:tc><w:tcPr><w:tcW w:w="{w}" w:type="dxa"/>{B}<w:vAlign w:val="center"/></w:tcPr>'
                f'<w:p><w:pPr><w:pStyle w:val="{style}"/><w:spacing w:before="20" w:after="20"/>{jcx}<w:rPr></w:rPr></w:pPr>{runs(text)}</w:p></w:tc>')
    x = (f'<w:tbl><w:tblPr><w:tblW w:w="{total}" w:type="dxa"/><w:jc w:val="center"/><w:tblLayout w:type="fixed"/>'
         f'<w:tblCellMar><w:top w:w="0" w:type="dxa"/><w:start w:w="60" w:type="dxa"/><w:bottom w:w="0" w:type="dxa"/><w:end w:w="60" w:type="dxa"/></w:tblCellMar></w:tblPr>'
         f'<w:tblGrid>{"".join(f"<w:gridCol w:w=\"{w}\"/>" for w in widths)}</w:tblGrid>')
    x += '<w:tr><w:trPr><w:tblHeader w:val="true"/><w:cantSplit w:val="true"/></w:trPr>' + "".join(cell(w, t, "tablecolhead", "center") for w, t in zip(widths, header)) + "</w:tr>"
    for row in rows:
        x += '<w:tr><w:trPr><w:cantSplit w:val="true"/></w:trPr>' + "".join(cell(w, t, "tablecopy", (align[i] if align else None)) for i, (w, t) in enumerate(zip(widths, row))) + "</w:tr>"
    return x + "</w:tbl>" + '<w:p><w:pPr><w:pStyle w:val="Normal"/><w:spacing w:before="0" w:after="120"/></w:pPr></w:p>'

# =====================================================================
#  CONTEÚDO
# =====================================================================
X = []
X.append(p("papertitle", r("StayScore: Inteligência de Mercado para Aluguel por Temporada a partir de Dados Abertos")))
X.append(SECT_TITLE)

AUTHORS = [("1", "st", "Bernardo Miller"), ("2", "nd", "Claudia Abajo"), ("3", "rd", "Enrico Astolfi"), ("4", "th", "Gabriel Maneiro"), ("5", "th", "Gabriel Martins")]
for idx, (n, suf, name) in enumerate(AUTHORS):
    colbr = '<w:r><w:br w:type="column"/></w:r>' if idx in (2, 4) else ''
    X.append('<w:p><w:pPr><w:pStyle w:val="Author"/><w:keepLines/><w:spacing w:before="100" w:after="40"/><w:rPr><w:sz w:val="18"/><w:szCs w:val="18"/></w:rPr></w:pPr>'
             + colbr + r(n, sz=18) + r(suf, sup=True, sz=18) + r(" " + name, sz=18) + '<w:r><w:rPr><w:sz w:val="18"/></w:rPr><w:br/></w:r>'
             + r("Disciplina de Análise de Dados", i=True, sz=18) + '<w:r><w:rPr><w:sz w:val="18"/></w:rPr><w:br/></w:r>'
             + r("Ibmec – Campus Barra da Tijuca", i=True, sz=18) + '<w:r><w:rPr><w:sz w:val="18"/></w:rPr><w:br/></w:r>'
             + r("Rio de Janeiro, Brasil", sz=18) + '<w:r><w:rPr><w:sz w:val="18"/></w:rPr><w:br/></w:r>'
             + r("gabrielpmaneiro@gmail.com" if name == "Gabriel Maneiro" else "[e-mail]", sz=18) + "</w:p>")
X.append(sect(3, 720, margin=893))

X.append(p("Abstract", r("Resumo", i=True) + r("—O pequeno anfitrião brasileiro decide quanto cobrar e se vale a pena anunciar um imóvel por temporada sem apoio de dados, enquanto as ferramentas profissionais existentes são caras, cobradas em dólar e pouco transparentes. Este artigo apresenta o StayScore, uma aplicação web progressiva (PWA) que, a partir de um endereço e das características de um imóvel, identifica anúncios comparáveis em um raio configurável, estima a diária média, a taxa de ocupação e a receita mensal e sintetiza o resultado em uma nota de 0 a 100. O sistema utiliza a base aberta do Inside Airbnb para o Rio de Janeiro (48.247 anúncios, dos quais 40.261 ativos, publicação de setembro de 2026), geocodificação pelo Nominatim/OpenStreetMap e um modelo transparente de pontuação que combina ocupação (45%), receita (35%) e competição (20%), todos relativos ao mercado da cidade. Uma pesquisa de intenção com 13 respondentes orientou o desenho do produto: 84,6% precificam sem ferramenta de dados e 77% demonstraram disposição a pagar por uma nota acompanhada dos dados que a sustentam. Os resultados mostram que o MVP devolve, para qualquer endereço da cidade, uma resposta objetiva e auditável sobre preço, ocupação e receita, com os comparáveis, o raio, o tamanho da amostra e a data de referência sempre visíveis. Discutem-se as limitações da ocupação estimada e da dependência de fonte única e apresenta-se o plano de evolução do produto.")))
X.append(p("Keywords", r("Palavras-chave—aluguel por temporada, dados abertos, Inside Airbnb, inteligência de mercado, análise geoespacial, aplicação web progressiva")))

# ---------------- I. Introdução / Motivação ----------------
X.append(h1("Introdução"))
X.append(body("Quem investe em um imóvel ou decide anunciá-lo para aluguel por temporada precisa responder, antes de qualquer decisão, a três perguntas: quanto cobrar por diária, por quanto tempo o imóvel ficará ocupado e quanto isso representará de receita ao final do mês. No Brasil, essas respostas são obtidas de forma informal. O anfitrião consulta alguns anúncios da vizinhança na própria plataforma, estima um valor e só descobre se acertou depois de um trimestre de reservas, muitas vezes com o calendário vazio."))
X.append(body("O mercado, por sua vez, cresce em ritmo acelerado. As reservas do Brasil no Airbnb avançaram mais de 20% por três trimestres consecutivos, colocando o país entre os três mercados que mais crescem no mundo, e o Rio de Janeiro reunia 48,2 mil anúncios ativos em junho de 2026, alta de 11% em um ano [1], [2]. Apesar disso, o pequeno anfitrião e o investidor iniciante não dispõem de uma ferramenta acessível, em português e em reais, que transforme dados públicos em uma resposta objetiva sobre um endereço específico. As soluções profissionais, como AirDNA, PriceLabs e Wheelhouse, atendem operadoras e fundos, custam a partir de US$ 125 por mês e concentram-se na diária, sem medir ocupação nem receita esperada [3]–[5]."))
X.append(body("A motivação deste trabalho está justamente nessa lacuna: os dados existem e são públicos, mas não chegam ao pequeno anfitrião em um formato simples, confiável e auditável. O StayScore converte dados abertos do mercado em uma nota de 0 a 100 para qualquer endereço do Rio de Janeiro, acompanhada de três indicadores objetivos (ocupação média mensal, diária média estimada e receita mensal projetada) e de toda a evidência que sustenta o cálculo: os imóveis comparáveis, o raio de busca, o tamanho da amostra e a data de referência dos dados."))
X.append(body("Este artigo documenta o projeto do ponto de vista técnico e de produto. A Seção II apresenta o diferencial em relação às alternativas existentes; a Seção III descreve a base de dados e o seu tratamento; a Seção IV detalha a arquitetura e o método de cálculo; a Seção V apresenta as telas do aplicativo; a Seção VI reúne os resultados obtidos com a base real e a pesquisa de validação; a Seção VII discute riscos e limitações; e a Seção VIII traz as conclusões e os trabalhos futuros."))

# ---------------- II. Diferencial ----------------
X.append(h1("Trabalhos Relacionados e Diferencial"))
X.append(body("A Tabela I compara as alternativas disponíveis hoje ao anfitrião com o posicionamento do StayScore. Três fatores, que nenhum concorrente reúne ao mesmo tempo, sustentam o diferencial do produto."))
X.append(tablehead("Comparativo entre as alternativas existentes e o StayScore"))
X.append(table([1150, 1500, 2210], ["Ferramenta", "Público", "Limite principal"], [
    ["AirDNA", "Operadoras profissionais e fundos imobiliários", "Planos a partir de US$ 125 por mês, fora do orçamento do pequeno anfitrião."],
    ["PriceLabs e Wheelhouse", "Gestoras profissionais de portfólio", "Cobrança em dólar e foco apenas na diária; não medem ocupação nem receita esperada."],
    ["Smart Pricing (Airbnb)", "Qualquer anfitrião dentro da plataforma", "Gratuito, mas tende a manter a diária perto do mínimo, sem explicar o motivo do valor."],
    ["Planilha e pesquisa manual", "Anfitrião iniciante", "Consome até 3 horas por mês; 15,4% dos respondentes desistem de pesquisar."],
    ["**StayScore**", "**Pequeno anfitrião e investidor iniciante brasileiro**", "**Nota transparente de ocupação, receita e competição, em português e em reais, com raio e amostra sempre visíveis.**"]]))
X.append(h2("Transparência antes de tudo"))
X.append(body("A nota nunca é uma caixa-preta. Toda pontuação pode ser detalhada: o aplicativo exibe os imóveis comparáveis utilizados, o raio de busca, o tamanho da amostra, o filtro de similaridade aplicado, a data de referência dos dados e a contribuição de cada componente para a nota final. O usuário consegue, portanto, verificar como a nota foi construída e contestá-la com base nos mesmos dados."))
X.append(h2("Acessibilidade real"))
X.append(body("O produto é desenhado para quem não tem escala para contratar ferramentas internacionais nem tempo para pesquisa manual. A interface é em português, os valores são apresentados em reais e o aplicativo roda no navegador do celular ou do computador, sem instalação por loja de aplicativos e sem custo de distribuição. O modelo de receita prevê uma camada gratuita, uma assinatura mensal entre R$ 39 e R$ 49 e a venda de relatórios avulsos."))
X.append(h2("Ocupação no centro, não apenas preço"))
X.append(body("A pesquisa de validação indicou que a principal dor do usuário é saber se o imóvel ficará ocupado; o preço, o anfitrião já consegue estimar observando os vizinhos. Taxa de ocupação e receita mensal estimada empataram como os indicadores mais úteis (38,5% dos votos cada), enquanto a diária média isolada não recebeu nenhum voto. Por isso, no StayScore, a diária funciona como insumo do cálculo e não como entregável final, e a ocupação recebe o maior peso na composição da nota."))

# ---------------- III. Base de dados ----------------
X.append(h1("Descrição da Base de Dados"))
X.append(h2("Fonte principal: Inside Airbnb"))
X.append(body("O Inside Airbnb é um projeto independente que publica, periodicamente, dados abertos dos anúncios do Airbnb por cidade, com cobertura do Rio de Janeiro [6]. Foi escolhido como fonte principal por três motivos: custo zero, permissão de uso acadêmico e disponibilidade de dados georreferenciados, requisito essencial para a busca de comparáveis por raio. Alternativas como o AirDNA (planos a partir de US$ 125 por mês) e *scrapers* de terceiros (custo variável e fragilidade jurídica da coleta automatizada) foram descartadas para o MVP."))
X.append(body("Foram utilizados os dois arquivos de anúncios da publicação de setembro de 2026 (data da última avaliação registrada: 29 de setembro de 2026): o *listings.csv* resumido, com 19 colunas, e o *listings.csv.gz* detalhado, com 90 colunas. Ambos contêm 48.247 registros. A Tabela II lista os campos efetivamente consumidos pelo StayScore."))
X.append(tablehead("Campos do Inside Airbnb utilizados pelo StayScore"))
X.append(table([1500, 3360], ["Campo", "Uso no sistema"], [
    ["id, name, picture_url", "Identificação, título e foto do anúncio nos cartões de comparáveis."],
    ["latitude, longitude, neighbourhood_cleansed", "Busca por raio (distância Haversine) e rótulo de bairro."],
    ["room_type, bedrooms, accommodates", "Filtro de similaridade: tipo de imóvel, quartos e capacidade."],
    ["amenities", "Marcação de oito amenidades (Wi-Fi, ar-condicionado, piscina, estacionamento, cozinha, vista para o mar, *pet friendly*, academia)."],
    ["price", "Diária anunciada, em reais; base da diária mediana da região."],
    ["availability_365", "Dias livres no calendário dos próximos 365 dias; insumo da ocupação estimada."],
    ["reviews_per_month, number_of_reviews, number_of_reviews_ltm", "Frequência de avaliações, usada como *proxy* de reservas e como critério de atividade do anúncio."],
    ["estimated_occupancy_l365d", "Estimativa de ocupação (dias por ano) publicada pelo próprio Inside Airbnb, usada na base detalhada."]]))
X.append(h2("Tratamento e filtro de atividade"))
X.append(body("O tratamento dos dados foi implementado em Python e gera um arquivo compacto consumido diretamente pelo aplicativo. Foram mantidos apenas anúncios de imóvel inteiro ou quarto privativo (quartos compartilhados e de hotel foram excluídos), com preço válido entre R$ 1 e R$ 20.000 e coordenadas presentes. Anúncios sem nenhuma avaliação nos últimos doze meses e com calendário totalmente livre (365 dias ou mais de 360 disponíveis) foram tratados como inativos e descartados, pois distorceriam tanto a ocupação quanto a densidade de competição. O resultado é uma base de **40.261 anúncios ativos**, dos quais 33.843 (84%) são imóveis inteiros."))
X.append(body("A Tabela III resume a distribuição por bairro. Copacabana concentra sozinha um terço da oferta ativa da cidade, seguida por Ipanema, Barra da Tijuca e Centro. A diária mediana da cidade é de R$ 444 e a ocupação estimada mediana é de 30%, com quartis de 14% e 42%."))
X.append(tablehead("Oferta ativa, diária e ocupação estimada por bairro (publicação de set. 2026)"))
X.append(table([1800, 1000, 1000, 1060], ["Bairro", "Anúncios ativos", "Diária mediana (R$)", "Ocupação est. mediana"], [
    ["Copacabana", "13.170", "455", "32%"], ["Ipanema", "3.454", "743", "33%"], ["Barra da Tijuca", "2.954", "614", "29%"], ["Centro", "2.944", "284", "31%"],
    ["Recreio dos Bandeirantes", "1.959", "415", "22%"], ["Botafogo", "1.718", "394", "32%"], ["Leblon", "1.662", "810", "32%"], ["Jacarepaguá", "1.496", "408", "23%"],
    ["**Cidade (40.261 ativos)**", "**40.261**", "**444**", "**30%**"]], align=[None, "center", "center", "center"]))
X.append(h2("Estimativa de ocupação"))
X.append(body("As plataformas não divulgam a ocupação real dos imóveis. Seguindo a abordagem do próprio Inside Airbnb [6], a ocupação de cada anúncio é estimada a partir de dois sinais: a disponibilidade do calendário e a frequência de avaliações, usada como indicador indireto (*proxy*) do volume de reservas, assumindo-se que cerca de metade das estadias gera uma avaliação e que a estadia média é de 3,5 noites. Quando a base detalhada está disponível, a estimativa anual publicada pelo Inside Airbnb (*estimated_occupancy_l365d*, em dias) é combinada com o calendário, conforme (1), em que *d* é a estimativa anual em dias e *a* é o número de dias disponíveis nos próximos 365 dias."))
X.append(equation("o = 0,6 · (d / 365) + 0,4 · (1 − a / 365)", 1))
X.append(body("Na ausência da estimativa anual (base resumida), a ocupação é a média simples entre o sinal do calendário e o sinal das avaliações, dado por (2), em que *m* é o número de avaliações por mês."))
X.append(equation("o = 0,5 · (1 − a / 365) + 0,5 · min(1, (m / 0,5) · 3,5 / 30,4)", 2))
X.append(body("Em todos os casos a ocupação é limitada ao intervalo de 5% a 97%, e a receita mensal de cada anúncio é obtida por *receita = preço × 30,4 × o*."))
X.append(h2("Geocodificação"))
X.append(body("O endereço informado pelo usuário é convertido em coordenadas pelo Nominatim, serviço de geocodificação baseado no OpenStreetMap [7], [8], com a busca restrita à caixa delimitadora do município do Rio de Janeiro. Como contingência para falhas de rede, o aplicativo mantém um dicionário local com os principais logradouros e os centroides de 30 bairros, que também aceita coordenadas digitadas diretamente."))

# ---------------- IV. Arquitetura ----------------
X.append(h1("Arquitetura e Método de Cálculo"))
X.append(body("O fluxo de uso do StayScore está organizado em quatro etapas, ilustradas na Fig. 1: (1) entrada do endereço e das características do imóvel; (2) geocodificação e busca de comparáveis por raio; (3) cálculo da diária, da ocupação e da receita a partir da amostra; e (4) apresentação da nota, do mapa e dos cartões de indicadores."))
X.append(image("arquitetura.png", 2.3))
X.append(caption("Pipeline de processamento do StayScore, da entrada do endereço à nota final."))
X.append(h2("Stack tecnológico"))
X.append(body("O relatório técnico previa uma arquitetura com Python (Pandas e GeoPandas) para o tratamento de dados, PostgreSQL com PostGIS para consultas georreferenciadas, FastAPI no back-end e Streamlit ou React no front-end. Para o MVP, adotou-se uma variante mais simples e de custo zero de operação: o tratamento dos dados permanece em Python e produz um arquivo estático compacto (cerca de 3 MB comprimidos) com os 40.261 anúncios ativos; a busca por raio, o filtro de similaridade e o cálculo da nota rodam inteiramente no navegador, em JavaScript; e o front-end é uma aplicação web progressiva (PWA) publicada no GitHub Pages, com *service worker* para funcionamento *offline* e instalação na tela inicial do celular. O mapa usa a biblioteca Leaflet com camadas do OpenStreetMap. Essa decisão eliminou a necessidade de servidor e banco de dados na fase de validação, sem alterar o método de cálculo, que pode ser migrado para a API prevista quando a base crescer para outras cidades."))
X.append(h2("Busca de comparáveis"))
X.append(body("Para cada consulta, o sistema calcula a distância Haversine entre o endereço e todos os anúncios ativos e retém os que estão dentro do raio escolhido (500 m, 1 km ou 2 km). Sobre esse conjunto aplica-se um filtro de similaridade com relaxamento progressivo: primeiro, mesmo tipo de imóvel, mesmo número de quartos e capacidade com diferença de até um hóspede; se a amostra tiver menos de oito anúncios, admitem-se quartos com diferença de até um e capacidade com diferença de até dois; em seguida, apenas o mesmo tipo de imóvel; por fim, todos os anúncios do raio. O nível de filtro efetivamente utilizado é exibido ao usuário."))
X.append(body("Os preços da amostra passam por remoção de *outliers* pelo critério do intervalo interquartil (valores fora de [Q1 − 1,5·IQR; Q3 + 1,5·IQR]). Em bairros muito densos, como Copacabana e Ipanema, mais de cinco mil anúncios podem cair em um raio de 1 km; nesses casos o cálculo utiliza os 300 comparáveis mais próximos, e a lista de comparativos mostra os 60 mais próximos, sempre com a indicação do total."))
X.append(h2("Indicadores"))
X.append(bullet("**Diária média estimada:** mediana dos preços da amostra, acompanhada do intervalo interquartil (\"pode variar de … a …\")."))
X.append(bullet("**Ocupação média mensal:** mediana das ocupações estimadas da amostra, ajustada em até ±8 pontos percentuais pelo efeito das amenidades do imóvel do usuário (ar-condicionado, piscina, vista para o mar e estacionamento), medido na própria amostra pela diferença de ocupação entre anúncios com e sem cada amenidade."))
X.append(bullet("**Receita mensal projetada:** diária mediana multiplicada pelo número de dias ocupados em um mês de 30,4 dias, informado ao usuário (\"baseado em N dias ocupados\")."))
X.append(bullet("**Competição:** quantidade de anúncios ativos do mesmo tipo por km² dentro do raio."))
X.append(h2("Composição da nota"))
X.append(body("O Stay Score é a combinação ponderada de três componentes normalizados entre 0 e 1, conforme (3). Os pesos refletem a prioridade identificada na pesquisa de validação: ocupação em primeiro lugar, receita em seguida e competição como fator de contexto."))
X.append(equation("S = 100 · (0,45 · O + 0,35 · R + 0,20 · C)", 3))
X.append(body("O componente de ocupação *O* é obtido a partir do percentil da ocupação estimada do imóvel entre todos os anúncios ativos da cidade, reescalado do intervalo [15%; 95%] para [0; 1]. O componente de receita *R* é calculado da mesma forma, a partir do percentil da receita mensal projetada, reescalado de [20%; 95%]. O uso de percentis torna a nota relativa ao mercado do Rio de Janeiro na data de referência, em vez de depender de limiares absolutos que variam de cidade para cidade. O componente de competição *C* usa escala logarítmica da densidade *ρ* (anúncios/km²), conforme (4), valendo 1 para 10 anúncios/km² ou menos e 0 para cerca de 4.000 anúncios/km², densidade observada em Copacabana."))
X.append(equation("C = 1 − (log10(max(ρ, 1)) − 1) / 2,6, limitado a [0; 1]", 4))
X.append(body("A nota é classificada em cinco faixas: Excelente (75 a 100), Muito Bom (60 a 74), Bom (45 a 59), Regular (30 a 44) e Baixo (abaixo de 30). O painel de transparência mostra os pontos obtidos em cada componente (por exemplo, 36/45 em ocupação), o percentil correspondente e a densidade de competição."))

# ---------------- V. Telas ----------------
X.append(h1("Telas do Aplicativo"))
X.append(body("O aplicativo possui três telas, mostradas nas Figs. 2 e 3. A tela de entrada recebe o endereço (com sugestões de exemplos), o tipo de imóvel, o número de quartos, a capacidade, o raio de busca e as amenidades. A tela de resultado apresenta a nota em destaque, com o medidor em arco e a classificação, o endereço analisado, os três cartões de indicadores e o mapa dos comparáveis dentro do raio, com o imóvel do usuário marcado em vermelho. A tela de comparativos detalhados exibe cada imóvel da amostra, com foto, distância, quartos, capacidade e número de avaliações, lado a lado com a mediana da região em um minigráfico de três grupos (diária, ocupação e receita), permitindo ao usuário entender como a nota foi construída. Ao final da lista, dicas geradas a partir da própria amostra orientam o anúncio, como a diferença de ocupação entre imóveis com e sem ar-condicionado ou a faixa de preço praticada pelos 25% mais ocupados."))
X.append(image("fig_telas1.png", 3.2))
X.append(caption("Tela de entrada e tela de resultado do StayScore no celular, com a base real de setembro de 2026: análise para a Rua Visconde de Pirajá, 500, Ipanema, geocodificada pelo Nominatim junto à Praça General Osório, na divisa com o Arpoador (nota 61, cartões de indicadores e mapa OpenStreetMap com os comparáveis no raio de 1 km)."))
X.append(image("fig_telas2.png", 3.2))
X.append(caption("Tela de comparativos detalhados no celular, com foto, distância e minigráfico de cada imóvel versus a mediana da região, e painel \"Como a nota foi construída\"."))
X.append(body("O painel de transparência (Fig. 3, à direita) é acessível pelo ícone de informação na tela de resultado. Ele apresenta o tamanho da amostra em relação ao total de anúncios no raio, o raio de busca, o filtro de similaridade efetivamente aplicado, a data de referência da publicação do Inside Airbnb e a contribuição de cada componente para a nota, além de uma nota metodológica sobre a ocupação estimada."))
X.append(body("A interface foi construída como PWA: ao abrir o endereço público do aplicativo no celular e escolher \"Adicionar à Tela de Início\", ele passa a abrir em tela cheia, com ícone próprio, e continua funcionando sem conexão com a última base carregada. Atualizações publicadas no repositório são aplicadas automaticamente na abertura seguinte."))

# ---------------- VI. Resultados ----------------
X.append(h1("Resultados"))
X.append(h2("Comportamento da nota com a base real"))
X.append(body("A Tabela IV apresenta o resultado do StayScore para um mesmo perfil de imóvel (imóvel inteiro, um quarto, dois hóspedes, com Wi-Fi, ar-condicionado e cozinha) em oito endereços da cidade, com raio de 1 km e a base de setembro de 2026. Os valores ilustram o comportamento esperado do método: Ipanema combina a maior ocupação estimada (42%) com diária elevada e alcança a maior nota (61, Muito Bom), apesar da competição extrema (cerca de 1.700 anúncios/km²); Botafogo obtém nota semelhante à de Leblon com diária quase metade, porque a ocupação e a menor densidade compensam; e Barra da Tijuca e Recreio, com poucos comparáveis de um quarto e ocupação estimada próxima de 10%, recebem notas baixas, sinalizando que, para esse perfil, o investimento exige cautela."))
X.append(tablehead("Stay Score para imóvel inteiro de 1 quarto e 2 hóspedes em oito endereços (raio de 1 km, set. 2026)"))
X.append(table([1040, 640, 600, 780, 760, 470, 570], ["Bairro", "Amostra (no raio)", "Diária (R$)", "Ocupação", "Receita (R$/mês)", "Nota", "Faixa"], [
    ["Ipanema", "300 (≈6.000)", "491", "42%", "6.383", "**61**", "Muito Bom"],
    ["Botafogo", "139 (662)", "353", "39%", "4.236", "**59**", "Bom"],
    ["Leblon", "300 (1.686)", "609", "32%", "6.090", "**54**", "Bom"],
    ["Copacabana", "300 (1.766)", "413", "34%", "4.130", "**48**", "Bom"],
    ["Tijuca", "20 (181)", "344", "28%", "3.096", "**44**", "Regular"],
    ["Lapa", "300 (2.851)", "282", "29%", "2.538", "**30**", "Regular"],
    ["Barra da Tijuca", "10 (224)", "382", "11%", "1.145", "**17**", "Baixo"],
    ["Recreio", "10 (200)", "391", "10%", "1.172", "**16**", "Baixo"]], align=[None, "center", "center", "center", "center", "center", "center"]))
X.append(body("Dois efeitos merecem destaque. Primeiro, a importância do filtro de similaridade: em Ipanema, a diária mediana de todos os imóveis inteiros no raio supera R$ 800, mas cai para R$ 491 quando se consideram apenas imóveis de um quarto para dois hóspedes, que é o valor relevante para o usuário. Segundo, a sensibilidade ao tamanho da amostra: em Tijuca, Barra e Recreio a amostra ficou entre 10 e 20 anúncios, o que o aplicativo sinaliza explicitamente para que o usuário amplie o raio antes de decidir."))
X.append(h2("Pesquisa de validação com o mercado"))
X.append(body("Para orientar o desenho do produto, o grupo aplicou um formulário a 13 respondentes do ecossistema de aluguel por temporada, entre pequenos anfitriões e investidores iniciantes. Os principais achados foram: 84,6% precificam hoje sem nenhuma ferramenta de dados; taxa de ocupação e receita mensal estimada empataram como os indicadores mais úteis, com 38,5% dos votos cada; a diária média da região, isoladamente, não recebeu nenhum voto; e 15,4% afirmaram desistir de pesquisar preços manualmente."))
X.append(body("A pesquisa também confirmou a disposição a pagar quando a nota vem acompanhada dos dados que a sustentam (Fig. 4): 46% pagariam pela assinatura, 31% apenas pelo relatório avulso e 23% não pagariam hoje, ou seja, cerca de 77% da amostra demonstrou alguma disposição a pagar."))
X.append(image("grafico_pagar.png", 3.1))
X.append(caption("Disposição a pagar dos respondentes da pesquisa de validação (n = 13)."))
X.append(body("A amostra é pequena e não probabilística; os resultados servem para orientar o desenho do produto, mas não podem ser generalizados para o mercado como um todo."))
X.append(h2("Cronograma e entrega"))
X.append(body("O projeto foi executado em 75 dias, de 27 de agosto a 10 de novembro de 2026, em três fases: planejamento (definição do conceito, decisão da base de dados, formulário, pesquisa de mercado, *storyboard* e relatório técnico), desenvolvimento (back-end, front-end, integração, revisão de código e teste fechado) e finalização (videotutorial, artigo e entrega). A meta do MVP, entregar uma nota funcional para qualquer endereço do Rio de Janeiro calculada a partir de dados abertos e pronta para teste com anfitriões reais, foi atingida com a publicação do aplicativo e do código-fonte em repositório aberto [9]."))

# ---------------- VII. Riscos ----------------
X.append(h1("Riscos e Limitações do Projeto"))
X.append(bullet("**Ocupação estimada, não observada.** A taxa de ocupação é inferida da disponibilidade do calendário, da frequência de avaliações e da estimativa anual do Inside Airbnb. Datas bloqueadas pelo anfitrião podem ser confundidas com reservas, e a taxa de avaliação varia entre perfis de hóspede. A ocupação mediana estimada da cidade (30%) deve ser lida como indicador relativo, útil para comparar endereços, e não como medida absoluta."))
X.append(bullet("**Dependência de fonte única.** O MVP depende das publicações periódicas do Inside Airbnb. A atualização dos resultados fica condicionada à frequência dessas publicações, razão pela qual a data de referência é sempre exibida ao usuário. Mudanças no formato dos arquivos exigem ajuste do *script* de tratamento."))
X.append(bullet("**Cobertura geográfica.** O MVP contempla apenas o Rio de Janeiro. A expansão para outras cidades depende da disponibilidade de dados abertos equivalentes."))
X.append(bullet("**Amostras pequenas em bairros de baixa densidade.** Em regiões com poucos anúncios do perfil consultado, a nota é calculada sobre dez ou vinte comparáveis e torna-se sensível a casos isolados. O aplicativo informa o tamanho da amostra e permite ampliar o raio, mas o usuário precisa interpretar essa informação."))
X.append(bullet("**Validação de mercado preliminar.** A pesquisa contou com 13 respondentes; uma amostra maior será necessária antes de decisões definitivas sobre preço e funcionalidades."))
X.append(bullet("**Carga inicial no celular.** A base compacta tem cerca de 3 MB comprimidos; a primeira abertura leva alguns segundos em conexões lentas, embora as seguintes usem o cache local."))
X.append(bullet("**Aspectos legais e de uso.** Os dados do Inside Airbnb são de uso livre para fins não comerciais e acadêmicos; a oferta comercial do produto exigirá revisar as condições de uso da fonte ou negociar acesso a dados licenciados."))

# ---------------- VIII. Conclusão e trabalhos futuros ----------------
X.append(h1("Conclusão e Trabalhos Futuros"))
X.append(body("O StayScore nasceu de uma pergunta simples que todo anfitrião iniciante faz e ninguém responde com dados: vale a pena anunciar o meu imóvel e quanto ele pode render? O projeto mostrou que é possível responder a essa pergunta usando apenas dados abertos, de forma transparente e em português, com uma nota que o usuário entende em segundos e pode conferir em detalhe se quiser. O aplicativo está publicado, funciona no celular como um app e cobre todos os endereços do Rio de Janeiro."))
X.append(body("A pesquisa com anfitriões confirmou que a maior dúvida não é o preço da diária, e sim se o imóvel vai ficar ocupado. Por isso a ocupação é o centro da nota, e a diária aparece como apoio. A arquitetura simples, sem servidor, permitiu entregar o MVP dentro do prazo e do orçamento de um projeto acadêmico e deixou o caminho aberto para as próximas etapas."))
X.append(body("Para o futuro, o grupo enxerga as seguintes ideias de evolução:"))
X.append(bullet("**Mais cidades.** Levar o StayScore para outras cidades turísticas do Brasil que também têm dados abertos disponíveis, como Belo Horizonte, e depois para destinos no exterior. Como a nota é sempre comparada ao mercado da própria cidade, o método funciona em qualquer lugar."))
X.append(bullet("**Ocupação por época do ano.** Hoje a nota reflete uma média anual. A ideia é mostrar como a ocupação e a receita mudam ao longo do ano, destacando períodos como réveillon, carnaval e férias, para que o anfitrião planeje a diária de cada temporada."))
X.append(bullet("**Acompanhar o imóvel ao longo do tempo.** Guardar o histórico das análises e avisar o usuário quando a diária ou a ocupação da sua região mudar, que é o principal benefício previsto para a assinatura."))
X.append(bullet("**Relatório completo.** Permitir baixar, a partir de uma análise, um relatório em PDF com os comparáveis, os gráficos e as recomendações, pensado para quem está decidindo comprar ou reformar um imóvel."))
X.append(bullet("**Novas telas e recursos.** Comparar dois endereços lado a lado, um mapa de calor mostrando os bairros mais rentáveis, um simulador em que o usuário testa uma diária e vê o efeito na ocupação e na receita, modo escuro e um tutorial na primeira abertura explicando como ler a nota."))
X.append(bullet("**Ouvir mais anfitriões.** Fazer uma nova pesquisa com mais respondentes e coletar a opinião dos usuários dentro do próprio aplicativo, para ajustar a nota, as funcionalidades e o preço da assinatura."))
X.append(body("Em todas essas evoluções, o princípio continua o mesmo: a nota nunca será uma caixa-preta. O raio, a amostra e a data dos dados seguirão sempre visíveis, para que o anfitrião confie no número que orienta a sua decisão."))

# ---------------- Referências ----------------
X.append(p("Heading1", r("Referências"), '<w:numPr><w:ilvl w:val="0"/><w:numId w:val="0"/></w:numPr>'))
REFS = [
    "Airbnb, \"Relatório de resultados do terceiro trimestre de 2025,\" Airbnb Investor Relations, 2025. [Online]. Disponível em: https://investors.airbnb.com",
    "Inside Airbnb, \"Rio de Janeiro: get the data,\" publicação de jun. 2026. [Online]. Disponível em: https://insideairbnb.com/rio-de-janeiro",
    "AirDNA, \"Pricing and plans,\" 2026. [Online]. Disponível em: https://www.airdna.co",
    "PriceLabs, \"Dynamic pricing for vacation rentals,\" 2026. [Online]. Disponível em: https://hello.pricelabs.co",
    "Wheelhouse, \"Revenue management for short-term rentals,\" 2026. [Online]. Disponível em: https://www.usewheelhouse.com",
    "Inside Airbnb, \"About Inside Airbnb: data assumptions and the occupancy model,\" acesso em set. 2026. [Online]. Disponível em: https://insideairbnb.com/data-assumptions",
    "Nominatim, \"Open-source geocoding with OpenStreetMap data,\" acesso em set. 2026. [Online]. Disponível em: https://nominatim.org",
    "OpenStreetMap Foundation, \"OpenStreetMap,\" acesso em set. 2026. [Online]. Disponível em: https://www.openstreetmap.org",
    "B. Miller, C. Abajo, E. Astolfi, G. Maneiro e G. Martins, \"StayScore: código-fonte e aplicativo,\" repositório GitHub, nov. 2026. [Online]. Disponível em: https://github.com/gabrielpmaneiro/stayscore",
    "B. Miller, C. Abajo, E. Astolfi, G. Maneiro e G. Martins, \"StayScore: inteligência de mercado para aluguel por temporada – relatório técnico do plano de negócios,\" set. 2026.",
]
for ref in REFS:
    X.append(f'<w:p><w:pPr><w:pStyle w:val="references"/><w:numPr><w:ilvl w:val="0"/><w:numId w:val="5"/></w:numPr><w:ind w:hanging="354" w:start="354" w:end="0"/><w:rPr></w:rPr></w:pPr>{r(ref)}</w:p>')
X.append(SECT_FINAL)

# ---------- grava ----------
doc_path = os.path.join(WORK, "word/document.xml")
doc = open(doc_path, encoding="utf-8").read()
head = doc[:doc.index("<w:body>") + 8]
new = head + "".join(X) + "</w:body></w:document>"
# idioma pt-BR nos estilos (dicionário e hifenização)
open(doc_path, "w", encoding="utf-8").write(new)
open(rels_path, "w", encoding="utf-8").write(rels)
st_path = os.path.join(WORK, "word/styles.xml"); st = open(st_path, encoding="utf-8").read()
open(st_path, "w", encoding="utf-8").write(st.replace('w:val="en-US"', 'w:val="pt-BR"'))
num_path = os.path.join(WORK, "word/numbering.xml"); num = open(num_path, encoding="utf-8").read()
open(num_path, "w", encoding="utf-8").write(num.replace('w:val="TABLE %1. "', 'w:val="TABELA %1. "'))
if os.path.exists(OUT): os.remove(OUT)
subprocess.run(["zip", "-Xr", os.path.abspath(OUT), "."], cwd=WORK, check=True, stdout=subprocess.DEVNULL)
shutil.rmtree(WORK)
print("gerado", OUT)
