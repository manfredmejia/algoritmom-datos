import json
import os
import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import requests

AÑO_ACTUAL = str(datetime.now().year)

# Solo los chances de tu panel y tus loterías principales
REGLAS_LOTERIAS = [
    ("CHONTICO", "NOCHE", "Chontico Noche"),
    ("CHONTICO", "DIA", "Chontico Día"),
    ("DORADO", "MANANA", "Dorado Mañana"),
    ("DORADO", "TARDE", "Dorado Tarde"),
    ("PAISITA", "DIA", "Paisita Día"),
    ("PAISITA", "NOCHE", "Paisita Noche"),
    ("CAFETERITO", "TARDE", "Cafeterito Tarde"),
    ("CAFETERITO", "NOCHE", "Cafeterito Noche"),
    ("SINUANO", "DIA", "Sinuano Día"),
    ("SINUANO", "NOCHE", "Sinuano Noche"),
    ("ASTRO", "SOL", "Astro Sol"),
    ("ASTRO", "LUNA", "Astro Luna"),
    ("BOGOTA", "", "BOGOTA"),
    ("VALLE", "", "VALLE"),
    ("MEDELLIN", "", "MEDELLIN"),
    ("HUILA", "", "HUILA"),
    ("RISARALDA", "", "RISARALDA"),
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

def identificar_sorteo(texto):
    txt_clean = normalizar(texto)
    for p1, p2, nombre_oficial in REGLAS_LOTERIAS:
        if p1 in txt_clean and (p2 == "" or p2 in txt_clean):
            return nombre_oficial
    return None

def extraer_signo(texto):
    txt_clean = normalizar(texto)
    for signo in SIGNOS_ZODIACALES:
        if signo in txt_clean:
            return signo
    return None

def detectar_fecha_en_bloque(texto, fecha_por_defecto):
    """Busca dentro del texto del recuadro si contiene una fecha explícita."""
    txt_lower = texto.lower()
    
    # 1. Si el bloque dice "ayer"
    if "ayer" in txt_lower:
        return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
    # 2. Si contiene texto tipo "6 de agosto" o "06 de agosto"
    match = re.search(r"(\d{1,2})\s+de\s+([a-zA-Z]+)", texto, re.IGNORECASE)
    if match:
        dia = match.group(1).zfill(2)
        mes_nombre = match.group(2).lower()
        if mes_nombre in MESES:
            return f"{AÑO_ACTUAL}-{MESES[mes_nombre]}-{dia}"
            
    return fecha_por_defecto

def obtener_resultados_web():
    resultados = []
    url = "https://www.ganarchance.com/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code != 200:
            return resultados

        soup = BeautifulSoup(res.text, "html.parser")
        
        # Buscamos secciones o tablas de resultados
        bloques = soup.find_all(["tr", "div", "li", "article"])

        fecha_defecto = datetime.now().strftime("%Y-%m-%d")

        for bloque in bloques:
            txt = bloque.get_text(" ", strip=True)
            sorteo = identificar_sorteo(txt)

            if sorteo:
                numeros = re.findall(r"\b\d{4}\b", txt)
                for num in numeros:
                    # Filtro anti-años (descarta 2026, 2025)
                    if num in [AÑO_ACTUAL, "2025", "2024"]:
                        continue

                    # Manejo de ASTRO (Cifra + Signo obligado)
                    if "Astro" in sorteo:
                        signo_encontrado = extraer_signo(txt)
                        if signo_encontrado:
                            num = f"{num}-{signo_encontrado}"
                        else:
                            continue

                    # Determinación de fecha real leída del bloque
                    fecha_real = detectar_fecha_en_bloque(txt, fecha_defecto)

                    resultados.append({
                        "fecha": fecha_real,
                        "sorteo": sorteo,
                        "resultado": num
                    })
                    break

    except Exception as e:
        print(f"[SCRAPER ERROR] {e}")

    return resultados

def actualizar_sorteos_json():
    archivo = "sorteos.json"
    memoria_dict = {}

    # 1. Cargar historial existente
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

    # 2. Nuevas lecturas
    nuevos = obtener_resultados_web()

    # 3. Guardado inteligente sin duplicar números viejos
    for item in nuevos:
        clave = f"{item['fecha']}_{item['sorteo']}"
        memoria_dict[clave] = item

    lista_final = list(memoria_dict.values())
    lista_final.sort(key=lambda x: x["fecha"], reverse=True)

    with open(archivo, "w", encoding="utf-8") as f:
        json.dump(lista_final, f, ensure_ascii=False, indent=2)

    print(f"✅ Extracción finalizada. Registros almacenados: {len(lista_final)}")

if __name__ == "__main__":
    actualizar_sorteos_json()
