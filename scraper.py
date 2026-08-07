import json
import os
import re
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

AÑO_ACTUAL = str(datetime.now().year)

# Mapeo de loterías y chances de tu software
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
    ("SINUANO NOCHE", "Sinuano Noche"),
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

def parsear_fecha_encabezado(soup):
    """Extrae la fecha general publicada en la cabecera de ChanceHoy (ej. 07 DE AGOSTO DE 2026 -> 2026-08-07)."""
    texto_pagina = soup.get_text(" ", strip=True)
    match = re.search(r"(\d{1,2})\s+DE\s+([A-Z]+)\s+DE\s+(\d{4})", texto_pagina, re.IGNORECASE)
    if match:
        dia = match.group(1).zfill(2)
        mes_nom = match.group(2).lower()
        año = match.group(3)
        if mes_nom in MESES:
            return f"{año}-{MESES[mes_nom]}-{dia}"
    return datetime.now().strftime("%Y-%m-%d")

def identificar_sorteo(texto):
    txt_norm = normalizar(texto)
    for clave, nombre_oficial in REGLAS_LOTERIAS:
        if clave in txt_norm:
            return nombre_oficial
    return None

def extraer_resultados_chancehoy():
    resultados = []
    url = "https://www.chancehoy.com/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    }

    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code != 200:
            print(f"[SCRAPER ERROR] HTTP Status: {res.status_code}")
            return resultados

        soup = BeautifulSoup(res.text, "html.parser")
        fecha_pagina = parsear_fecha_encabezado(soup)

        # En ChanceHoy cada tarjeta o bloque de resultado está en contenedores div/article
        bloques = soup.find_all(["div", "article", "section"])
        sorteos_procesados = set()

        for b in bloques:
            txt = b.get_text(" ", strip=True)
            sorteo = identificar_sorteo(txt)

            if sorteo and sorteo not in sorteos_procesados:
                # Buscamos todas las cifras individuales (las bolas verdes y azules de la imagen)
                ditos_encontrados = re.findall(r"\b\d\b", txt)
                
                if len(ditos_encontrados) >= 4:
                    # Tomamos estrictamente los primeros 4 dígitos (las 4 bolas verdes) y descartamos la 5ta bola azul
                    cifra_4 = "".join(ditos_encontrados[:4])

                    if "Astro" in sorteo:
                        signo = extraer_signo(txt)
                        if signo:
                            cifra_4 = f"{cifra_4}-{signo}"
                        else:
                            continue  # Exige que Astro contenga su signo zodiacal

                    resultados.append({
                        "fecha": fecha_pagina,
                        "sorteo": sorteo,
                        "resultado": cifra_4
                    })
                    sorteos_procesados.add(sorteo)

    except Exception as e:
        print(f"[SCRAPER EXCEPCIÓN] {e}")

    return resultados

def actualizar_sorteos_json():
    archivo = "sorteos.json"
    memoria_dict = {}

    # 1. Cargar historial anterior purgado
    if os.path.exists(archivo):
        try:
            with open(archivo, "r", encoding="utf-8") as f:
                datos_viejos = json.load(f)
                for item in datos_viejos:
                    # Descartar entradas con fechas mal formateadas o resultados corruptos
                    if len(str(item.get("fecha"))) == 10 and item.get("resultado") != AÑO_ACTUAL:
                        clave = f"{item['fecha']}_{item['sorteo']}"
                        memoria_dict[clave] = item
        except Exception:
            memoria_dict = {}

    # 2. Extraer de ChanceHoy.com
    nuevos = extraer_resultados_chancehoy()

    for item in nuevos:
        clave = f"{item['fecha']}_{item['sorteo']}"
        memoria_dict[clave] = item

    # 3. Guardar ordenado
    lista_final = list(memoria_dict.values())
    lista_final.sort(key=lambda x: (x["fecha"], x["sorteo"]), reverse=True)

    with open(archivo, "w", encoding="utf-8") as f:
        json.dump(lista_final, f, ensure_ascii=False, indent=2)

    print(f"✅ Sincronización impecable desde ChanceHoy. Total sorteos guardados: {len(lista_final)}")

if __name__ == "__main__":
    actualizar_sorteos_json()
