import json
import os
import re
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup


def obtener_hora_colombia():
    """Retorna la fecha y hora actual ajustada a Colombia (UTC-5)."""
    return datetime.utcnow() - timedelta(hours=5)


AÑO_ACTUAL = str(obtener_hora_colombia().year)

# Catálogo oficial de loterías y chances de ALGORITMOM
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


def extraer_signo(texto_o_html):
    t_norm = normalizar(texto_o_html)
    for s in SIGNOS:
        if s in t_norm:
            return s
    return None


def extraer_fecha_de_encabezado_texto(texto):
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
    elem_prev = tarjeta.find_previous(
        ["p", "div", "h1", "h2", "h3", "section", "header"]
    )
    while elem_prev:
        txt_prev = elem_prev.get_text(" ", strip=True)
        fecha_hallada = extraer_fecha_de_encabezado_texto(txt_prev)
        if fecha_hallada:
            return fecha_hallada
        elem_prev = elem_prev.find_previous(
            ["p", "div", "h1", "h2", "h3", "section", "header"]
        )
    return fecha_defecto


def identificar_sorteo(texto):
    txt_norm = normalizar(texto)
    for clave, nombre_oficial in REGLAS_LOTERIAS:
        if clave in txt_norm:
            return nombre_oficial
    return None


def rescatar_cafeterito_noche():
    """RESCATE QUIRÚRGICO DE CAFETERITO NOCHE (ganarchance.com)"""
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
            items = soup.find_all("div", class_="flex-item")

            for item in items:
                elem_nombre = item.find("div", class_="nombre")
                if elem_nombre and "CAFETERITO NOCHE" in normalizar(
                    elem_nombre.text
                ):
                    elem_numero = item.find("div", class_="numero")
                    if elem_numero:
                        # Buscar bloques exactos de 4 dígitos descartando el año actual
                        bloques = re.findall(r"\b\d{4}\b", elem_numero.text)
                        bloques_validos = [b for b in bloques if b != AÑO_ACTUAL]

                        if bloques_validos:
                            num = bloques_validos[0]
                            ahora = obtener_hora_colombia()
                            fecha_res = (
                                (ahora - timedelta(days=1)).strftime("%Y-%m-%d")
                                if ahora.hour < 22
                                else ahora.strftime("%Y-%m-%d")
                            )
                            print(
                                f"🎯 Cafeterito Noche rescatado con éxito: {num}"
                                f" ({fecha_res})"
                            )
                            return {
                                "fecha": fecha_res,
                                "sorteo": "Cafeterito Noche",
                                "resultado": num,
                            }
    except Exception as e:
        print(f"[RESCATE CAFETERITO ERROR] {e}")

    return None


def rescatar_astro_luna():
    """RESCATE QUIRÚRGICO DE ASTRO LUNA (ganarchance.com)

    Captura desde: div.flex-item > div.nombre + div.numero > span.serie
    """
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
            items = soup.find_all("div", class_="flex-item")

            for item in items:
                elem_nombre = item.find("div", class_="nombre")
                if elem_nombre and "ASTRO LUNA" in normalizar(elem_nombre.text):
                    elem_numero = item.find("div", class_="numero")
                    if elem_numero:
                        # 1. Extraer bloque de 4 dígitos ignorando el año actual
                        bloques = re.findall(r"\b\d{4}\b", elem_numero.text)
                        bloques_validos = [b for b in bloques if b != AÑO_ACTUAL]

                        # 2. Buscar el signo en span.serie o en todo el bloque
                        elem_serie = elem_numero.find("span", class_="serie")
                        txt_signo = (
                            elem_serie.text
                            if elem_serie
                            else item.get_text(" ", strip=True)
                        )
                        signo = extraer_signo(txt_signo)

                        if bloques_validos and signo:
                            num = bloques_validos[0]
                            ahora = obtener_hora_colombia()

                            # Astro Luna juega a las 22:30 Hora Colombia
                            if ahora.hour < 22 or (
                                ahora.hour == 22 and ahora.minute < 30
                            ):
                                fecha_res = (
                                    ahora - timedelta(days=1)
                                ).strftime("%Y-%m-%d")
                            else:
                                fecha_res = ahora.strftime("%Y-%m-%d")

                            print(
                                f"🎯 Astro Luna rescatado con éxito: {num}-{signo}"
                                f" ({fecha_res})"
                            )
                            return {
                                "fecha": fecha_res,
                                "sorteo": "Astro Luna",
                                "resultado": f"{num}-{signo}",
                            }
    except Exception as e:
        print(f"[RESCATE ASTRO LUNA ERROR] {e}")

    return None


def extraer_resultados_chancehoy():
    resultados = []
    url = "https://www.chancehoy.com/"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
    }

    tiene_cafeterito_noche = False
    tiene_astro_luna = False

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
                if not sorteo or sorteo == "Astro Luna":
                    # Forzamos a que Astro Luna pase SIEMPRE por el rescate quirúrgico de ganarchance.com
                    continue

                fecha_real = obtener_fecha_de_tarjeta(t, fecha_defecto_hoy)
                clave_procesada = f"{fecha_real}_{sorteo}"
                if clave_procesada in sorteos_fecha_procesados:
                    continue

                txt_tarjeta = t.get_text(" ", strip=True)
                html_tarjeta = str(t)

                # Buscar 4 dígitos exactos evitando tomar los números del año actual
                cifras = re.findall(r"\b\d{4}\b", txt_tarjeta)
                cifras_validas = [c for c in cifras if c != AÑO_ACTUAL]

                if cifras_validas:
                    cifra_4 = cifras_validas[0]

                    if "Astro" in sorteo:
                        signo = extraer_signo(txt_tarjeta + " " + html_tarjeta)
                        if signo:
                            cifra_4 = f"{cifra_4}-{signo}"
                        else:
                            continue

                    if sorteo == "Cafeterito Noche":
                        tiene_cafeterito_noche = True

                    resultados.append({
                        "fecha": fecha_real,
                        "sorteo": sorteo,
                        "resultado": cifra_4,
                    })
                    sorteos_fecha_procesados.add(clave_procesada)

    except Exception as e:
        print(f"[SCRAPER EXCEPCIÓN] {e}")

    # RESCATES QUIRÚRGICOS GARANTIZADOS DESDE GANARCHANCE.COM
    if not tiene_cafeterito_noche:
        rescate_caf = rescatar_cafeterito_noche()
        if rescate_caf:
            resultados.append(rescate_caf)

    # Astro Luna siempre se procesa por ganarchance.com para máxima precisión
    rescate_astro = rescatar_astro_luna()
    if rescate_astro:
        resultados.append(rescate_astro)

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
            memoria_dict = {}

    nuevos = extraer_resultados_chancehoy()

    registros_nuevos_count = 0
    for item in nuevos:
        clave = f"{item['fecha']}_{item['sorteo']}"
        if clave not in memoria_dict:
            registros_nuevos_count += 1
        memoria_dict[clave] = item

    lista_final = list(memoria_dict.values())
    lista_final.sort(key=lambda x: (x["fecha"], x["sorteo"]), reverse=True)

    with open(archivo, "w", encoding="utf-8") as f:
        json.dump(lista_final, f, ensure_ascii=False, indent=2)

    print(
        f"✅ Extracción finalizada con éxito. Nuevos insertados:"
        f" {registros_nuevos_count} | Total en sorteos.json: {len(lista_final)}"
    )


if __name__ == "__main__":
    actualizar_sorteos_json()
