# StayScore

**Inteligência de mercado para aluguel por temporada.** A partir de um endereço e das características de um imóvel, o StayScore busca anúncios comparáveis na vizinhança, estima diária média, taxa de ocupação e receita mensal e devolve uma nota de 0 a 100, sempre acompanhada dos dados que a sustentam.

- **App (PWA):** https://gabrielpmaneiro.github.io/stayscore/
- **Artigo de conclusão:** [`artigo/StayScore_Artigo.pdf`](artigo/StayScore_Artigo.pdf)
- **Cobertura:** Rio de Janeiro · Base: Inside Airbnb (publicação de set. 2026, 40.261 anúncios ativos)

Projeto da disciplina de Análise de Dados – Ibmec, Campus Barra da Tijuca (2026).
Integrantes: Bernardo Miller, Claudia Abajo, Enrico Astolfi, Gabriel Maneiro e Gabriel Martins.

---

## 1. O problema

Quem vai anunciar ou comprar um imóvel para temporada precisa responder a três perguntas: **quanto cobrar por diária, quanto tempo o imóvel ficará ocupado e quanto isso rende por mês**. Hoje o pequeno anfitrião responde olhando alguns anúncios vizinhos; as ferramentas profissionais (AirDNA, PriceLabs, Wheelhouse) custam a partir de US$ 125/mês, são em inglês e focam só na diária. O StayScore transforma dados abertos em uma resposta objetiva, em português, para qualquer endereço do Rio.

## 2. Como funciona

```
Endereço + características  →  Geocodificação (Nominatim/OSM)
        →  Busca de anúncios no raio (500 m / 1 km / 2 km)
        →  Filtro de similaridade (tipo, quartos, capacidade) + remoção de outliers de preço
        →  Diária mediana · Ocupação estimada · Receita projetada · Competição
        →  Stay Score 0–100  +  mapa  +  comparativos detalhados
```

### Indicadores
| Indicador | Cálculo |
|---|---|
| **Diária média estimada** | Mediana dos preços dos comparáveis (com intervalo interquartil "pode variar de … a …") |
| **Ocupação média mensal** | Mediana da ocupação estimada dos comparáveis, ajustada em até ±8 p.p. pelas amenidades do imóvel |
| **Receita mensal projetada** | Diária × dias ocupados em um mês de 30,4 dias |
| **Competição** | Anúncios ativos do mesmo tipo por km² dentro do raio |

### Ocupação estimada
As plataformas não divulgam ocupação real. Cada anúncio recebe uma estimativa que combina a estimativa anual do Inside Airbnb (`estimated_occupancy_l365d`) com a disponibilidade do calendário (`availability_365`):

`ocupação = 0,6 · (dias_estimados / 365) + 0,4 · (1 − dias_disponíveis / 365)`

Na base resumida (sem a estimativa anual), usa-se a frequência de avaliações como proxy de reservas (≈ 50 % das estadias geram review, estadia média de 3,5 noites).

### A nota
`Stay Score = 100 · (0,45 · Ocupação + 0,35 · Receita + 0,20 · Competição)`

- **Ocupação** e **Receita** são o percentil do imóvel entre todos os anúncios ativos da cidade (nota relativa ao mercado do Rio).
- **Competição** usa escala logarítmica da densidade: 10 anúncios/km² → 1 ponto; ~4.000/km² (Copacabana) → 0.
- Faixas: Excelente ≥ 75 · Muito Bom ≥ 60 · Bom ≥ 45 · Regular ≥ 30 · Baixo < 30.

Tudo isso é mostrado ao usuário no painel **ⓘ "Como a nota foi construída"**: amostra, raio, filtro aplicado, data de referência e pontos por componente. A nota nunca é uma caixa-preta.

## 3. Telas

1. **Entrada** – endereço (com exemplos), tipo, quartos, capacidade, raio e amenidades.
2. **Resultado** – Stay Score em arco, três cartões (ocupação, diária, receita) e mapa OpenStreetMap com os comparáveis no raio.
3. **Comparativos detalhados** – cada imóvel da amostra com foto, distância e minigráfico (imóvel × mediana da região), busca/filtro e dicas geradas a partir da amostra.

## 4. Estrutura do repositório

```
stayscore.html              ← fonte único do app (HTML + CSS + JS)
build_pwa.py                ← gera a pasta docs/ (index.html, manifest, service worker, ícones)
preparar_inside_airbnb.py   ← converte o CSV do Inside Airbnb em docs/listings.js
docs/                       ← site publicado no GitHub Pages
  index.html                  página do app
  listings.js                 base de anúncios (compacta, ~3 MB gzip)
  manifest.webmanifest        instalação como app (PWA)
  sw.js                       cache offline e atualização automática
  icons/                      ícones do app
artigo/                     ← artigo no template IEEE (docx, pdf, figuras e gerador)
.github/workflows/pages.yml ← publicação automática a cada push
```

## 5. Stack

| Camada | Tecnologia |
|---|---|
| Tratamento de dados | Python (csv, json, re) – `preparar_inside_airbnb.py` |
| Cálculo e interface | JavaScript puro no navegador (sem framework) |
| Mapa | Leaflet 1.9 + tiles OpenStreetMap |
| Geocodificação | Nominatim (OpenStreetMap), com dicionário local de ruas/bairros como contingência |
| Distribuição | PWA no GitHub Pages (instalável no celular, funciona offline) |

Para o MVP o cálculo roda inteiramente no navegador, o que dispensa servidor. O relatório técnico prevê a migração para FastAPI + PostgreSQL/PostGIS quando houver mais cidades e histórico por usuário.

## 6. Como rodar localmente

```bash
git clone https://github.com/gabrielpmaneiro/stayscore.git
cd stayscore
python3 -m http.server 8000 --directory docs
# abra http://localhost:8000
```
(Precisa ser servido por HTTP – abrir o arquivo direto bloqueia o service worker.)

Após editar `stayscore.html`, regenere a pasta publicada:
```bash
python3 build_pwa.py
```

## 7. Como atualizar os dados

1. Baixe o `listings.csv.gz` (detalhado) de Rio de Janeiro em https://insideairbnb.com/get-the-data/
2. Converta:
   ```bash
   python3 preparar_inside_airbnb.py listings.csv.gz "DD mmm AAAA" > docs/listings.js
   ```
   O segundo argumento é a data da publicação, exibida no app como data de referência.
3. Faça commit e push: o GitHub Actions publica e o app atualiza sozinho na próxima abertura.

O script descarta quartos compartilhados/hotel, preços inválidos e anúncios inativos (sem review em 12 meses e com calendário totalmente livre). Também aceita o `listings.csv` resumido; nesse caso quartos, capacidade e amenidades são inferidos do título do anúncio.

## 8. Instalar no celular

- **iPhone (Safari):** abrir o link → Compartilhar → *Adicionar à Tela de Início*.
- **Android (Chrome):** abrir o link → menu ⋮ → *Instalar app*.

## 9. Limitações conhecidas

- A ocupação é **estimada**, não observada; datas bloqueadas pelo anfitrião podem parecer reservas.
- Depende das publicações periódicas do Inside Airbnb (a data de referência está sempre visível).
- Cobertura apenas do Rio de Janeiro; bairros com poucos anúncios geram amostras pequenas (o app informa o tamanho).
- Primeira abertura leva alguns segundos (≈ 3 MB de dados); depois fica em cache.

## 10. Fontes

- Inside Airbnb – https://insideairbnb.com (dados abertos, uso não comercial)
- Nominatim – https://nominatim.org · OpenStreetMap – https://www.openstreetmap.org
- Leaflet – https://leafletjs.com
