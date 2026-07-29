import json
import os
import re
import urllib.request
from datetime import datetime
from bs4 import BeautifulSoup

FECHA_HOY = datetime.now().strftime("%Y-%m-%d")

# 🗺️ MAPEO OFICIAL: Mantiene limpia la IA y estandariza los nombres para tu interfaz
MAPEO_LOTERIAS = {
    # Disipadores y Nocturnos (Chance)
    "DORADO MAÑANA": "Dorado Mañana",
    "DORADO MANANA": "Dorado Mañana",
    "CHONTICO DÍA": "Chontico Día",
    "CHONTICO DIA": "Chontico Día",
    "PAISITA DÍA": "Paisita Día",
    "PAISITA DIA": "Paisita Día",
    "DORADO TARDE": "Dorado Tarde",
    "CAFETERITO TARDE": "Cafeterito Tarde",
    "SINUANO DÍA": "Sinuano Día",
    "SINUANO DIA": "Sinuano Día",
    "PAISITA NOCHE": "Paisita Noche",
    "CHONTICO NOCHE": "Chontico Noche",
    "CAFETERITO NOCHE": "Cafeterito Noche",

    # Filtro Astro
    "ASTRO SOL": "Astro Sol",
    "ASTRO LUNA": "Astro Luna",

    # Loterías Principales (MAYÚSCULAS)
    "CRUZ ROJA": "CRUZ ROJA",
    "HUILA": "HUILA",
    "META": "META",
    "SANTANDER": "SANTANDER",
    "BOGOTA": "BOGOTA",
    "VALLE": "VALLE",
    "MANIZALES": "MANIZALES",
    "CUNDINAMARCA": "CUNDINAMARCA",
    "MEDELLIN": "MEDELLIN",
    "RISARALDA": "RISARALDA",
    "BOYACA": "BOYACA",
    "CAUCA": "CAUCA",
    "TOLIMA": "TOLIMA"
}

def normalizar_nombre(nombre_sorteo):
    """Limpia tildes, convierte a mayúsculas y verifica si pertenece al panel."""
    clave = nombre_sorteo.strip().upper()
    clave = clave.replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U")
    return MAPEO_LOTERIAS.get(clave, None)

def extraer_resultados_oficiales():
    """Busca en ganarchance.com los resultados reales del día."""
    resultados = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # URL oficial de GanarChance
    url = "https://www.ganarchance.com/"

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode("utf-8")
            soup = BeautifulSoup(html, "html.parser")

            # 🔍 Búsqueda de bloques de sorteos en la estructura HTML de ganarchance.com
            # Busca elementos contenedores donde se publican el nombre del sorteo y el número ganador
            for bloque in soup.find_all(
                ["div", "tr", "li"], class_=["resultado", "sorteo", "item"]
            ):
                texto = bloque.get_text(separator=" ").strip()
                lineas = [line.strip() for line in texto.split("\n") if line.strip()]

                if len(lineas) >= 2:
                    nombre_raw = lineas[0]
                    numero_raw = lineas[1]

                    # Validar que contenga números válidos
                    if any(char.isdigit() for char in numero_raw):
                        resultados.append(
                            {
                                "fecha": FECHA_HOY,
                                "sorteo": nombre_raw,
                                "resultado": numero_raw,
                            }
                        )

    except Exception as e:
        print(f"[SCRAPER] Error leyendo ganarchance.com: {e}")

    return resultados

def actualizar_sorteos_json():
    archivo = "sorteos.json"
    existentes = []
    agregados = 0

    if os.path.exists(archivo):
        try:
            with open(archivo, "r", encoding="utf-8") as f:
                existentes = json.load(f)
        except Exception:
            existentes = []

    # 1. Extraer resultados reales
    brutos = extraer_resultados_oficiales()
    filtrados = []

    # 2. Filtrar con la Lista Blanca
    for item in brutos:
        nombre_correcto = normalizar_nombre(item["sorteo"])
        if nombre_correcto:
            item["sorteo"] = nombre_correcto
            filtrados.append(item)

    if not filtrados:
        print("[SCRAPER] No se detectaron extracciones válidas en esta consulta.")
        return

    # 3. Mapear existentes para evitar duplicar (Fecha + Sorteo)
    claves_existentes = {f"{s['fecha']}_{s['sorteo']}" for s in existentes}

    for item in filtrados:
        clave = f"{item['fecha']}_{item['sorteo']}"
        if clave not in claves_existentes:
            existentes.append(item)
            agregados += 1

    # 4. Guardar los datos en el JSON
    if agregados > 0:
        with open(archivo, "w", encoding="utf-8") as f:
            json.dump(existentes, f, ensure_ascii=False, indent=2)
        print(f"[SCRAPER] ✅ Se agregaron {agregados} sorteos reales a GitHub.")
    else:
        print("[SCRAPER] El archivo JSON ya contenía todas las extracciones de hoy.")

if __name__ == "__main__":
    actualizar_sorteos_json()
