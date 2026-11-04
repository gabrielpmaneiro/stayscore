"""
Converte o listings.csv do Inside Airbnb (Rio de Janeiro) no arquivo docs/listings.js
que o StayScore carrega.

Uso:
  python preparar_inside_airbnb.py listings.csv [data_de_referencia] > docs/listings.js
  ex.: python preparar_inside_airbnb.py listings.csv "set. 2026" > docs/listings.js

Aceita tanto o listings.csv resumido (visualisations) quanto o listings.csv.gz detalhado.
No resumido não há quartos, capacidade, amenidades nem foto: quartos e capacidade são
extraídos do título do anúncio (ex.: "2 quartos", "studio", "4 pessoas") e, quando o
título não informa, assumem-se 1 quarto / 2 hóspedes. No detalhado, as colunas
bedrooms, accommodates, amenities e picture_url são usadas diretamente.

Filtro de atividade: anúncios sem review nos últimos 12 meses e com calendário
totalmente livre (availability_365 >= 360) são tratados como inativos e descartados.

Formato de saída (compacto, uma lista por anúncio):
 [id, nome, bairro, lat, lng, tipo(0=inteiro,1=quarto), quartos, capacidade,
  preço, availability_365, reviews_per_month, number_of_reviews, mascara_amenidades,
  foto (caminho após https://a0.muscache.com/), estimated_occupancy_l365d (dias/ano; -1 se ausente)]
"""
import csv, gzip, json, re, sys

AMENITIES = ["Wi-Fi", "Ar-condicionado", "Piscina", "Estacionamento", "Cozinha", "Vista para o mar", "Pet friendly", "Academia"]
AMEN_PATTERNS = {
    "Wi-Fi": r"wi-?fi|internet",
    "Ar-condicionado": r"ar[\s-]?cond|a/c\b|\bac\b|air[\s-]?cond|climatizad",
    "Piscina": r"piscina|\bpool\b",
    "Estacionamento": r"garagem|parking|\bvaga\b|estacionamento|carport",
    "Cozinha": r"cozinha|kitchen",
    "Vista para o mar": r"vista (para o |pro |p/ )?mar|ocean ?view|sea ?view|beach ?view|beach ?front|frente (ao |para o |pro )?mar|ocean ?front|waterfront|vista mar",
    "Pet friendly": r"\bpets? allowed|\bpet\b|aceita animais",
    "Academia": r"academia|\bgym\b|fitness",
}
PIC_PREFIX = "https://a0.muscache.com/"

def num(v, default=0.0):
    try:
        return float(str(v).replace("$", "").replace(",", ""))
    except (ValueError, TypeError):
        return default

def parse_bedrooms(name, room_type):
    n = name.lower()
    if room_type == "Private room":
        return 1
    if re.search(r"\b(studio|estudio|estúdio|kitnet|kitinete|conjugado|loft)\b", n):
        return 0
    m = re.search(r"(\d)\s*(quartos?|qts?\b|qtos?\b|dormit[oó]rios?|bedrooms?|\bbr\b|\bbdr\b|\bbd\b|suites?|suítes?)", n)
    if m:
        return min(int(m.group(1)), 6)
    return 1

def parse_accommodates(name, bedrooms, room_type):
    n = name.lower()
    m = re.search(r"(\d{1,2})\s*(pessoas|p\.|hóspedes|hospedes|guests|people|pax|adultos)", n) or re.search(r"(?:sleeps|até|up to|for)\s*(\d{1,2})", n)
    if m:
        return max(1, min(int(m.group(1)), 16))
    if room_type == "Private room":
        return 2
    return 2 if bedrooms == 0 else bedrooms * 2

def main(path, ref_date=""):
    opener = gzip.open if path.endswith(".gz") else open
    out, skipped = [], 0
    with opener(path, "rt", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            room = row.get("room_type", "")
            if room not in ("Entire home/apt", "Private room"):
                skipped += 1; continue
            price = num(row.get("price"))
            lat, lng = num(row.get("latitude")), num(row.get("longitude"))
            if price <= 0 or price > 20000 or not lat or not lng:
                skipped += 1; continue
            avail = int(num(row.get("availability_365"), 365))
            ltm = num(row.get("number_of_reviews_ltm"), 0)
            if ltm == 0 and avail >= 360:
                skipped += 1; continue
            name = (row.get("name") or "").strip()
            bedrooms = int(num(row.get("bedrooms"), -1))
            if bedrooms < 0:
                bedrooms = parse_bedrooms(name, room)
            acc = int(num(row.get("accommodates"), -1))
            if acc < 1:
                acc = parse_accommodates(name, bedrooms, room)
            text = (name + " " + (row.get("amenities") or "")).lower()
            mask = 0
            for i, a in enumerate(AMENITIES):
                if re.search(AMEN_PATTERNS[a], text):
                    mask |= 1 << i
            if not row.get("amenities"):          # resumido: Wi-Fi e cozinha são praticamente universais em imóvel inteiro
                mask |= 1
                if room == "Entire home/apt":
                    mask |= 1 << 4
            pic = row.get("picture_url") or ""
            if pic.startswith(PIC_PREFIX):
                pic = pic[len(PIC_PREFIX):]
            est = row.get("estimated_occupancy_l365d")
            est_days = int(num(est, -1)) if est not in (None, "") else -1
            out.append([int(row["id"]), name[:70], row.get("neighbourhood_cleansed") or row.get("neighbourhood", ""),
                        round(lat, 5), round(lng, 5), 0 if room == "Entire home/apt" else 1, bedrooms, acc,
                        round(price), avail, round(num(row.get("reviews_per_month"), 0), 2),
                        int(num(row.get("number_of_reviews"), 0)), mask, pic, est_days])
    sys.stdout.write('window.LISTINGS_DATE = ' + json.dumps(ref_date, ensure_ascii=False) + ';\n')
    sys.stdout.write('window.LISTINGS_COMPACT = ' + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ';\n')
    sys.stderr.write(f"{len(out)} anúncios ativos exportados, {skipped} descartados\n")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "")
