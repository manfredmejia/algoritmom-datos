import json
import os
import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import requests

AÑO_ACTUAL = str(datetime.now().year)

# Mapeo de subpáginas por lotería para extraer historial de días anteriores
LOTERIAS_URLS = [
    ("Chontico Día", "https://www.ganarchance.com/chontico-dia"),
    ("Chontico Noche", "https://www.ganarchance.com/chontico-noche"),
    ("Dorado Mañana", "https://www.ganarchance.com/dorado-manana"),
    ("Dorado Tarde", "https://www.ganarchance.com/dorado-tarde"),
    ("Paisita Día", "https://www.ganarchance.com/paisita-dia"),
    ("Paisita Noche", "https://www.ganarchance.com/paisita-noche"),
    ("Cafeterito Tarde", "https://www.ganarchance.com/cafeterito-tarde"),
    ("Cafeterito Noche", "https://www.ganarchance.com/cafeterito-noche"),
    ("Sinuano Día", "https://www.ganarchance.com/sinuano-dia"),
    ("Astro Sol", "https://www.ganarchance.com/astro-sol"),
    ("Astro Luna", "https://www.ganarchance.com/astro-luna"),
    ("BOGOTA", "https://www.ganarchance.com/loteria-de-bogota"),
    ("RISARALDA", "https://www.ganarchance.com/loteria-del-risaralda"),
    ("MEDELLIN", "https://www.ganarchance.com/loteria-de-medellin"),
    ("VALLE", "https://www.ganarchance.com/loteria-del-valle"),
    ("HUILA", "https://www.ganarchance.com/loteria-del-huila"),
    ("CRUZ ROJA", "https://www.ganarchance.com/loteria-de-cruzroja"),
    ("CUNDINAMARCA", "https://www.ganarchance.com/loteria-de-cundinamarca"),
    ("MANIZALES", "https://www.ganarchance.com/loteria-de-manizales"),
    ("META", "https://www.ganarchance.com/loteria-del-meta"),
    ("SANTANDER", "https://www.ganarchance.com/loteria-del-santander"),
    ("CAUCA", "https://www.ganarchance.com/loteria-del-cauca"),
    ("BOYACA", "https://www.ganarchance.com/loteria-de-boyaca"),
]

SIGNOS_ZODIACALES = [
    "ARIES", "TAURO", "GEMINIS", "CANCER", "LEO", "VIRGO",
    "LIBRA", "ESCORPIO", "SAGITARIO", "CAPRICORNIO", "ACUARIO", "PISCIS"
]

MESES = {
    "enero": "01", "febrero": "02", "marzo": "03", "abril": "04",
    "mayo": "05", "junio": "06", "julio": "07", "agosto": "08",
    "septiembre": "09", "octubre": "10", "noviembre": "11", "diciembre": "12"
}

def normalizar(texto):
    txt = texto.strip().upper()
    for origen, destino in [("Á", "A"), ("É", "E"), ("Í", "I"), ("Ó", "O"), ("Ú", "U")]:
        txt = txt.replace(origen, destino)
    return txt

def extraer_signo(texto):
    txt_clean = normalizar(texto)
    for signo in SIGNOS_ZODIACALES:
        if signo in txt_clean:
            return signo
    return None

def extraer_fecha(texto):
    match = re.search(r"(\d{1,2})\s+de\s+([a-zA-Z]+)(?:\s+de\s+(\d{4}))?", texto, re.IGNORECASE)
    if match:
        dia = match.group(1).zfill(2)
        mes_nom = match.group(2).lower()
        año = match.group(3) if match.group(3) else AÑO_ACTUAL
        if mes_nom in MESES:
            return f"{año}-{MESES[mes_nom]}-{dia}"
    return None

def extraer_historial():
    resultados = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    # 1. Escaneo de la portada principal
    try:
        res = requests.get("https://www.ganarchance.com/", headers=headers, timeout=12)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            for bloque in soup.find_all(["tr", "li", "div"]):
                txt = bloque.get_text(" ", strip=True)
                for nombre_oficial, _ in LOTERIAS_URLS:
                    if normalizar(nombre_oficial) in normalizar(txt):
                        nums = re.findall(r"\b\d{4}\b", txt)
                        for num in nums:
                            if num not in [AÑO_ACTUAL, "2025", "2024"]:
                                if "Astro" in nombre_oficial:
                                    signo = extraer_signo(txt)
                                    if signo:
                                        num = f"{num}-{signo}"
                                    else:
                                        continue
                                fecha_det = extraer_fecha(txt)
                                if not fecha_det:
                                    fecha_det = datetime.now().strftime("%Y-%m-%d")
                                resultados.append({"fecha": fecha_det, "sorteo": nombre_oficial, "resultado": num})
                                break
    except Exception as e:
        print(f"[SCRAPER PORTADA ERROR] {e}")

    # 2. Escaneo de subpáginas específicas para rescatar el historial de ayer
    for nombre_oficial, url in LOTERIAS_URLS:
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code != 200:
                continue

            soup = BeautifulSoup(res.text, "html.parser")
            filas = soup.find_all(["tr", "li", "article", "div"])

            for fila in filas:
                txt = fila.get_text(" ", strip=True)
                fecha_det = extraer_fecha(txt)

                if fecha_det:
                    nums = re.findall(r"\b\d{4}\b", txt)
                    for num in nums:
                        if num not in [AÑO_ACTUAL, "2025", "2024"]:
                            if "Astro" in nombre_oficial:
                                signo = extraer_signo(txt)
                                if signo:
                                    num = f"{num}-{signo}"
                                else:
                                    continue

                            resultados.append({"fecha": fecha_det, "sorteo": nombre_oficial, "resultado": num})
                            break
        except Exception:
            continue

    return resultados

def actualizar_sorteos_json():
    archivo = "sorteos.json"
    memoria_dict = {}

    if os.path.exists(archivo):
        try:
            with open(archivo, "r", encoding="utf-8") as f:
                datos_viejos = json.load(f)
                for item in datos_viejos:
                    if item.get("resultado") != AÑO_ACTUAL:
                        clave = f"{item['fecha']}_{item['sorteo']}"
                        memoria_dict[clave] = item
        except Exception:
            memoria_dict = {}

    nuevos = extraer_historial()

    for item in nuevos:
        clave = f"{item['fecha']}_{item['sorteo']}"
        memoria_dict[clave] = item

    lista_final = list(memoria_dict.values())
    lista_final.sort(key=lambda x: (x["fecha"], x["sorteo"]), reverse=True)

    with open(archivo, "w", encoding="utf-8") as f:
        json.dump(lista_final, f, ensure_ascii=False, indent=2)

    print(f"✅ Historial completo sincronizado. Registros en sorteos.json: {len(lista_final)}")

if __name__ == "__main__":
    actualizar_sorteos_json()
