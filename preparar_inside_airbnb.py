"""
Converte o listings.csv do Inside Airbnb (Rio de Janeiro) para o formato que o
StayScore consome, gerando `listings.js`.

Uso:
  1. Baixe em https://insideairbnb.com/get-the-data/ o arquivo
     "listings.csv" (versão resumida) de Rio de Janeiro.
  2. python preparar_inside_airbnb.py listings.csv > listings.js
  3. Em stayscore.html, substitua o bloco
         const LISTINGS = (()=>{ ... })();
     por
         <script src="listings.js"></script>  (antes do script principal)
     e remova a definição local de LISTINGS. Atualize também DATA_REF com a
     data da publicação do Inside Airbnb.

Campos usados pelo app: id, name, neighbourhood, latitude, longitude,
room_type, bedrooms, accommodates, price, availability_365,
reviews_per_month, number_of_reviews, amenities (lista), photoSeed.
A versão resumida do Inside Airbnb não traz bedrooms/accommodates/amenities;
o script tenta extraí-los do nome do anúncio e, se não encontrar, usa padrões.
Para resultados melhores, use o "listings.csv.gz" detalhado, que contém
essas colunas diretamente.
"""
import csv, json, re, sys, gzip

AMEN_MAP = {
    "wifi": "Wi-Fi", "air conditioning": "Ar-condicionado", "pool": "Piscina",
    "parking": "Estacionamento", "kitchen": "Cozinha", "beach view": "Vista para o mar",
    "ocean view": "Vista para o mar", "sea view": "Vista para o mar",
    "pets allowed": "Pet friendly", "gym": "Academia",
}

def num(v, default=0.0):
    try:
        return float(str(v).replace("$", "").replace(",", ""))
    except ValueError:
        return default

def main(path):
    opener = gzip.open if path.endswith(".gz") else open
    out = []
    with opener(path, "rt", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            price = num(row.get("price"))
            if price <= 0 or not row.get("latitude"):
                continue
            name = row.get("name", "")
            m = re.search(r"(\d+)\s*bedroom", name)
            bedrooms = int(row.get("bedrooms") or (m.group(1) if m else 1) or 1)
            if "studio" in name.lower():
                bedrooms = 0
            amen_raw = (row.get("amenities") or "").lower()
            amenities = sorted({v for k, v in AMEN_MAP.items() if k in amen_raw}) or ["Wi-Fi", "Cozinha"]
            out.append({
                "id": int(row["id"]), "name": name[:80],
                "neighbourhood": row.get("neighbourhood") or row.get("neighbourhood_cleansed", ""),
                "latitude": float(row["latitude"]), "longitude": float(row["longitude"]),
                "room_type": row.get("room_type", "Entire home/apt"),
                "bedrooms": bedrooms,
                "accommodates": int(num(row.get("accommodates"), max(2, bedrooms * 2))),
                "price": price,
                "availability_365": int(num(row.get("availability_365"), 180)),
                "reviews_per_month": num(row.get("reviews_per_month"), 0.0),
                "number_of_reviews": int(num(row.get("number_of_reviews"), 0)),
                "amenities": amenities,
                "photoSeed": int(row["id"]) % 1_000_000,
            })
    sys.stdout.write("window.LISTINGS_DATE = \"\";\nwindow.LISTINGS_DATA = " + json.dumps(out, ensure_ascii=False) + ";\n")
    sys.stderr.write(f"{len(out)} anúncios exportados\n")

if __name__ == "__main__":
    main(sys.argv[1])
