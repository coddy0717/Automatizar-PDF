"""
main.py
=======

Punto de entrada de la aplicación. Encadena todo el proceso:

    leer CSV -> procesar estudiantes -> generar resumen -> generar PDF

Se ejecuta desde la terminal (con el entorno virtual activado):

    python main.py

Opcionalmente se pueden indicar rutas propias:

    python main.py ruta/al/datos.csv ruta/de/salida.pdf
"""

import os
import sys

# Importamos las funciones del módulo con la lógica.
from generador_reportes import (
    leer_csv,
    procesar_estudiantes,
    generar_resumen,
    generar_pdf,
)

# Rutas por defecto (relativas a la ubicación de este archivo), de modo que
# el programa funcione sin importar desde qué carpeta se ejecute.
CARPETA_BASE = os.path.dirname(os.path.abspath(__file__))
CSV_POR_DEFECTO = os.path.join(CARPETA_BASE, "data", "estudiantes.csv")
PDF_POR_DEFECTO = os.path.join(CARPETA_BASE, "reportes", "reporte.pdf")


def main(ruta_csv=CSV_POR_DEFECTO, ruta_pdf=PDF_POR_DEFECTO):
    """Ejecuta el proceso completo y devuelve la ruta del PDF generado.

    Todo el flujo va dentro de un try/except para mostrar mensajes claros
    en lugar de un error técnico difícil de entender.

    Args:
        ruta_csv (str): Ruta del archivo CSV de entrada.
        ruta_pdf (str): Ruta del PDF de salida.

    Returns:
        str | None: Ruta del PDF si todo salió bien; None si hubo un error.
    """
    try:
        print(f"Leyendo datos desde: {ruta_csv}")
        filas = leer_csv(ruta_csv)

        # Procesamos: agrupamos por estudiante, calculamos promedio y estado.
        resultados = procesar_estudiantes(filas)

        # Calculamos las estadísticas generales del grupo.
        resumen = generar_resumen(resultados)

        # Construimos el PDF.
        generar_pdf(resultados, resumen, ruta_pdf)

        # Mensajes finales para el usuario.
        print("Reporte generado correctamente.")
        print(f"  - Estudiantes procesados : {resumen['total']}")
        print(f"  - Aprobados              : {resumen['aprobados']}")
        print(f"  - Reprobados             : {resumen['reprobados']}")
        print(f"  - Promedio general       : {resumen['promedio_general']}")
        print(f"  - PDF guardado en        : {ruta_pdf}")
        return ruta_pdf

    except FileNotFoundError as error:
        # El archivo CSV no existe.
        print(f"[Error] {error}")
    except ValueError as error:
        # Datos inválidos dentro del CSV (nota no numérica, columnas faltantes, etc.).
        print(f"[Error de datos] {error}")
    except Exception as error:  # Red de seguridad para cualquier otro problema.
        print(f"[Error inesperado] {error}")

    return None


if __name__ == "__main__":
    # Permite pasar las rutas como argumentos de la terminal (opcional).
    # sys.argv[0] es el nombre del script; los siguientes son los argumentos.
    csv_entrada = sys.argv[1] if len(sys.argv) > 1 else CSV_POR_DEFECTO
    pdf_salida = sys.argv[2] if len(sys.argv) > 2 else PDF_POR_DEFECTO

    resultado = main(csv_entrada, pdf_salida)

    # Devolvemos un código de salida distinto de 0 si algo falló, útil para scripts/CI.
    sys.exit(0 if resultado else 1)
