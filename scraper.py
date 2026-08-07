import json
import os
import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup

FECHA_HOY = datetime.now().strftime("%Y-%m-%d")

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
    ("HUILA", "", "HUILA"),
    ("VALLE", "", "VALLE"),
    ("RED", "ROJA", "CRUZ ROJA"),
    ("BOGOTA", "", "BOGOTA"),
    ("MEDELLIN", "", "MEDELLIN"),
]


def normalizar(texto):
    txt = texto.strip().upper()
    for origen, destino in [
        ("Á", "A"),
        ("É", "E"),
        ("Í", "I"),
        ("Ó", "O"),
        ("Ú", "U"),
    ]:
        txt = txt.replace(origen, destino)
    return txt


def identificar_sorteo(texto):
    txt_clean = normalizar(texto)
    for p1, p2, nombre_oficial in REGLAS_LOTERIAS:
        if p1 in txt_clean and (p2 == "" or p2 in txt_clean):
            return nombre_oficial
    return None


def extraer_resultados_oficiales():
    resultados = []
    url = "https://www.ganarchance.com/"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        "Cache-Control": "no-cache",
    }

    try:
        response = requests.get(url, headers=headers, timeout=20)
        print(f"[SCRAPER DIAGNÓSTICO] Estado HTTP: {response.status_code}")

        if response.status_code != 200:
            print(
                f"[SCRAPER ALERTA] La web respondió con código {response.status_code}. Es posible un bloqueo de IP."
            )
            return resultados

        soup = BeautifulSoup(response.text, "html.parser")
        bloques = soup.find_all(["tr", "div", "li", "p", "td"])

        for bloque in bloques:
            texto = bloque.get_text(" ", strip=True)
            sorteo = identificar_sorteo(texto)

            if sorteo:
                num_match = re.search(r"\b\d{4}\b", texto)
                if num_match:
                    numero = num_match.group(0)

                    # Si es Astro, extrae signo si está presente
                    if "Astro" in sorteo:
                        for s in [
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
                        ]:
                            if s.lower() in texto.lower():
                                numero = f"{numero}-{s}"
                                break

                    resultados.append(
                        {
                            "fecha": FECHA_HOY,
                            "sorteo": sorteo,
                            "resultado": numero,
                        }
                    )

    except Exception as e:
        print(f"[SCRAPER ERROR] Excepción al conectar: {e}")

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

    nuevos = extraer_resultados_oficiales()
    print(f"[SCRAPER LOG] Total elementos capturados hoy: {len(nuevos)}")

    if not nuevos:
        print(
            "[SCRAPER] No se extrajeron sorteos. Verifique el diagnóstico de la conexión."
        )
        return

    claves = {f"{s['fecha']}_{s['sorteo']}" for s in existentes}
    agregados = 0

    for item in nuevos:
        clave = f"{item['fecha']}_{item['sorteo']}"
        if clave not in claves:
            existentes.append(item)
            claves.add(clave)
            agregados += 1
            print(
                f"[SCRAPER CAPTURADO] {item['sorteo']} -> {item['resultado']}"
            )

    if agregados > 0:
        with open(archivo, "w", encoding="utf-8") as f:
            json.dump(existentes, f, ensure_ascii=False, indent=2)
        print(
            f"[SCRAPER ÉXITO] Se guardaron {agregados} sorteos nuevos en sorteos.json"
        )
    else:
        print("[SCRAPER] Los sorteos ya estaban previamente registrados.")


if __name__ == "__main__":
    actualizar_sorteos_json()
