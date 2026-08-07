import json
import os
import re
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

AÑO_ACTUAL = str(datetime.now().year)

# 1. Chances del panel y Loterías Principales con sus URLs de historial directo
LOTERIAS_MAPA = [
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
    ("VALLE", "https://www.ganarchance.com/loteria-del-valle"),
    ("MEDELLIN", "https://www.ganarchance.com/loteria-de-medellin"),
    ("HUILA", "https://www.ganarchance.com/loteria-del-huila"),
    ("RISARALDA", "https://www.ganarchance.com/loteria-del-risaralda"),
    ("CRUZ ROJA", "https://www.ganarchance.com/cruz-roja"),
    ("CUNDINAMARCA", "https://www.ganarchance.com/loteria-de-cundinamarca"),
    ("MANIZALES", "https://www.ganarchance.com/loteria-de-manizales"),
    ("META", "https://www.ganarchance.com/loteria-del-meta"),
    ("SANTANDER", "https://www.ganarchance.com/loteria-de-santander"),
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
    txt_norm = normalizar(texto)
    for signo in SIGNOS_ZODIACALES:
        if signo in txt_norm:
            return signo
    return None

def extraer_fecha_de_texto(texto):
    txt_lower = texto.lower()
    if "ayer" in txt_lower:
        return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    match = re.search(r"(\d{1,2})\s+de\s+([a-zA-Z]+)(?:\s+de\s+(\d{4}))?", texto, re.IGNORECASE)
    if match:
        dia = match.group(1).zfill(2)
        mes_nom = match.group(2).lower()
        año = match.group(3) if match.group(3) else AÑO_ACTUAL
        if mes_nom in MESES:
            return f"{año}-{MESES[mes_nom]}-{dia}"
    return None

def obtener_resultados_web():
    resultados = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    }

    # 1. Escanear la Portada Principal para los chances rápidos
    try:
        res = requests.get("https://www.ganarchance.com/", headers=headers, timeout=15)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            for elem in soup.find_all(["tr", "li", "article", "div", "td"]):
                txt = elem.get_text(" ", strip=True)
                for nombre_oficial, _ in LOTERIAS_MAPA:
                    if normalizar(nombre_oficial) in normalizar(txt):
                        numeros = re.findall(r"\b\d{4}\b", txt)
                        for num in numeros:
                            if num in [AÑO_ACTUAL, "2025", "2024"]:
                                continue
                            if "Astro" in nombre_oficial:
                                signo = extraer_signo(txt)
                                if signo:
                                    num = f"{num}-{signo}"
                                else:
                                    continue
                            fecha = extraer_fecha_de_texto(txt)
                            if not fecha:
                                fecha = datetime.now().strftime("%Y-%m-%d")
                            resultados.append({"fecha": fecha, "sorteo": nombre_oficial, "resultado": num})
                            break
    except Exception as e:
        print(f"[SCRAPER PORTADA ERROR] {e}")

    # 2. Escanear las URLs individuales para garantizar el historial de Loterías Principales
    for nombre_oficial, url in LOTERIAS_MAPA:
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code != 200:
                continue
            soup = BeautifulSoup(res.text, "html.parser")
            for fila in soup.find_all(["tr", "li", "article", "div"]):
                txt = fila.get_text(" ", strip=True)
                fecha = extraer_fecha_de_texto(txt)
                if fecha:
                    numeros = re.findall(r"\b\d{4}\b", txt)
                    for num in numeros:
                        if num in [AÑO_ACTUAL, "2025", "2024"]:
                            continue
                        resultados.append({"fecha": fecha, "sorteo": nombre_oficial, "resultado": num})
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

    nuevos = obtener_resultados_web()

    for item in nuevos:
        clave = f"{item['fecha']}_{item['sorteo']}"
        memoria_dict[clave] = item

    lista_final = list(memoria_dict.values())
    lista_final.sort(key=lambda x: (x["fecha"], x["sorteo"]), reverse=True)

    with open(archivo, "w", encoding="utf-8") as f:
        json.dump(lista_final, f, ensure_ascii=False, indent=2)

    print(f"✅ Sincronización completa. Total registros en sorteos.json: {len(lista_final)}")

if __name__ == "__main__":
    actualizar_sorteos_json()
