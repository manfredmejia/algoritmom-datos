import json
import os
import re
import urllib.request
from datetime import datetime
from bs4 import BeautifulSoup

FECHA_HOY = datetime.now().strftime("%Y-%m-%d")


def extraer_resultados_oficiales():
    """
    Descarga el HTML de un portal confiable de resultados colombianos
    y lee directamente las etiquetas con los números ganadores reales.
    """
    resultados = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    # Ejemplo apuntando a un agregador público verificado
    url = "https://www.loteriascolombia.com/"

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode("utf-8")
            soup = BeautifulSoup(html, "html.parser")

            # Buscamos los bloques donde se publican las loterías
            # (El selector se adapta según la estructura exacta de la web)
            for bloque in soup.find_all("div", class_="sorteo-block"):
                nombre_elem = bloque.find("span", class_="nombre-sorteo")
                numero_elem = bloque.find("span", class_="numero-ganador")

                if nombre_elem and numero_elem:
                    sorteo = nombre_elem.text.strip().upper()
                    resultado = numero_elem.text.strip()

                    # Guardamos el dato extraído tal cual aparece en pantalla
                    resultados.append(
                        {
                            "fecha": FECHA_HOY,
                            "sorteo": sorteo,
                            "resultado": resultado,
                        }
                    )

    except Exception as e:
        print(
            f"[SCRAPER] Error de lectura web: {e}. No se realizarán cambios erróneos."
        )

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

    # Extraer datos reales
    nuevos = extraer_resultados_oficiales()

    if not nuevos:
        print("[SCRAPER] No se obtuvieron datos nuevos hoy.")
        return

    # Mapear claves existentes (Fecha + Sorteo) para no duplicar datos
    claves = {f"{s['fecha']}_{s['sorteo'].upper()}" for s in existentes}

    agregados = 0
    for item in nuevos:
        clave = f"{item['fecha']}_{item['sorteo'].upper()}"
        if clave not in claves:
            existentes.append(item)
            agregados += 1

    if agregados > 0:
        with open(archivo, "w", encoding="utf-8") as f:
            json.dump(existentes, f, ensure_ascii=False, indent=2)
        print(f"[SCRAPER] ✅ Se guardaron {agregados} sorteos reales nuevos.")
    else:
        print("[SCRAPER] La base de datos de GitHub ya estaba al día.")


if __name__ == "__main__":
    actualizar_sorteos_json()
