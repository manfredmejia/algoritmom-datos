import json
import os
import re
import urllib.request
from datetime import datetime
from bs4 import BeautifulSoup

FECHA_HOY = datetime.now().strftime("%Y-%m-%d")

# 🎯 REGLAS FLEXIBLES: Si el texto contiene Palabra1 Y Palabra2, se asigna el Nombre Oficial
REGLAS_LOTERIAS = [
    # (Palabra Clave 1, Palabra Clave 2, Nombre Oficial UI)
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
    ("HUILA", "", "HUILA"),
    ("META", "", "META"),
    ("VALLE", "", "VALLE"),
    ("CRUZ", "ROJA", "CRUZ ROJA"),
    ("BOGOTA", "", "BOGOTA"),
    ("MEDELLIN", "", "MEDELLIN"),
    ("SANTANDER", "", "SANTANDER"),
    ("MANIZALES", "", "MANIZALES"),
    ("CUNDINAMARCA", "", "CUNDINAMARCA"),
    ("RISARALDA", "", "RISARALDA"),
    ("BOYACA", "", "BOYACA"),
    ("CAUCA", "", "CAUCA"),
    ("TOLIMA", "", "TOLIMA"),
]


def normalizar_texto(texto):
    """Limpia tildes y caracteres especiales."""
    txt = texto.strip().upper()
    txt = (
        txt.replace("Á", "A")
        .replace("É", "E")
        .replace("Í", "I")
        .replace("Ó", "O")
        .replace("Ú", "U")
    )
    return txt


def identificar_sorteo(texto_bloque):
    """Identifica la lotería por coincidencia parcial de palabras clave."""
    txt_limpio = normalizar_texto(texto_bloque)

    for p1, p2, nombre_oficial in REGLAS_LOTERIAS:
        if p1 in txt_limpio and (p2 == "" or p2 in txt_limpio):
            return nombre_oficial
    return None


def extraer_resultados_oficiales():
    resultados = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    # Intentar conexión con ganarchance.com
    url = "https://www.ganarchance.com/"

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode("utf-8")
            soup = BeautifulSoup(html, "html.parser")

            # Analizar todos los contenedores de texto
            for bloque in soup.find_all(
                ["tr", "div", "li", "p", "td"], class_=True
            ):
                texto = bloque.get_text(" ", strip=True)

                # Verificar si el bloque contiene el nombre de algún sorteo de nuestro panel
                sorteo_detectado = identificar_sorteo(texto)

                if sorteo_detectado:
                    # Buscar número de 4 dígitos usando Expresiones Regulares (Regex)
                    match_num = re.search(r"\b\d{4}\b", texto)
                    if match_num:
                        numero_ganador = match_num.group(0)

                        # Si es un sorteo Astro, intentar extraer el signo
                        if "Astro" in sorteo_detectado:
                            signos = [
                                "Aries",
                                "Tauro",
                                "Géminis",
                                "Cáncer",
                                "Leo",
                                "Virgo",
                                "Libra",
                                "Escorpio",
                                "Sagitario",
                                "Capricornio",
                                "Acuario",
                                "Piscis",
                            ]
                            for s in signos:
                                if s.lower() in texto.lower():
                                    numero_ganador = f"{numero_ganador}-{s}"
                                    break

                        resultados.append(
                            {
                                "fecha": FECHA_HOY,
                                "sorteo": sorteo_detectado,
                                "resultado": numero_ganador,
                            }
                        )

    except Exception as e:
        print(f"[SCRAPER] Error de conexión: {e}")

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

    nuevos = extraer_resultados_oficiales()

    if not nuevos:
        print("[SCRAPER] No se encontraron sorteos nuevos en la web hoy.")
        return

    # Usar diccionario para evitar duplicados del mismo día y sorteo
    claves_existentes = {f"{s['fecha']}_{s['sorteo']}" for s in existentes}

    for item in nuevos:
        clave = f"{item['fecha']}_{item['sorteo']}"
        if clave not in claves_existentes:
            existentes.append(item)
            claves_existentes.add(clave)
            agregados += 1
            print(
                f"[SCRAPER] Capturado: {item['sorteo']} -> {item['resultado']}"
            )

    if agregados > 0:
        with open(archivo, "w", encoding="utf-8") as f:
            json.dump(existentes, f, ensure_ascii=False, indent=2)
        print(f"[SCRAPER] ✅ Exito: {agregados} sorteos guardados en GitHub.")
    else:
        print(
            "[SCRAPER] Todos los sorteos capturados ya estaban registrados en el JSON."
        )


if __name__ == "__main__":
    actualizar_sorteos_json()
