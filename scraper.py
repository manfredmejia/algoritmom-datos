import json
import os
import urllib.request
from datetime import datetime
from bs4 import BeautifulSoup

FECHA_HOY = datetime.now().strftime("%Y-%m-%d")

# 🗺️ MAPEO OFICIAL: Convierte y filtra los sorteos al formato exacto de tu interfaz
MAPEO_LOTERIAS = {
    # Disipadores y Nocturnos (Formato Mixto)
    "DORADO MAÑANA": "Dorado Mañana",
    "CHONTICO DÍA": "Chontico Día",
    "PAISITA DÍA": "Paisita Día",
    "DORADO TARDE": "Dorado Tarde",
    "CAFETERITO TARDE": "Cafeterito Tarde",
    "SINUANO DÍA": "Sinuano Día",
    "PAISITA NOCHE": "Paisita Noche",
    "CHONTICO NOCHE": "Chontico Noche",
    "CAFETERITO NOCHE": "Cafeterito Noche",

    # Filtro Astro
    "ASTRO SOL": "Astro Sol",
    "ASTRO LUNA": "Astro Luna",

    # Loterías Principales (MAYÚSCULAS SOSTENIDAS)
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
    """Limpia tildes, convierte a mayúsculas y busca en el mapa si el sorteo es permitido."""
    clave = nombre_sorteo.strip().upper()
    clave = clave.replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U")
    return MAPEO_LOTERIAS.get(clave, None)

def extraer_resultados_oficiales():
    """Busca en la web los resultados crudos del día."""
    resultados = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    url = "https://www.loteriascolombia.com/"

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode("utf-8")
            soup = BeautifulSoup(html, "html.parser")

            for bloque in soup.find_all("div", class_="sorteo-block"):
                nombre_elem = bloque.find("span", class_="nombre-sorteo")
                numero_elem = bloque.find("span", class_="numero-ganador")

                if nombre_elem and numero_elem:
                    resultados.append({
                        "fecha": FECHA_HOY,
                        "sorteo": nombre_elem.text.strip(),
                        "resultado": numero_elem.text.strip()
                    })
    except Exception as e:
        print(f"[SCRAPER] Error leyendo la web: {e}")

    return resultados

def actualizar_sorteos_json():
    archivo = "sorteos.json"
    existentes = []

    if os.path.exists(archivo):
        try:
            with open(archivo, "r", encoding="utf-8") as f:
                existentes = json.load(f)
        except Exception:
            existentes = []

    if agregados == 0 and len(existentes) > 0:
        # Esto forzará un error simulado para que GitHub te envíe un email de alerta
        raise ValueError(
            "[ALERTA] No se extrajo ningún sorteo hoy. Posible cambio de diseño web."
        )

    # 1. Obtener extracciones crudas de la web
    brutos = extraer_resultados_oficiales()
    filtrados = []

    # 2. Filtrar y formatear con el mapa
    for item in brutos:
        nombre_correcto = normalizar_nombre(item["sorteo"])
        if nombre_correcto:
            item["sorteo"] = nombre_correcto  # Asigna 'Chontico Noche', 'HUILA', etc.
            filtrados.append(item)
        else:
            print(f"[FILTRO IA] Descartado por no pertenecer al panel: {item['sorteo']}")

    if not filtrados:
        print("[SCRAPER] No se encontraron sorteos válidos nuevos hoy.")
        return

    # 3. Evitar duplicados (combinación Fecha + Sorteo)
    claves_existentes = {f"{s['fecha']}_{s['sorteo']}" for s in existentes}
    agregados = 0

    for item in filtrados:
        clave = f"{item['fecha']}_{item['sorteo']}"
        if clave not in claves_existentes:
            existentes.append(item)
            agregados += 1

    # 4. Guardar en sorteos.json
    if agregados > 0:
        with open(archivo, "w", encoding="utf-8") as f:
            json.dump(existentes, f, ensure_ascii=False, indent=2)
        print(f"[SCRAPER] ✅ Se agregaron {agregados} sorteos compatibles con la IA.")
    else:
        print("[SCRAPER] El archivo JSON ya tenía todos los sorteos de hoy.")

if __name__ == "__main__":
    actualizar_sorteos_json()
