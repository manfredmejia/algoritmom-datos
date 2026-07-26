import json
import os
import urllib.request
from datetime import datetime
from bs4 import BeautifulSoup

FECHA_HOY = datetime.now().strftime("%Y-%m-%d")

# 🛡️ LISTA BLANCA OFICIAL: Solo estas loterías entrarán a la IA
LOTERIAS_PERMITIDAS = [
    # Disipadores y Nocturnos (Chance)
    "DORADO MAÑANA",
    "CHONTICO DÍA",
    "CHONTICO DIA",
    "PAISITA DÍA",
    "PAISITA DIA",
    "DORADO TARDE",
    "CAFETERITO TARDE",
    "SINUANO DÍA",
    "SINUANO DIA",
    "PAISITA NOCHE",
    "CHONTICO NOCHE",
    "CAFETERITO NOCHE",
    # Filtro Astro
    "ASTRO SOL",
    "ASTRO LUNA",
    # Loterías Principales
    "CRUZ ROJA",
    "HUILA",
    "META",
    "SANTANDER",
    "BOGOTA",
    "VALLE",
    "MANIZALES",
    "CUNDINAMARCA",
    "MEDELLIN",
    "RISARALDA",
    "BOYACA",
    "CAUCA",
    "TOLIMA",
]


def normalizar_nombre(nombre_sorteo):
    """Limpia el texto para comparar de forma exacta."""
    nombre = nombre_sorteo.strip().upper()
    nombre = nombre.replace("Á", "A").replace("É", "E").replace(
        "Í", "I"
    ).replace("Ó", "O").replace("Ú", "U")
    return nombre


def actualizar_sorteos_json():
    archivo = "sorteos.json"
    existentes = []

    if os.path.exists(archivo):
        try:
            with open(archivo, "r", encoding="utf-8") as f:
                existentes = json.load(f)
        except Exception:
            existentes = []

    # Supongamos que 'nuevos' trae la lista extraída de la web
    nuevos_extraidos = (
        extraer_resultados_oficiales()
    )  # Tu función de scraping
    nuevos_filtrados = []

    # 🚨 FILTRADO QUIRÚRGICO: Descarte automático de loterías no deseadas
    for item in nuevos_extraidos:
        sorteo_clean = normalizar_nombre(item["sorteo"])

        if sorteo_clean in LOTERIAS_PERMITIDAS:
            item["sorteo"] = (
                sorteo_clean  # Guardar con el nombre estandarizado
            )
            nuevos_filtrados.append(item)
        else:
            print(
                f"[FILTRO IA] Sorteo ignorado para evitar contaminación: {item['sorteo']}"
            )

    if not nuevos_filtrados:
        print("[SCRAPER] No hay sorteos permitidos nuevos para registrar.")
        return

    # Mapear claves (Fecha + Sorteo) para evitar duplicados
    claves = {f"{s['fecha']}_{s['sorteo']}" for s in existentes}

    agregados = 0
    for item in nuevos_filtrados:
        clave = f"{item['fecha']}_{item['sorteo']}"
        if clave not in claves:
            existentes.append(item)
            agregados += 1

    if agregados > 0:
        with open(archivo, "w", encoding="utf-8") as f:
            json.dump(existentes, f, ensure_ascii=False, indent=2)
        print(
            f"[SCRAPER] ✅ Se guardaron {agregados} sorteos limpios y compatibles con la IA."
        )


if __name__ == "__main__":
    actualizar_sorteos_json()
