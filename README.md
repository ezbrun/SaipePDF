# I 🤖 PDF

App web en Streamlit para consolidar o separar PDFs con selección por rangos y marcadores automáticos.

## Funcionalidades

- Consolidar: todas las páginas, primeras, últimas o rangos por archivo (ej. `1, 2, 20, 25, 45:57, 66:89`). Crea bookmarks con el nombre del PDF y el rango usado.
- Separar: todas las hojas, o rangos/páginas por archivo. Podés descargar un ZIP con PDFs individuales (cada uno con bookmark) o consolidar todo en un solo PDF con bookmarks anidados por archivo y rango.
- Ordenar archivos por nombre y descargar con el nombre de salida que elijas.
- Botón de donación a Cafecito incluido en la UI.

## Requisitos

- Python 3.11+ (o usar Docker/Compose)

## Ejecutar con Python

```bash
pip install -r Requirements.txt
streamlit run app.py
```

Abrí el enlace local que muestra Streamlit (por defecto http://localhost:8501).

## Ejecutar con Docker Compose

```bash
docker compose up --build
```

Luego abrí http://localhost:8501.

## Uso rápido

- Subí uno o varios PDFs.
- Elegí el modo (consolidar o separar) y define los rangos si aplica, usando comas para separar páginas/rangos.
- Descargá el resultado (PDF o ZIP) con los bookmarks generados automáticamente.

## Licencia

Licencia PL: uso gratuito, no comercial; derivados deben mantenerse abiertos y gratuitos.
