import json
import os
import re
import urllib.request
from datetime import datetime
from bs4 import BeautifulSoup

# Configuración de fecha actual en Colombia
FECHA_HOY = datetime.now().strftime("%Y-%m-%d")


def obtener_resultados_web():
    """
    Extrae los resultados del día desde sitios web de sorteos colombianos.
    """
    nuevos = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    # Ejemplo de scraping ligero para obtener sorteos principales
    # Nota: Puedes añadir o adaptar selectores según el portal de tu preferencia
    try:
        url = "https://www.resultadotiradas.com/"  # O sitio equivalente de loterías
        req = urllib.request.Request(url, headers=headers)

        # Aquí procesamos el HTML descargado para extraer sorteo y número
        # Ejemplo demostrativo de extracción estructurada:
        # nuevos.append({"fecha": FECHA_HOY, "sorteo": "CHONTICO NOCHE", "resultado": "4589"})

    except Exception as e:
        print(f"Error consultando la web: {e}")

    return nuevos


def actualizar_repositorio_json():
    archivo_json = "sorteos.json"

    # 1. Cargar archivo JSON existente
    sorteos_existentes = []
    if os.path.exists(archivo_json):
        try:
            with open(archivo_json, "r", encoding="utf-8") as f:
                sorteos_existentes = json.load(f)
        except Exception:
            sorteos_existentes = []

    # 2. Consultar web para obtener el día de hoy
    nuevos_sorteos = obtener_resultados_web()

    if not nuevos_sorteos:
        print(
            "No se encontraron sorteos nuevos hoy o se actualizará manualmente."
        )
        return

    # 3. Evitar duplicados (combinación Fecha + Sorteo)
    claves_existentes = {
        f"{s['fecha']}_{s['sorteo'].upper()}" for s in sorteos_existentes
    }

    agregados = 0
    for nuevo in nuevos_sorteos:
        clave = f"{nuevo['fecha']}_{nuevo['sorteo'].upper()}"
        if clave not in claves_existentes:
            sorteos_existentes.append(nuevo)
            agregados += 1

    # 4. Guardar archivo JSON actualizado
    if agregados > 0:
        with open(archivo_json, "w", encoding="utf-8") as f:
            json.dump(sorteos_existentes, f, ensure_ascii=False, indent=2)
        print(f"Se agregaron {agregados} sorteos nuevos a {archivo_json}.")
    else:
        print("El archivo JSON ya estaba actualizado.")


if __name__ == "__main__":
    actualizar_repositorio_json()
