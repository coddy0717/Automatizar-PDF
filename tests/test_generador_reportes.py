"""
Pruebas unitarias del módulo ``generador_reportes`` usando pytest.

Se cubren todas las funciones principales. Para no tocar archivos reales,
usamos el fixture ``tmp_path`` que pytest ofrece: es una carpeta temporal
única por prueba que se borra automáticamente al terminar.

Ejecutar desde la raíz del proyecto:

    pytest -v
"""

import os
import sys

import pytest

# Aseguramos que Python encuentre el módulo aunque las pruebas estén en /tests.
# Añadimos la carpeta raíz del proyecto (un nivel arriba de este archivo) al path.
RAIZ_PROYECTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ_PROYECTO not in sys.path:
    sys.path.insert(0, RAIZ_PROYECTO)

import generador_reportes as gr  # noqa: E402  (import después de ajustar sys.path)


# ---------------------------------------------------------------------------
# Datos de apoyo reutilizables por varias pruebas
# ---------------------------------------------------------------------------
FILAS_EJEMPLO = [
    {"nombre": "Ana", "materia": "Matemáticas", "nota": 11.0},
    {"nombre": "Ana", "materia": "Historia", "nota": 6.0},
    {"nombre": "Luis", "materia": "Matemáticas", "nota": 5.0},
    {"nombre": "Luis", "materia": "Historia", "nota": 4.0},
]


def _crear_csv(carpeta, contenido):
    """Helper: crea un CSV temporal con el contenido dado y devuelve su ruta."""
    ruta = os.path.join(str(carpeta), "datos.csv")
    with open(ruta, "w", newline="", encoding="utf-8") as archivo:
        archivo.write(contenido)
    return ruta


# ---------------------------------------------------------------------------
# Pruebas de leer_csv
# ---------------------------------------------------------------------------
def test_leer_csv_valido(tmp_path):
    """Un CSV correcto se lee y convierte la nota a float."""
    contenido = "nombre,materia,nota\nAna,Matemáticas,8.5\nAna,Historia,7\n"
    ruta = _crear_csv(tmp_path, contenido)

    filas = gr.leer_csv(ruta)

    assert len(filas) == 2
    assert filas[0] == {"nombre": "Ana", "materia": "Matemáticas", "nota": 8.5}
    # La nota debe quedar como número (float), no como texto.
    assert isinstance(filas[0]["nota"], float)


def test_leer_csv_archivo_inexistente():
    """Si el archivo no existe, debe lanzarse FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        gr.leer_csv("ruta/que/no/existe.csv")


def test_leer_csv_nota_no_numerica(tmp_path):
    """Una nota que no es número debe producir un ValueError."""
    contenido = "nombre,materia,nota\nAna,Matemáticas,ocho\n"
    ruta = _crear_csv(tmp_path, contenido)

    with pytest.raises(ValueError):
        gr.leer_csv(ruta)


def test_leer_csv_columna_faltante(tmp_path):
    """Si falta una columna requerida, debe lanzarse ValueError."""
    contenido = "nombre,nota\nAna,8\n"  # Falta 'materia'.
    ruta = _crear_csv(tmp_path, contenido)

    with pytest.raises(ValueError):
        gr.leer_csv(ruta)


# ---------------------------------------------------------------------------
# Pruebas de calcular_promedio
# ---------------------------------------------------------------------------
def test_calcular_promedio_correcto():
    """El promedio se calcula y redondea a 2 decimales."""
    assert gr.calcular_promedio([8.0, 6.0]) == 7.0
    assert gr.calcular_promedio([5.0, 4.0, 4.0]) == 4.33  # 13/3 = 4.333...


def test_calcular_promedio_lista_vacia():
    """Una lista vacía debe lanzar ValueError."""
    with pytest.raises(ValueError):
        gr.calcular_promedio([])


# ---------------------------------------------------------------------------
# Pruebas de determinar_estado
# ---------------------------------------------------------------------------
def test_determinar_estado_aprobado():
    assert gr.determinar_estado(8.0) == "Aprobado"


def test_determinar_estado_reprobado():
    assert gr.determinar_estado(5.0) == "Reprobado"


def test_determinar_estado_borde_exacto():
    """Justo en el umbral (7.0) el estudiante aprueba."""
    assert gr.determinar_estado(7.0) == "Aprobado"


# ---------------------------------------------------------------------------
# Pruebas de procesar_estudiantes
# ---------------------------------------------------------------------------
def test_procesar_estudiantes_agrupa_y_calcula():
    """Agrupa por estudiante, calcula promedio y estado, y ordena por nombre."""
    resultados = gr.procesar_estudiantes(FILAS_EJEMPLO)

    # Hay dos estudiantes: Ana y Luis (ordenados alfabéticamente).
    assert len(resultados) == 2
    assert resultados[0]["nombre"] == "Ana"
    assert resultados[1]["nombre"] == "Luis"

    # Ana: (8 + 6) / 2 = 7.0 -> Aprobado.
    assert resultados[0]["promedio"] == 7.0
    assert resultados[0]["estado"] == "Aprobado"
    assert len(resultados[0]["materias"]) == 2

    # Luis: (5 + 4) / 2 = 4.5 -> Reprobado.
    assert resultados[1]["promedio"] == 4.5
    assert resultados[1]["estado"] == "Reprobado"


# ---------------------------------------------------------------------------
# Pruebas de generar_resumen
# ---------------------------------------------------------------------------
def test_generar_resumen_calcula_totales():
    """El resumen cuenta aprobados/reprobados y calcula promedios y porcentaje."""
    resultados = gr.procesar_estudiantes(FILAS_EJEMPLO)
    resumen = gr.generar_resumen(resultados)

    assert resumen["total"] == 2
    assert resumen["aprobados"] == 1
    assert resumen["reprobados"] == 1
    # Promedio general: (7.0 + 4.5) / 2 = 5.75.
    assert resumen["promedio_general"] == 5.75
    # Porcentaje de aprobación: 1 de 2 = 50 %.
    assert resumen["porcentaje_aprobacion"] == 50.0


def test_generar_resumen_lista_vacia():
    """Sin estudiantes, generar_resumen debe lanzar ValueError."""
    with pytest.raises(ValueError):
        gr.generar_resumen([])


# ---------------------------------------------------------------------------
# Pruebas de generar_pdf
# ---------------------------------------------------------------------------
def test_generar_pdf_crea_archivo(tmp_path):
    """El PDF debe crearse en disco y no estar vacío."""
    resultados = gr.procesar_estudiantes(FILAS_EJEMPLO)
    resumen = gr.generar_resumen(resultados)

    ruta_pdf = os.path.join(str(tmp_path), "reporte.pdf")
    ruta_devuelta = gr.generar_pdf(resultados, resumen, ruta_pdf)

    # La función devuelve la ruta y el archivo existe con contenido (> 0 bytes).
    assert ruta_devuelta == ruta_pdf
    assert os.path.exists(ruta_pdf)
    assert os.path.getsize(ruta_pdf) > 0


def test_generar_pdf_crea_carpeta_si_no_existe(tmp_path):
    """Si la carpeta de salida no existe, generar_pdf debe crearla."""
    resultados = gr.procesar_estudiantes(FILAS_EJEMPLO)
    resumen = gr.generar_resumen(resultados)

    # Ruta dentro de una subcarpeta que todavía no existe.
    ruta_pdf = os.path.join(str(tmp_path), "salida", "reporte.pdf")
    gr.generar_pdf(resultados, resumen, ruta_pdf)

    assert os.path.exists(ruta_pdf)
