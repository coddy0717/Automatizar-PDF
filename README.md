# Automatizar PDF — Reporte de Calificaciones

Aplicación sencilla en **Python** que automatiza la generación de reportes en **PDF**
a partir de un archivo **CSV** de estudiantes. Lee los datos (`nombre, materia, nota`),
calcula el **promedio por estudiante**, determina si **aprobó o reprobó**, y produce
un PDF con un **resumen general** y el **detalle por estudiante**.

Pensada como proyecto educativo: código organizado en funciones, comentado, con
manejo de errores y pruebas automáticas.

![Pruebas](https://github.com/coddy0717/Automatizar-PDF/actions/workflows/test.yml/badge.svg)

---

## Características

- Lee un CSV con columnas `nombre`, `materia`, `nota`.
- Calcula el promedio de cada estudiante (varias materias por estudiante).
- Marca **Aprobado** / **Reprobado** según el umbral configurable.
- Genera un PDF con tablas de resumen y de detalle (verde = aprobado, rojo = reprobado).
- Manejo de errores claro (archivo inexistente, notas inválidas, columnas faltantes).
- Pruebas unitarias con `pytest` e integración continua con GitHub Actions.

Escala de notas: **0 a 10**. Nota mínima para aprobar: **7**
(configurable en la constante `UMBRAL_APROBACION` de `generador_reportes.py`).

---

## Requisitos

- Python 3.11
- Librerías: `reportlab` (PDF) y `pytest` (pruebas). Las librerías `csv` y `os`
  vienen incluidas en Python.

---

## Instalación

```bash
# 1) Crear el entorno virtual (si aún no existe)
python -m venv myenv

# 2) Activar el entorno virtual
#    Windows (PowerShell):
myenv\Scripts\Activate.ps1
#    Windows (CMD):
myenv\Scripts\activate.bat
#    Linux / macOS:
source myenv/bin/activate

# 3) Instalar las dependencias
pip install -r requirements.txt
```

> Nota: en este proyecto el entorno virtual `myenv` se encuentra en la carpeta
> superior a la del código. Ajusta la ruta de activación según dónde lo tengas.

---

## Uso

Con el entorno virtual activado, desde la carpeta del proyecto:

```bash
# Usa el CSV de ejemplo (data/estudiantes.csv) y crea reportes/reporte.pdf
python main.py

# O indica rutas propias: python main.py <csv_entrada> <pdf_salida>
python main.py data/estudiantes.csv reportes/mi_reporte.pdf
```

Al terminar verás un resumen en la terminal y el PDF en la carpeta `reportes/`.

### Formato del CSV

```csv
nombre,materia,nota
Ana Torres,Matemáticas,8.5
Ana Torres,Historia,7.0
Luis Gómez,Matemáticas,5.5
```

Cada fila es una materia de un estudiante. El estudiante puede repetirse en
varias filas; el promedio se calcula con todas sus notas.

---

## Ejecutar las pruebas

```bash
pytest -v
```

Las pruebas cubren todas las funciones principales y usan carpetas temporales,
por lo que no modifican tus archivos.

---

## Estructura del proyecto

```
Automatizar-PDF/
├── .github/workflows/test.yml      # CI: instala Python 3.11, deps y corre pytest
├── data/
│   └── estudiantes.csv             # Datos de ejemplo
├── reportes/                       # Salida de los PDF (se ignora en git)
├── tests/
│   └── test_generador_reportes.py  # Pruebas unitarias (pytest)
├── generador_reportes.py           # Módulo con todas las funciones
├── main.py                         # Punto de entrada del programa
├── requirements.txt                # Dependencias
├── .gitignore
└── README.md
```

---

## Funciones principales (`generador_reportes.py`)

| Función | Descripción |
|--------|-------------|
| `leer_csv(ruta_csv)` | Lee y valida el CSV; devuelve la lista de filas. |
| `calcular_promedio(notas)` | Promedio de una lista de notas. |
| `determinar_estado(promedio, umbral)` | Devuelve "Aprobado" o "Reprobado". |
| `procesar_estudiantes(filas, umbral)` | Agrupa por estudiante y calcula promedio/estado. |
| `generar_resumen(resultados)` | Estadísticas generales del grupo. |
| `generar_pdf(resultados, resumen, ruta_pdf)` | Construye el reporte PDF. |

---

## Licencia

Proyecto educativo de uso libre.
