import json
import os
import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import requests

AÑO_ACTUAL = str(datetime.now().year)

# Loterías y chances configurados en tu software
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

# Clasificación de sorteos por franja horaria
SORTEOS_NOCTURNOS = [
    "Chontico Noche", "Paisita Noche", "Cafeterito Noche", "Sinuano Noche", 
    "Astro Luna", "BOGOTA", "VALLE", "MEDELLIN", "HUILA", "RISARALDA"
]

SORTEOS_TARDE = ["Dorado Tarde", "Cafeterito Tarde", "Astro Sol"]

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

def determinar_fecha_real(sorteo, texto_tarjeta):
    """Determina si el resultado leído pertenece a HOY o a AYER según el texto y la hora actual."""
    ahora = datetime.now()
    hoy_str = ahora.strftime("%Y-%m-%d")
    ayer_str = (ahora - timedelta(days=1)).strftime("%Y-%m-%d")
    txt_lower = texto_tarjeta.lower()

    # 1. Si la tarjeta dice explícitamente "ayer" o una fecha pasada
    if "ayer" in txt_lower:
        return ayer_str
    
    match_fecha = re.search(r"(\d{1,2})\s+de\s+([a-zA-Z]+)", texto_tarjeta, re.IGNORECASE)
    if match_fecha:
        dia = match_fecha.group(1).zfill(2)
        mes_nom = match_fecha.group(2).lower()
        if mes_nom in MESES:
            fecha_detectada = f"{AÑO_ACTUAL}-{MESES[mes_nom]}-{dia}"
            if fecha_detectada <= hoy_str:
                return fecha_detectada

    # 2. Lógica por franja horaria según la hora de ejecución del script
    hora_actual = ahora.hour

    # Si se ejecuta antes de las 8:00 PM, cualquier resultado nocturno presente en la web es de AYER
    if sorteo in SORTEOS_NOCTURNOS and hora_actual < 20:
        return ayer_str

    # Si se ejecuta antes de las 2:30 PM, cualquier resultado vespertino es de AYER
    if sorteo in SORTEOS_TARDE and hora_actual < 14:
        return ayer_str

    return hoy_str

def obtener_resultados_web():
    resultados = []
    url = "https://www.ganarchance.com/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code != 200:
            print(f"[SCRAPER ERROR] Código HTTP: {res.status_code}")
            return resultados

        soup = BeautifulSoup(res.text, "html.parser")
        
        # Seleccionamos únicamente elementos contenedores de resultados individuales para evitar sangrado de texto
        tarjetas = soup.find_all(["tr", "li", "article", "div"])

        sorteos_procesados = set()

        for tarjeta in tarjetas:
            txt = tarjeta.get_text(" ", strip=True)
            sorteo = identificar_sorteo(txt)

            if sorteo and sorteo not in sorteos_procesados:
                numeros = re.findall(r"\b\d{4}\b", txt)
                for num in numeros:
                    # Filtro anti-años (descarta 2026, 2025)
                    if num in [AÑO_ACTUAL, "2025", "2024"]:
                        continue

                    # Manejo de ASTRO (Obligatorio Cifra + Signo)
                    if "Astro" in sorteo:
                        signo = extraer_signo(txt)
                        if signo:
                            num = f"{num}-{signo}"
                        else:
                            # Si es Astro pero la tarjeta no incluye el signo, omitir para no contaminar
                            continue

                    fecha_evaluada = determinar_fecha_real(sorteo, txt)

                    resultados.append({
                        "fecha": fecha_evaluada,
                        "sorteo": sorteo,
                        "resultado": num
                    })
                    sorteos_procesados.add(sorteo)
                    break

    except Exception as e:
        print(f"[SCRAPER EXCEPCIÓN] {e}")

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
                    if item.get("resultado") != AÑO_ACTUAL and item.get("sorteo") in [r[2] for r in REGLAS_LOTERIAS]:
                        clave = f"{item['fecha']}_{item['sorteo']}"
                        memoria_dict[clave] = item
        except Exception:
            memoria_dict = {}

    # 2. Nuevas lecturas de la web
    nuevos = obtener_resultados_web()

    # 3. Insertar o actualizar
    for item in nuevos:
        clave = f"{item['fecha']}_{item['sorteo']}"
        memoria_dict[clave] = item

    lista_final = list(memoria_dict.values())
    lista_final.sort(key=lambda x: (x["fecha"], x["sorteo"]), reverse=True)

    with open(archivo, "w", encoding="utf-8") as f:
        json.dump(lista_final, f, ensure_ascii=False, indent=2)

    print(f"✅ Extracción completada. Total registros en sorteos.json: {len(lista_final)}")

if __name__ == "__main__":
    actualizar_sorteos_json()
