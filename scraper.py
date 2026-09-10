import json
import os
import re
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup


def obtener_hora_colombia():
    """Retorna la fecha y hora actual en zona horaria de Colombia (UTC-5)."""
    return datetime.utcnow() - timedelta(hours=5)


AÑO_ACTUAL = str(obtener_hora_colombia().year)

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
    ("LOTERIA DEL VALLE", "VALLE"),
    ("LOTERIA VALLE", "VALLE"),
    ("VALLE", "VALLE"),
    ("LOTERIA DE MANIZALES", "MANIZALES"),
    ("MANIZALES", "MANIZALES"),
    ("LOTERIA DEL META", "META"),
    ("META", "META"),
    ("TOLIMA", "TOLIMA"),
    ("BOGOTA", "BOGOTA"),
    ("BOGOTÁ", "BOGOTA"),
    ("MEDELLIN", "MEDELLIN"),
    ("MEDELLÍN", "MEDELLIN"),
    ("HUILA", "HUILA"),
    ("RISARALDA", "RISARALDA"),
    ("CRUZ ROJA", "CRUZ ROJA"),
    ("CUNDINAMARCA", "CUNDINAMARCA"),
    ("SANTANDER", "SANTANDER"),
    ("CAUCA", "CAUCA"),
    ("BOYACA", "BOYACA"),
    ("BOYACÁ", "BOYACA"),
]

DIAS_OFICIALES_LOTERIAS = {
    "CUNDINAMARCA": [0],
    "TOLIMA": [0],
    "CRUZ ROJA": [1],
    "HUILA": [1],
    "MANIZALES": [2],
    "META": [2],
    "VALLE": [2],
    "BOGOTA": [3],
    "QUINDIO": [3],
    "MEDELLIN": [4],
    "RISARALDA": [4],
    "SANTANDER": [4],
    "BOYACA": [5],
    "CAUCA": [5],
}

SIGNOS = [
    "ARIES",
    "TAURO",
    "GEMINIS",
    "CANCER",
    "LEO",
    "VIRGO",
    "LIBRA",
    "ESCORPIO",
    "ESCORPION",
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
            return "ESCORPIO" if s == "ESCORPION" else s
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


def extraer_cifra_4(texto):
    """Extrae 4 dígitos asegurando descartar explícitamente el año actual (2026)."""
    # 1. Buscar bloques exactos de 4 dígitos descartando el año actual
    bloques = re.findall(r"\b\d{4}\b", texto)
    bloques_validos = [b for b in bloques if b != AÑO_ACTUAL]
    if bloques_validos:
        return bloques_validos[0]

    # 2. Si vienen separados por tags, capturar dígitos ignorando secuencias que formen el año actual
    digitos = re.findall(r"\d", texto)
    if len(digitos) >= 4:
        cifra_unida = "".join(digitos[:4])
        if cifra_unida != AÑO_ACTUAL:
            return cifra_unida
        elif len(digitos) >= 8:
            cifra_secundaria = "".join(digitos[4:8])
            if cifra_secundaria != AÑO_ACTUAL:
                return cifra_secundaria

    return None


def ajustar_fecha_segun_dia_oficial(sorteo, fecha_str):
    if sorteo in DIAS_OFICIALES_LOTERIAS:
        dias_permitidos = DIAS_OFICIALES_LOTERIAS[sorteo]
        try:
            dt = datetime.strptime(fecha_str, "%Y-%m-%d")
            if dt.weekday() not in dias_permitidos:
                for i in range(1, 7):
                    dt_prev = dt - timedelta(days=i)
                    if dt_prev.weekday() in dias_permitidos:
                        return dt_prev.strftime("%Y-%m-%d")
        except Exception as e:
            print(f"[REAJUSTE FECHA ERROR] {e}")

    return fecha_str


def extraer_resultados_chancehoy():
    resultados = []
    url = "https://www.chancehoy.com/"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        res = requests.get(url, headers=headers, timeout=12)
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
                fecha_real = ajustar_fecha_segun_dia_oficial(sorteo, fecha_real)

                clave_procesada = f"{fecha_real}_{sorteo}"
                if clave_procesada in sorteos_fecha_procesados:
                    continue

                txt_tarjeta = t.get_text(" ", strip=True)
                cifra_4 = extraer_cifra_4(txt_tarjeta)

                if cifra_4 and cifra_4 != AÑO_ACTUAL:
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
        print(f"[CHANCEHOY WARNING] {e}")

    return resultados


def rescate_emergencia_ganarchance(resultados_actuales):
    sorteos_ya_capturados = {r["sorteo"] for r in resultados_actuales}
    rescatados = []

    url = "https://www.ganarchance.com/"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        res = requests.get(url, headers=headers, timeout=12)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")

            txt_pagina = soup.get_text(" ", strip=True)
            fecha_real_pagina = extraer_fecha_de_encabezado_texto(txt_pagina)
            if not fecha_real_pagina:
                fecha_real_pagina = obtener_hora_colombia().strftime("%Y-%m-%d")

            items = soup.find_all("div", class_="flex-item")
            for item in items:
                elem_nombre = item.find("div", class_="nombre")
                if not elem_nombre:
                    continue

                nombre_txt = elem_nombre.get_text(" ", strip=True)
                sorteo_oficial = identificar_sorteo(nombre_txt)

                if not sorteo_oficial or sorteo_oficial in sorteos_ya_capturados:
                    continue

                elem_numero = item.find("div", class_="numero")
                if not elem_numero:
                    continue

                txt_num = elem_numero.get_text(" ", strip=True)
                cifra = extraer_cifra_4(txt_num)

                if cifra and cifra != AÑO_ACTUAL:
                    fecha_corregida = ajustar_fecha_segun_dia_oficial(
                        sorteo_oficial, fecha_real_pagina
                    )

                    if "Astro" in sorteo_oficial:
                        signo = extraer_signo(item.get_text(" ", strip=True))
                        if signo:
                            cifra = f"{cifra}-{signo}"
                        else:
                            continue

                    rescatados.append({
                        "fecha": fecha_corregida,
                        "sorteo": sorteo_oficial,
                        "resultado": cifra,
                    })
                    sorteos_ya_capturados.add(sorteo_oficial)

    except Exception as e:
        print(f"[RESCATE GANARCHANCE ERROR] {e}")

    return rescatados


def sanitizar_y_limpiar_errados(memoria_dict):
    """PULGADO AUTOMÁTICO DE RESULTADOS '2026'.

    Elimina de la memoria cualquier entrada donde el resultado sea '2026' o
    empiece por '2026-'.
    """
    memoria_limpia = {}

    for clave, item in memoria_dict.items():
        res = str(item.get("resultado", ""))
        # Si el resultado es "2026" o "2026-SIGNO", se descarta la entrada errónea
        if res == AÑO_ACTUAL or res.startswith(f"{AÑO_ACTUAL}-"):
            print(
                f"🗑️ Purgando registro corrupto: {item.get('sorteo')} -"
                f" {item.get('fecha')} -> {res}"
            )
            continue
        memoria_limpia[clave] = item

    return memoria_limpia


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

    # 1. Purgar inmediatamente cualquier dato erróneo de "2026"
    memoria_dict = sanitizar_y_limpiar_errados(memoria_dict)

    # 2. Re-extraer desde fuentes web los números reales
    nuevos = extraer_resultados_chancehoy()
    rescatados = rescate_emergencia_ganarchance(nuevos)

    # 3. Guardar solo datos válidos
    for item in nuevos + rescatados:
        clave = f"{item['fecha']}_{item['sorteo']}"
        memoria_dict[clave] = item

    lista_final = list(memoria_dict.values())
    lista_final.sort(key=lambda x: (x["fecha"], x["sorteo"]), reverse=True)

    with open(archivo, "w", encoding="utf-8") as f:
        json.dump(lista_final, f, ensure_ascii=False, indent=2)

    print(
        "✅ Limpieza y actualización completadas. Total registros en"
        f" sorteos.json: {len(lista_final)}"
    )


if __name__ == "__main__":
    actualizar_sorteos_json()
