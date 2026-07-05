"""
generador_reportes.py
======================

Módulo con la lógica para automatizar la generación de reportes PDF a partir
de un archivo CSV de estudiantes.

Flujo del proceso:
    1. Leer el CSV (columnas: nombre, materia, nota).
    2. Agrupar las notas por estudiante y calcular su promedio.
    3. Determinar si cada estudiante aprobó o reprobó.
    4. Calcular un resumen general del grupo.
    5. Generar un reporte PDF con el resumen y el detalle por estudiante.

Solo se utilizan las librerías pedidas:
    - csv        -> leer el archivo de datos.
    - reportlab  -> construir el PDF.
    - os         -> trabajar con rutas y carpetas.

El código está pensado para ser fácil de leer por alguien que recién aprende
Python: cada función hace una sola cosa, tiene su docstring y sus comentarios.
"""

import csv
import os

# reportlab: componentes para armar el PDF de forma sencilla ("platypus").
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

# ---------------------------------------------------------------------------
# Constantes de configuración (fáciles de ajustar en un solo lugar)
# ---------------------------------------------------------------------------
UMBRAL_APROBACION = 7.0        # Nota mínima (promedio) para aprobar.
NOTA_MINIMA = 0.0             # Nota más baja posible en la escala.
NOTA_MAXIMA = 10.0           # Nota más alta posible en la escala.

# Nombres de columna que esperamos encontrar en el CSV.
COLUMNAS_REQUERIDAS = ("nombre", "materia", "nota")


# ---------------------------------------------------------------------------
# 1. Lectura del archivo CSV
# ---------------------------------------------------------------------------
def leer_csv(ruta_csv):
    """Lee el archivo CSV y devuelve una lista de diccionarios.

    Cada diccionario representa una fila con las claves:
    ``nombre`` (str), ``materia`` (str) y ``nota`` (float).

    Args:
        ruta_csv (str): Ruta al archivo CSV.

    Returns:
        list[dict]: Filas leídas y validadas.

    Raises:
        FileNotFoundError: Si el archivo no existe.
        ValueError: Si el archivo está vacío, le faltan columnas
            o alguna nota no es un número válido / está fuera de rango.
    """
    # Comprobamos que el archivo exista antes de intentar abrirlo.
    if not os.path.exists(ruta_csv):
        raise FileNotFoundError(f"No se encontró el archivo CSV: {ruta_csv}")

    filas = []

    # 'newline=""' es la forma recomendada de abrir CSV en Python.
    # 'encoding="utf-8-sig"' permite leer tildes y quita el BOM si Excel lo agregó.
    with open(ruta_csv, mode="r", newline="", encoding="utf-8-sig") as archivo:
        lector = csv.DictReader(archivo)

        # Si el CSV no tiene encabezados, 'fieldnames' es None.
        if lector.fieldnames is None:
            raise ValueError("El archivo CSV está vacío o no tiene encabezados.")

        # Normalizamos los encabezados (sin espacios y en minúsculas) para
        # comparar de forma flexible.
        encabezados = [columna.strip().lower() for columna in lector.fieldnames]
        for columna in COLUMNAS_REQUERIDAS:
            if columna not in encabezados:
                raise ValueError(
                    f"El CSV debe tener las columnas {COLUMNAS_REQUERIDAS}. "
                    f"Falta la columna: '{columna}'."
                )

        # Recorremos cada fila. 'start=2' porque la línea 1 son los encabezados.
        for numero_fila, fila in enumerate(lector, start=2):
            nombre = (fila.get("nombre") or "").strip()
            materia = (fila.get("materia") or "").strip()
            nota_texto = (fila.get("nota") or "").strip()

            # Saltamos filas completamente vacías (comunes al final del archivo).
            if not nombre and not materia and not nota_texto:
                continue

            # Validamos que no falten datos en la fila.
            if not nombre or not materia or not nota_texto:
                raise ValueError(
                    f"Fila {numero_fila}: faltan datos (nombre, materia o nota)."
                )

            # Convertimos la nota a número. Aceptamos coma o punto decimal.
            try:
                nota = float(nota_texto.replace(",", "."))
            except ValueError:
                raise ValueError(
                    f"Fila {numero_fila}: la nota '{nota_texto}' no es un número válido."
                )

            # Validamos que la nota esté dentro de la escala permitida.
            if not (NOTA_MINIMA <= nota <= NOTA_MAXIMA):
                raise ValueError(
                    f"Fila {numero_fila}: la nota {nota} está fuera del rango "
                    f"[{NOTA_MINIMA}, {NOTA_MAXIMA}]."
                )

            filas.append({"nombre": nombre, "materia": materia, "nota": nota})

    # Si tras recorrer todo no hay filas útiles, avisamos con un error claro.
    if not filas:
        raise ValueError("El archivo CSV no contiene datos de estudiantes.")

    return filas


# ---------------------------------------------------------------------------
# 2. Cálculo del promedio
# ---------------------------------------------------------------------------
def calcular_promedio(notas):
    """Calcula el promedio de una lista de notas.

    Args:
        notas (list[float]): Notas del estudiante.

    Returns:
        float: Promedio redondeado a 2 decimales.

    Raises:
        ValueError: Si la lista de notas está vacía.
    """
    if not notas:
        raise ValueError("No se puede calcular el promedio de una lista vacía.")

    promedio = sum(notas) / len(notas)
    return round(promedio, 2)


# ---------------------------------------------------------------------------
# 3. Estado del estudiante (aprobado / reprobado)
# ---------------------------------------------------------------------------
def determinar_estado(promedio, umbral=UMBRAL_APROBACION):
    """Indica si un promedio corresponde a 'Aprobado' o 'Reprobado'.

    Args:
        promedio (float): Promedio del estudiante.
        umbral (float): Nota mínima para aprobar (por defecto UMBRAL_APROBACION).

    Returns:
        str: "Aprobado" si promedio >= umbral, en caso contrario "Reprobado".
    """
    return "Aprobado" if promedio >= umbral else "Reprobado"


# ---------------------------------------------------------------------------
# 4. Procesar todos los estudiantes
# ---------------------------------------------------------------------------
def procesar_estudiantes(filas, umbral=UMBRAL_APROBACION):
    """Agrupa las filas por estudiante y calcula promedio y estado.

    Un mismo estudiante aparece en varias filas (una por materia). Aquí las
    reunimos para obtener un único registro por estudiante.

    Args:
        filas (list[dict]): Filas devueltas por :func:`leer_csv`.
        umbral (float): Nota mínima para aprobar.

    Returns:
        list[dict]: Un diccionario por estudiante con las claves:
            - ``nombre`` (str)
            - ``materias`` (list[dict]): cada una con ``materia`` y ``nota``
            - ``promedio`` (float)
            - ``estado`` (str)
        La lista se devuelve ordenada alfabéticamente por nombre.
    """
    # Diccionario temporal: nombre -> lista de {materia, nota}.
    # Usamos un dict normal para que sea fácil de entender.
    agrupado = {}
    for fila in filas:
        nombre = fila["nombre"]
        # Si es la primera vez que vemos al estudiante, creamos su lista.
        if nombre not in agrupado:
            agrupado[nombre] = []
        agrupado[nombre].append({"materia": fila["materia"], "nota": fila["nota"]})

    resultados = []
    # 'sorted' ordena los nombres alfabéticamente para un reporte prolijo.
    for nombre in sorted(agrupado):
        materias = agrupado[nombre]
        notas = [m["nota"] for m in materias]           # Solo las notas.
        promedio = calcular_promedio(notas)             # Reutilizamos la función.
        estado = determinar_estado(promedio, umbral)    # Reutilizamos la función.

        resultados.append(
            {
                "nombre": nombre,
                "materias": materias,
                "promedio": promedio,
                "estado": estado,
            }
        )

    return resultados


# ---------------------------------------------------------------------------
# 5. Resumen general del grupo
# ---------------------------------------------------------------------------
def generar_resumen(resultados):
    """Calcula estadísticas generales a partir de los resultados.

    Args:
        resultados (list[dict]): Salida de :func:`procesar_estudiantes`.

    Returns:
        dict: Con las claves:
            - ``total`` (int): cantidad de estudiantes.
            - ``aprobados`` (int)
            - ``reprobados`` (int)
            - ``promedio_general`` (float): promedio de los promedios.
            - ``porcentaje_aprobacion`` (float): % de aprobados.

    Raises:
        ValueError: Si no hay estudiantes que resumir.
    """
    if not resultados:
        raise ValueError("No hay estudiantes para generar el resumen.")

    total = len(resultados)
    # 'sum' con una condición cuenta cuántos cumplen el estado buscado.
    aprobados = sum(1 for e in resultados if e["estado"] == "Aprobado")
    reprobados = total - aprobados

    promedio_general = round(sum(e["promedio"] for e in resultados) / total, 2)
    porcentaje_aprobacion = round((aprobados / total) * 100, 2)

    return {
        "total": total,
        "aprobados": aprobados,
        "reprobados": reprobados,
        "promedio_general": promedio_general,
        "porcentaje_aprobacion": porcentaje_aprobacion,
    }


# ---------------------------------------------------------------------------
# 6. Generación del PDF
# ---------------------------------------------------------------------------
def generar_pdf(resultados, resumen, ruta_pdf):
    """Genera el reporte PDF con el resumen general y el detalle por estudiante.

    Args:
        resultados (list[dict]): Salida de :func:`procesar_estudiantes`.
        resumen (dict): Salida de :func:`generar_resumen`.
        ruta_pdf (str): Ruta donde se guardará el PDF.

    Returns:
        str: La ruta del PDF generado.
    """
    # Si la ruta incluye una carpeta que no existe, la creamos.
    carpeta = os.path.dirname(ruta_pdf)
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)

    # 'estilos' trae estilos de párrafo predefinidos (títulos, texto normal, etc.).
    estilos = getSampleStyleSheet()

    # 'elementos' es la lista de bloques (párrafos, tablas, espacios) del PDF.
    elementos = []

    # ---- Título del reporte ----
    elementos.append(Paragraph("Reporte de Calificaciones", estilos["Title"]))
    elementos.append(Spacer(1, 0.5 * cm))  # Un espacio en blanco.

    # ---- Sección: Resumen general ----
    elementos.append(Paragraph("Resumen general", estilos["Heading2"]))
    elementos.append(Spacer(1, 0.2 * cm))

    # Datos del resumen como una tabla de dos columnas (etiqueta / valor).
    datos_resumen = [
        ["Indicador", "Valor"],
        ["Total de estudiantes", str(resumen["total"])],
        ["Aprobados", str(resumen["aprobados"])],
        ["Reprobados", str(resumen["reprobados"])],
        ["Promedio general", str(resumen["promedio_general"])],
        ["Porcentaje de aprobación", f"{resumen['porcentaje_aprobacion']} %"],
    ]
    tabla_resumen = Table(datos_resumen, colWidths=[8 * cm, 5 * cm])
    tabla_resumen.setStyle(
        TableStyle(
            [
                # Encabezado con fondo azul y letra blanca.
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E79")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                # Bordes y alineación para todas las celdas.
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#EAF1F8")]),
            ]
        )
    )
    elementos.append(tabla_resumen)
    elementos.append(Spacer(1, 0.8 * cm))

    # ---- Sección: Detalle por estudiante ----
    elementos.append(Paragraph("Detalle por estudiante", estilos["Heading2"]))
    elementos.append(Spacer(1, 0.2 * cm))

    # La primera fila es el encabezado de la tabla de detalle.
    datos_detalle = [["Estudiante", "Materias (nota)", "Promedio", "Estado"]]

    # Guardamos las filas donde el estudiante reprobó para pintarlas de otro color.
    filas_reprobadas = []

    for indice, estudiante in enumerate(resultados, start=1):
        # Convertimos la lista de materias en un texto tipo "Matemáticas: 8.0\nHistoria: 6.0".
        detalle_materias = "\n".join(
            f"{m['materia']}: {m['nota']}" for m in estudiante["materias"]
        )
        # Usamos Paragraph para que el texto de materias pueda partirse en varias líneas.
        celda_materias = Paragraph(detalle_materias.replace("\n", "<br/>"), estilos["Normal"])

        datos_detalle.append(
            [
                estudiante["nombre"],
                celda_materias,
                str(estudiante["promedio"]),
                estudiante["estado"],
            ]
        )

        # 'indice' coincide con la fila de la tabla (0 es el encabezado).
        if estudiante["estado"] == "Reprobado":
            filas_reprobadas.append(indice)

    tabla_detalle = Table(
        datos_detalle,
        colWidths=[4.5 * cm, 7 * cm, 2.5 * cm, 2.5 * cm],
    )

    # Estilo base de la tabla de detalle.
    estilo_detalle = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E79")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (2, 1), (3, -1), "CENTER"),  # Promedio y estado centrados.
    ]

    # Pintamos de verde a los aprobados (todas las filas de datos) y luego
    # sobrescribimos en rojo las filas reprobadas. Así se distingue de un vistazo.
    estilo_detalle.append(
        ("TEXTCOLOR", (3, 1), (3, -1), colors.HexColor("#1E7B34"))  # Verde: Aprobado.
    )
    for fila in filas_reprobadas:
        estilo_detalle.append(
            ("TEXTCOLOR", (3, fila), (3, fila), colors.HexColor("#B00020"))  # Rojo: Reprobado.
        )

    tabla_detalle.setStyle(TableStyle(estilo_detalle))
    elementos.append(tabla_detalle)

    # ---- Construcción final del documento ----
    documento = SimpleDocTemplate(
        ruta_pdf,
        pagesize=A4,
        title="Reporte de Calificaciones",
    )
    documento.build(elementos)

    return ruta_pdf
