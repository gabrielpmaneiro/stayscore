# StayScore — MVP (PWA)

Inteligência de mercado para aluguel por temporada no Rio de Janeiro: nota de 0 a 100, ocupação estimada, diária média e receita mensal projetada, com mapa de comparáveis.

## Publicação (GitHub Pages)
1. Suba este repositório no GitHub.
2. Settings → Pages → Source: *Deploy from a branch* → Branch `main`, pasta `/docs`.
3. O app fica em `https://<usuario>.github.io/<repo>/`.

## Instalar no celular
- **iPhone (Safari):** abrir a URL → botão Compartilhar → *Adicionar à Tela de Início*.
- **Android (Chrome):** abrir a URL → menu ⋮ → *Instalar app* (ou *Adicionar à tela inicial*).

## Dados do Inside Airbnb
1. Baixe `listings.csv` (Rio de Janeiro) em https://insideairbnb.com/get-the-data/
2. `python preparar_inside_airbnb.py listings.csv > docs/listings.js`
3. Edite a primeira linha de `docs/listings.js` para incluir `window.LISTINGS_DATE = "27 jun 2026";` (data da publicação).
Enquanto `listings.js` estiver vazio, o app usa a base de demonstração calibrada por bairro.

## Estrutura
- `stayscore.html` — fonte único do app (também publicado como artefato no Claude)
- `build_pwa.py` — gera `docs/` (index.html, manifest, service worker, ícones)
- `preparar_inside_airbnb.py` — converte o CSV do Inside Airbnb
