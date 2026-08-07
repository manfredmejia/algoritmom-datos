import json
import os
import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import requests

AÑO_ACTUAL = str(datetime.now().year)

# Días habituales de juego para Loterías Principales (0=Lunes, 1=Martes, 2=Miércoles, 3=Jueves, 4=Viernes, 5=Sábado)
DIAS_LOTERIAS_PRINCIPALES = {
    "HUILA": 1,        # Martes
    "VALLE": 2,        # Miércoles
    "BOGOTA": 3,       # Jueves
    "MEDELLIN": 4,     # Viernes
    "RISARALDA": 4,    # Viernes
}

# Solo las loterías y chances registrados en tu software
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
    ("ASTRO", "SOL", "Astro Sol"),
    ("ASTRO", "LUNA", "Astro Luna"),
    ("BOGOTA", "", "BOGOTA"),
    ("VALLE", "", "VALLE"),
    ("MEDELLIN", "", "MEDELLIN"),
    ("HUILA", "", "HUILA"),
    ("RISARALDA", "", "RISARALDA"),
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

def extraer_fecha_texto(texto):
    """Detecta fechas reales escritas en la web para evitar problemas con días festivos."""
    match = re.search(r"(\d{1,2})\s+de\s+([a-zA-Z]+)(?:\s+de\s+(\d{4}))?", texto, re.IGNORECASE)
    if match:
        dia = match.group(1).zfill(2)
        mes_nom = match.group(2).lower()
        año = match.group(3) if match.group(3) else AÑO_ACTUAL
        if mes_nom in MESES:
            return f"{año}-{MESES[mes_nom]}-{dia}"
    return None

def obtener_fecha_calculada(sorteo_nombre):
    hoy = datetime.now()
    if sorteo_nombre in DIAS_LOTERIAS_PRINCIPALES:
        dia_habitual = DIAS_LOTERIAS_PRINCIPALES[sorteo_nombre]
        dias_atras = (hoy.weekday() - dia_habitual) % 7
        if dias_atras == 0 and hoy.hour < 22:
            dias_atras = 7
        return (hoy - timedelta(days=dias_atras)).strftime("%Y-%m-%d")
    return hoy.strftime("%Y-%m-%d")

def extraer_resultados():
    resultados = []
    url = "https://www.ganarchance.com/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code != 200:
            return resultados

        soup = BeautifulSoup(res.text, "html.parser")
        bloques = soup.find_all(["tr", "div", "li"])

        for bloque in bloques:
            txt = bloque.get_text(" ", strip=True)
            sorteo = identificar_sorteo(txt)

            if sorteo:
                numeros = re.findall(r"\b\d{4}\b", txt)
                for num in numeros:
                    # 🚨 FILTRO ANTI-CONTAMINACIÓN: Ignora años
                    if num in [AÑO_ACTUAL, "2025", "2024"]:
                        continue

                    if "Astro" in sorteo:
                        for signo in ["Aries", "Tauro", "Géminis", "Cáncer", "Leo", "Virgo", "Libra", "Escorpio", "Sagitario", "Capricornio", "Acuario", "Piscis"]:
                            if signo.lower() in txt.lower():
                                num = f"{num}-{signo.upper()}"
                                break

                    # Intentamos leer la fecha real del HTML; si no está, usamos la fecha calculada
                    fecha_web = extraer_fecha_texto(txt)
                    fecha_final = fecha_web if fecha_web else obtener_fecha_calculada(sorteo)

                    resultados.append({
                        "fecha": fecha_final,
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

    if os.path.exists(archivo):
        try:
            with open(archivo, "r", encoding="utf-8") as f:
                datos_viejos = json.load(f)
                for item in datos_viejos:
                    # Se filtran únicamente registros válidos (sin años como resultados)
                    if item.get("resultado") != AÑO_ACTUAL and item.get("sorteo") in [r[2] for r in REGLAS_LOTERIAS]:
                        clave = f"{item['fecha']}_{item['sorteo']}"
                        memoria_dict[clave] = item
        except Exception:
            memoria_dict = {}

    nuevos = extraer_resultados()

    for item in nuevos:
        clave = f"{item['fecha']}_{item['sorteo']}"
        memoria_dict[clave] = item

    lista_final = list(memoria_dict.values())
    lista_final.sort(key=lambda x: x["fecha"], reverse=True)

    with open(archivo, "w", encoding="utf-8") as f:
        json.dump(lista_final, f, ensure_ascii=False, indent=2)

    print(f"✅ Base limpia y sincronizada. Registros válidos: {len(lista_final)}")

if __name__ == "__main__":
    actualizar_sorteos_json()
