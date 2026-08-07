import json
import os
import re
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

AÑO_ACTUAL = str(datetime.now().year)

# Catálogo completo de las 27 loterías y chances de tu software
REGLAS_LOTERIAS = [
    ("CHONTICO DIA", "Chontico Día"),
    ("CHONTICO NOCHE", "Chontico Noche"),
    ("DORADO MAÑANA", "Dorado Mañana"),
    ("DORADO MANANA", "Dorado Mañana"),
    ("DORADO TARDE", "Dorado Tarde"),
    ("PAISITA DIA", "Paisita Día"),
    ("PAISITA NOCHE", "Paisita Noche"),
    ("CAFETERITO TARDE", "Cafeterito Tarde"),
    ("CAFETERITO NOCHE", "Cafeterito Noche"),
    ("SINUANO DIA", "Sinuano Día"),
    ("ASTRO SOL", "Astro Sol"),
    ("ASTRO LUNA", "Astro Luna"),
    ("BOGOTA", "BOGOTA"),
    ("BOGOTÁ", "BOGOTA"),
    ("VALLE", "VALLE"),
    ("MEDELLIN", "MEDELLIN"),
    ("MEDELLÍN", "MEDELLIN"),
    ("HUILA", "HUILA"),
    ("RISARALDA", "RISARALDA"),
    ("CRUZ ROJA", "CRUZ ROJA"),
    ("CUNDINAMARCA", "CUNDINAMARCA"),
    ("MANIZALES", "MANIZALES"),
    ("META", "META"),
    ("TOLIMA", "TOLIMA"),
    ("SANTANDER", "SANTANDER"),
    ("CAUCA", "CAUCA"),
    ("BOYACA", "BOYACA"),
    ("BOYACÁ", "BOYACA"),
]

SIGNOS = [
    "ARIES", "TAURO", "GEMINIS", "CANCER", "LEO", "VIRGO",
    "LIBRA", "ESCORPIO", "SAGITARIO", "CAPRICORNIO", "ACUARIO", "PISCIS"
]

MESES = {
    "enero": "01", "febrero": "02", "marzo": "03", "abril": "04",
    "mayo": "05", "junio": "06", "julio": "07", "agosto": "08",
    "septiembre": "09", "octubre": "10", "noviembre": "11", "diciembre": "12"
}

NOCTURNOS = [
    "Chontico Noche", "Paisita Noche", "Cafeterito Noche", 
    "Astro Luna", "BOGOTA", "VALLE", "MEDELLIN", "HUILA", "RISARALDA",
    "CRUZ ROJA", "CUNDINAMARCA", "MANIZALES", "META", "SANTANDER", "CAUCA", "BOYACA", "TOLIMA"
]

def normalizar(txt):
    t = txt.strip().upper()
    for a, b in [("Á", "A"), ("É", "E"), ("Í", "I"), ("Ó", "O"), ("Ú", "U")]:
        t = t.replace(a, b)
    return t

def extraer_signo(texto):
    t_norm = normalizar(texto)
    for s in SIGNOS:
        if s in t_norm:
            return s
    return None

def formatear_fecha(texto):
    if not texto:
        return None
    t = texto.lower().strip()
    
    if "ayer" in t:
        return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    match = re.search(r"(\d{1,2})\s+de\s+([a-zA-Z]+)(?:\s+de\s+(\d{4}))?", t)
    if match:
        dia = match.group(1).zfill(2)
        mes_nom = match.group(2)
        año = match.group(3) if match.group(3) else AÑO_ACTUAL
        if mes_nom in MESES:
            return f"{año}-{MESES[mes_nom]}-{dia}"

    match_iso = re.search(r"(\d{4})[-/](\d{2})[-/](\d{2})", t)
    if match_iso:
        return f"{match_iso.group(1)}-{match_iso.group(2)}-{match_iso.group(3)}"

    return None

def extraer_cuatro_cifras(texto):
    """
    TRUNCADOR DE QUINTA CIFRA:
    Busca secuencias de 4 o 5 dígitos y devuelve estrictamente los primeros 4 dígitos.
    """
    coincidencias = re.findall(r"\b\d{4,5}\b", texto)
    for c in coincidencias:
        if c not in [AÑO_ACTUAL, "2025", "2024"]:
            return c[:4]  # Se descarta la 5ta cifra inmediatamente
    return None

def extraer_loterias_de_hoy():
    resultados = []
    url = "https://loteriasdehoy.co/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    }

    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code != 200:
            print(f"[SCRAPER ERROR] HTTP Status: {res.status_code}")
            return resultados

        soup = BeautifulSoup(res.text, "html.parser")
        
        # LoteriasDeHoy utiliza tarjetas/bloques individuales
        tarjetas = soup.find_all(["div", "article", "section", "tr", "li"])

        sorteos_procesados = set()

        for t in tarjetas:
            txt = t.get_text(" ", strip=True)
            txt_norm = normalizar(txt)
            
            # Filtro para procesar tarjetas con 1 sola lotería
            loterias_halladas = set()
            for clave, nombre in REGLAS_LOTERIAS:
                if clave in txt_norm:
                    loterias_halladas.add(nombre)

            if len(loterias_halladas) != 1:
                continue

            sorteo = list(loterias_halladas)[0]

            if sorteo in sorteos_procesados:
                continue

            cifra_4 = extraer_cuatro_cifras(txt)
            if not cifra_4:
                continue

            # Extracción de Signo Zodiacal para Astro
            if "Astro" in sorteo:
                signo = extraer_signo(txt)
                if signo:
                    cifra_4 = f"{cifra_4}-{signo}"
                else:
                    continue  # Requiere signo zodiacal obligatoriamente

            # Control de Fecha
            fecha = formatear_fecha(txt)
            if not fecha:
                ahora = datetime.now()
                if sorteo in NOCTURNOS and ahora.hour < 20:
                    fecha = (ahora - timedelta(days=1)).strftime("%Y-%m-%d")
                else:
                    fecha = ahora.strftime("%Y-%m-%d")

            resultados.append({
                "fecha": fecha,
                "sorteo": sorteo,
                "resultado": cifra_4
            })
            sorteos_procesados.add(sorteo)

    except Exception as e:
        print(f"[SCRAPER ERROR EXCEPCIÓN] {e}")

    return resultados

def actualizar_sorteos_json():
    archivo = "sorteos.json"
    memoria_dict = {}

    # 1. Cargar datos válidos anteriores
    if os.path.exists(archivo):
        try:
            with open(archivo, "r", encoding="utf-8") as f:
                datos_viejos = json.load(f)
                for item in datos_viejos:
                    if item.get("resultado") != AÑO_ACTUAL and len(str(item.get("fecha"))) == 10:
                        clave = f"{item['fecha']}_{item['sorteo']}"
                        memoria_dict[clave] = item
        except Exception:
            memoria_dict = {}

    # 2. Extraer de LoteriasDeHoy.co
    nuevos = extraer_loterias_de_hoy()

    for item in nuevos:
        clave = f"{item['fecha']}_{item['sorteo']}"
        memoria_dict[clave] = item

    # 3. Guardado limpio y ordenado
    lista_final = list(memoria_dict.values())
    lista_final.sort(key=lambda x: (x["fecha"], x["sorteo"]), reverse=True)

    with open(archivo, "w", encoding="utf-8") as f:
        json.dump(lista_final, f, ensure_ascii=False, indent=2)

    print(f"✅ Sincronización exitosa desde LoteriasDeHoy.co. Total sorteos: {len(lista_final)}")

if __name__ == "__main__":
    actualizar_sorteos_json()
