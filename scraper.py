import json
import os
import re
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup


def obtener_hora_colombia():
    """Retorna la fecha y hora actual ajustada a Colombia (UTC-5)."""
    return datetime.utcnow() - timedelta(hours=5)


REGLAS_LOTERIAS = [
    ("CHONTICO DIA", "Chontico Día"),
    ("CHONTICO NOCHE", "Chontico Noche"),
    ("DORADO MAÑANA", "Dorado Mañana"),
    ("DORADO MANANA", "Dorado Mañana"),
    ("DORADO TARDE", "Dorado Tarde"),
    ("PAISITA DIA", "Paisita Día"),
    ("PAISITA NOCHE", "Paisita Noche"),
    ("CAFETERITO TARDE", "Cafeterito Tarde"),
    ("CAFETERITO NOCHE", "Cafeterito Noche"),
    ("SINUANO DIA", "Sinuano Día"),
    ("SUPER ASTRO SOL", "Astro Sol"),
    ("ASTRO SOL", "Astro Sol"),
    ("SUPER ASTRO LUNA", "Astro Luna"),
    ("ASTRO LUNA", "Astro Luna"),
    ("TOLIMA", "TOLIMA"),
    ("BOGOTA", "BOGOTA"),
    ("BOGOTÁ", "BOGOTA"),
    ("VALLE", "VALLE"),
    ("MEDELLIN", "MEDELLIN"),
    ("MEDELLÍN", "MEDELLIN"),
    ("HUILA", "HUILA"),
    ("RISARALDA", "RISARALDA"),
    ("CRUZ ROJA", "CRUZ ROJA"),
    ("CUNDINAMARCA", "CUNDINAMARCA"),
    ("MANIZALES", "MANIZALES"),
    ("META", "META"),
    ("SANTANDER", "SANTANDER"),
    ("CAUCA", "CAUCA"),
    ("BOYACA", "BOYACA"),
    ("BOYACÁ", "BOYACA"),
]

SIGNOS = [
    "ARIES",
    "TAURO",
    "GEMINIS",
    "CANCER",
    "LEO",
    "VIRGO",
    "LIBRA",
    "ESCORPIO",
    "SAGITARIO",
    "CAPRICORNIO",
    "ACUARIO",
    "PISCIS",
]

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


def normalizar(txt):
    t = str(txt).strip().upper()
    for a, b in [("Á", "A"), ("É", "E"), ("Í", "I"), ("Ó", "O"), ("Ú", "U")]:
        t = t.replace(a, b)
    return t


def extraer_signo(texto):
    t_norm = normalizar(texto)
    for s in SIGNOS:
        if s in t_norm:
            return s
    return None


def extraer_fecha_de_encabezado_texto(texto):
    """Busca patrones de fecha como '27 DE AGOSTO DE 2026' y los convierte a YYYY-MM-DD."""
    match = re.search(
        r"(\d{1,2})\s+DE\s+([A-Z]+)\s+DE\s+(\d{4})", texto, re.IGNORECASE
    )
    if match:
        dia = match.group(1).zfill(2)
        mes_nom = match.group(2).lower()
        año = match.group(3)
        if mes_nom in MESES:
            return f"{año}-{MESES[mes_nom]}-{dia}"
    return None


def obtener_fecha_de_tarjeta(tarjeta, fecha_defecto):
    """Busca hacia atrás en el árbol HTML el encabezado de fecha más cercano."""
    elem_prev = tarjeta.find_previous([
        "p",
        "div",
        "h1",
        "h2",
        "h3",
        "h4",
        "section",
        "header",
        "strong",
        "b",
    ])
    while elem_prev:
        txt_prev = elem_prev.get_text(" ", strip=True)
        fecha_hallada = extraer_fecha_de_encabezado_texto(txt_prev)
        if fecha_hallada:
            return fecha_hallada
        elem_prev = elem_prev.find_previous([
            "p",
            "div",
            "h1",
            "h2",
            "h3",
            "h4",
            "section",
            "header",
            "strong",
            "b",
        ])
    return fecha_defecto


def identificar_sorteo(texto):
    txt_norm = normalizar(texto)
    for clave, nombre_oficial in REGLAS_LOTERIAS:
        if clave in txt_norm:
            return nombre_oficial
    return None


def rescatar_desde_ganarchance():
    """RESCATE QUIRÚRGICO DESDE GANARCHANCE.COM

    Extrae los datos leyendo la fecha real del banner superior en lugar de
    calcular la hora.
    """
    resultados_rescatados = []
    url = "https://www.ganarchance.com/"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
    }

    try:
        res = requests.get(url, headers=headers, timeout=12)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            fecha_defecto_hoy = obtener_hora_colombia().strftime("%Y-%m-%d")
            items = soup.find_all("div", class_="flex-item")

            for item in items:
                elem_nombre = item.find("div", class_="nombre")
                if not elem_nombre:
                    continue

                nombre_txt = elem_nombre.get_text(" ", strip=True)
                sorteo_oficial = identificar_sorteo(nombre_txt)
                if not sorteo_oficial:
                    continue

                elem_numero = item.find("div", class_="numero")
                if not elem_numero:
                    continue

                digitos = re.findall(r"\d", elem_numero.text)
                if len(digitos) < 4:
                    continue

                cifra_4 = "".join(digitos[:4])
                fecha_real = obtener_fecha_de_tarjeta(item, fecha_defecto_hoy)

                if "Astro" in sorteo_oficial:
                    signo = extraer_signo(item.get_text(" ", strip=True))
                    if signo:
                        cifra_4 = f"{cifra_4}-{signo}"
                    else:
                        continue

                resultados_rescatados.append({
                    "fecha": fecha_real,
                    "sorteo": sorteo_oficial,
                    "resultado": cifra_4,
                })
                print(
                    f"🎯 Rescatado de ganarchance: {sorteo_oficial} ->"
                    f" {cifra_4} ({fecha_real})"
                )

    except Exception as e:
        print(f"[RESCATE GANARCHANCE ERROR] {e}")

    return resultados_rescatados


def extraer_resultados_chancehoy():
    resultados = []
    url = "https://www.chancehoy.com/"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
    }

    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            fecha_defecto_hoy = obtener_hora_colombia().strftime("%Y-%m-%d")
            tarjetas = soup.find_all("a", class_="box-post")
            sorteos_fecha_procesados = set()

            for t in tarjetas:
                elem_titulo = t.find("p", class_="box-post-title")
                txt_titulo = (
                    elem_titulo.get_text(" ", strip=True)
                    if elem_titulo
                    else t.get_text(" ", strip=True)
                )

                sorteo = identificar_sorteo(txt_titulo)
                if not sorteo:
                    continue

                fecha_real = obtener_fecha_de_tarjeta(t, fecha_defecto_hoy)
                clave_procesada = f"{fecha_real}_{sorteo}"
                if clave_procesada in sorteos_fecha_procesados:
                    continue

                txt_tarjeta = t.get_text(" ", strip=True)
                digitos = re.findall(r"\d", txt_tarjeta)

                if len(digitos) >= 4:
                    cifra_4 = "".join(digitos[:4])

                    if "Astro" in sorteo:
                        signo = extraer_signo(txt_tarjeta)
                        if signo:
                            cifra_4 = f"{cifra_4}-{signo}"
                        else:
                            continue

                    resultados.append({
                        "fecha": fecha_real,
                        "sorteo": sorteo,
                        "resultado": cifra_4,
                    })
                    sorteos_fecha_procesados.add(clave_procesada)
    except Exception as e:
        print(f"[SCRAPER EXCEPCIÓN] {e}")

    return resultados


def actualizar_sorteos_json():
    archivo = "sorteos.json"
    memoria_dict = {}

    if os.path.exists(archivo):
        try:
            with open(archivo, "r", encoding="utf-8") as f:
                datos_viejos = json.load(f)
                for item in datos_viejos:
                    if (
                        len(str(item.get("fecha"))) == 10
                        and item.get("resultado")
                        and item.get("sorteo") != "Sinuano Noche"
                    ):
                        clave = f"{item['fecha']}_{item['sorteo']}"
                        memoria_dict[clave] = item
        except Exception as e:
            print(f"[MEMORIA JSON ERROR] {e}")

    # 1. Extraer desde chancehoy.com
    nuevos = extraer_resultados_chancehoy()

    # 2. Rescatar desde ganarchance.com (para Astro Luna, Cafeterito Noche, etc., con fechas reales)
    rescatados = rescatar_desde_ganarchance()

    # Combinar ambas fuentes
    for item in nuevos + rescatados:
        clave = f"{item['fecha']}_{item['sorteo']}"
        memoria_dict[clave] = item

    lista_final = list(memoria_dict.values())
    lista_final.sort(key=lambda x: (x["fecha"], x["sorteo"]), reverse=True)

    with open(archivo, "w", encoding="utf-8") as f:
        json.dump(lista_final, f, ensure_ascii=False, indent=2)

    print(
        "✅ Extracción finalizada con éxito. Total en sorteos.json:"
        f" {len(lista_final)}"
    )


if __name__ == "__main__":
    actualizar_sorteos_json()
