from datetime import datetime, timedelta
import json
import os
import re
from bs4 import BeautifulSoup
import requests

# Mapa de meses para conversión de fechas en español
MESES = {
    "enero": "01",
    "febrero": "02",
    "marzo": "03",
    "abril": "04",
    "mayo": "05",
    "junio": "06",
    "julio": "07",
    "agosto": "08",
    "septiembre": "09",
    "octubre": "10",
    "noviembre": "11",
    "diciembre": "12",
}

# Reglas de emparejamiento para Loterías Principales y Chances del Panel
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
    ("HUILA", "", "HUILA"),
    ("MANIZALES", "", "MANIZALES"),
    ("MEDELLIN", "", "MEDELLIN"),
    ("RED", "ROJA", "CRUZ ROJA"),
    ("SANTANDER", "", "SANTANDER"),
    ("RISARALDA", "", "RISARALDA"),
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


def extraer_fecha_del_texto(texto):
    """Extrae la fecha real en formato YYYY-MM-DD desde el texto de la página web."""
    # 1. Buscar formato tipo: "06 de agosto de 2026" o "6 de agosto"
    match_texto = re.search(
        r"(\d{1,2})\s+de\s+([a-zA-Z]+)(?:\s+de\s+(\d{4}))?",
        texto,
        re.IGNORECASE,
    )
    if match_texto:
        dia = match_texto.group(1).zfill(2)
        mes_nombre = match_texto.group(2).lower()
        año = match_texto.group(3) if match_texto.group(3) else "2026"

        if mes_nombre in MESES:
            return f"{año}-{MESES[mes_nombre]}-{dia}"

    # 2. Buscar formato numérico tipo: "06/08/2026" o "2026-08-06"
    match_num = re.search(r"(\d{2})[/.-](\d{2})[/.-](\d{4})", texto)
    if match_num:
        return f"{match_num.group(3)}-{match_num.group(2)}-{match_num.group(1)}"

    match_iso = re.search(r"(\d{4})[/.-](\d{2})[/.-](\d{2})", texto)
    if match_iso:
        return f"{match_iso.group(1)}-{match_iso.group(2)}-{match_iso.group(3)}"

    return None


def identificar_sorteo(texto):
    txt_clean = normalizar(texto)
    for p1, p2, nombre_oficial in REGLAS_LOTERIAS:
        if p1 in txt_clean and (p2 == "" or p2 in txt_clean):
            return nombre_oficial
    return None


def obtener_resultados_web():
    resultados = []
    url = "https://www.ganarchance.com/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    }

    try:
        res = requests.get(url, headers=headers, timeout=20)
        if res.status_code != 200:
            print(f"[SCRAPER ERROR] Código HTTP: {res.status_code}")
            return resultados

        soup = BeautifulSoup(res.text, "html.parser")

        # Recorremos bloques de tablas o contenedores de resultados
        bloques = soup.find_all(["tr", "div", "li", "article"])

        fecha_bloque_actual = (datetime.now() - timedelta(days=1)).strftime(
            "%Y-%m-%d"
        )

        for bloque in bloques:
            txt_bloque = bloque.get_text(" ", strip=True)

            # Intentar capturar fecha en el bloque o encabezado
            fecha_detectada = extraer_fecha_del_texto(txt_bloque)
            if fecha_detectada:
                fecha_bloque_actual = fecha_detectada

            sorteo = identificar_sorteo(txt_bloque)
            if sorteo:
                num_match = re.search(r"\b\d{4}\b", txt_bloque)
                if num_match:
                    numero = num_match.group(0)

                    # Si es Astro, extrae el signo si está presente
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
                            if s.lower() in txt_bloque.lower():
                                numero = f"{numero}-{s.upper()}"
                                break

                    # Asignación de fecha real
                    fecha_resultado = (
                        fecha_detectada
                        if fecha_detectada
                        else fecha_bloque_actual
                    )

                    # Ajuste específico para Loterías nocturnas semanales
                    if (
                        sorteo in ["BOGOTA", "QUINDIO"]
                        and datetime.now().weekday() == 4
                    ):
                        # Si hoy es viernes y se extrae Bogotá, la fecha real fue ayer jueves
                        fecha_resultado = (
                            datetime.now() - timedelta(days=1)
                        ).strftime("%Y-%m-%d")

                    resultados.append(
                        {
                            "fecha": fecha_resultado,
                            "sorteo": sorteo,
                            "resultado": numero,
                        }
                    )

    except Exception as e:
        print(f"[SCRAPER EXCEPCIÓN] {e}")

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

    nuevos = obtener_resultados_web()
    print(f"[SCRAPER LOG] Resultados procesados hoy: {len(nuevos)}")

    claves = {f"{s['fecha']}_{s['sorteo']}" for s in existentes}
    agregados = 0

    for item in nuevos:
        clave = f"{item['fecha']}_{item['sorteo']}"
        if clave not in claves:
            existentes.append(item)
            claves.add(clave)
            agregados += 1
            print(
                f"✅ [NUEVO GUARDA] {item['fecha']} | {item['sorteo']} -> {item['resultado']}"
            )

    # Ordenar por fecha descendente
    existentes.sort(key=lambda x: x["fecha"], reverse=True)

    if agregados > 0 or not os.path.exists(archivo):
        with open(archivo, "w", encoding="utf-8") as f:
            json.dump(existentes, f, ensure_ascii=False, indent=2)
        print(
            f"🚀 [ÉXITO] Base de datos actualizada en sorteos.json ({len(existentes)} registros en total)."
        )
    else:
        print("ℹ️ [INFO] Los resultados leídos ya existen en la base.")


if __name__ == "__main__":
    actualizar_sorteos_json()
