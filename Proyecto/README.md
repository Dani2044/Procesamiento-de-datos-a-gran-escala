# proyecto_procesamiento

Proyecto de investigación en Big Data desarrollado para la materia **Procesamiento de Datos** de la Pontificia Universidad Javeriana. El proyecto actúa como consultoría para el Ministerio de Educación de Colombia, buscando identificar los factores territoriales, socioeconómicos y de infraestructura que impactan los resultados de las pruebas Saber 11° a nivel municipal.

## Integrantes
- Julián Camilo Gaitán Contreras
- Daniel Felipe Castro Moreno
- Nicolas Algarra Polanco
- Sebastián Angulo Vergara

## Descripción del Proyecto

A partir del procesamiento de múltiples conjuntos de datos con Apache Spark, se busca responder preguntas de negocio estratégicas relacionadas con conectividad, pobreza, gestión del riesgo y calidad educativa en Colombia, con el fin de construir un plan de acción basado en evidencia cuantitativa.

## Datasets utilizados

| Dataset | Fuente |
|---|---|
| Beneficiarios Estrategia UNIDOS | datos.gov.co |
| Internet Fijo por Tecnología y Segmento | datos.gov.co |
| Matrícula Educación Superior por Municipio | MEN |
| Estadísticas Educación Preescolar, Básica y Media | MEN |
| Gestión del Riesgo Municipal (IMRC) | UNGRD |
| COVID-19 por municipio y departamento | INS (Web Scraping) |

### Dataset externo — Resultados Saber 11

Los resultados de la prueba Saber 11° no se encuentran en este repositorio debido al tamaño del archivo. Pueden descargarse directamente desde el portal de datos abiertos del gobierno:

[Resultados Únicos Saber 11 — datos.gov.co](https://www.datos.gov.co/Educaci-n/Resultados-nicos-Saber-11/kgxf-xxbe/about_data)

## Tecnologías utilizadas
- Apache Spark (PySpark)
- Python (Jupyter Notebooks)
- Web Scraping (requests, BeautifulSoup)
- OpenWeatherMap API
