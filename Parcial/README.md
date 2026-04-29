# Calidad del Agua en la India — Procesamiento con PySpark y Machine Learning

**Autor:** Daniel Felipe Castro Moreno  
**Inicio:** 16/04/2026 · **Última actualización:** 22/04/2026  
**Asignatura:** Procesamiento de Alto Volumen de Datos

---

## Descripción

Este taller aplica técnicas de procesamiento distribuido con **PySpark** y aprendizaje automático con **Keras/TensorFlow** para analizar y clasificar la calidad del agua en ríos de la India. Los datos provienen de la plataforma oficial RiverIndia y contienen mediciones fisicoquímicas y bacteriológicas de múltiples estaciones de monitoreo.

El objetivo principal es construir un **Índice de Calidad del Agua (WQI)** basado en literatura técnica especializada ([IntechOpen](https://www.intechopen.com/chapters/69568)) y entrenar una red neuronal que clasifique la calidad del agua a partir de los parámetros medidos en campo.

---

## Estructura del Proyecto

```
.
├── Clean_ML_Water.ipynb     # Notebook principal
├── waterquality.csv         # Dataset de calidad del agua (RiverIndia)
├── Indian_States.shp        # Shapefile de estados de la India (y archivos asociados)
└── README.md
```

---

## Requisitos

**Python 3.x** con las siguientes bibliotecas:

```
pyspark
findspark
pandas
numpy
matplotlib
seaborn
scikit-learn
tensorflow
keras
geopandas
adjustText
mapclassify >= 2.4.0
```

Instalación rápida:

```bash
pip install pyspark findspark pandas numpy matplotlib seaborn scikit-learn tensorflow geopandas adjustText mapclassify
```

También se requiere tener **Apache Spark** instalado. El notebook lo busca en `/Almacen/Spark`; ajustar la ruta en `findspark.init()` según el entorno local.

---

## Metodología

### 1. Carga y exploración de datos
- Lectura del archivo `waterquality.csv` con el lector de Spark (CSV con encabezado).
- Inspección del esquema, tipos de datos y estadísticas descriptivas por columna.

### 2. Variables del dataset

| Variable | Descripción | Unidad |
|---|---|---|
| `STATION CODE` | Identificador de la estación | — |
| `LOCATIONS` | Punto de muestreo | — |
| `STATE` | Estado de la India | — |
| `TEMP` | Temperatura | °C |
| `DO` | Oxígeno Disuelto | mg/L |
| `pH` | Potencial de Hidrógeno | 0–14 |
| `CONDUCTIVITY` | Conductividad eléctrica | µS/cm |
| `BOD` | Demanda Bioquímica de Oxígeno | mg/L |
| `NITRATE_N_NITRITE_N` | Nitratos y Nitritos | mg/L |
| `FECAL_COLIFORM` | Coliformes Fecales | UFC |
| `TOTAL_COLIFORM` | Coliformes Totales | *eliminada* |

### 3. Limpieza y preprocesamiento
- Detección de valores `"NA"` como cadena de texto (causados por el formato original del CSV).
- Casting de columnas a tipos numéricos (`Float`, `Integer`).
- **Imputación por media** para variables fisicoquímicas con baja tasa de nulos (TEMP, DO, pH, BOD, NITRATE, CONDUCTIVITY).
- **Eliminación de filas** para `FECAL_COLIFORM` (~15% nulos) para evitar sesgos en el indicador bacteriológico.
- **Winsorización** (percentil 1–99) en variables de alta varianza: BOD, CONDUCTIVITY, FECAL_COLIFORM, NITRATE.
- Filtrado de valores de pH físicamente imposibles (< 0 o > 14).

### 4. Construcción del WQI
Se asigna un puntaje discreto (0, 40, 60, 80, 100) a cada parámetro según rangos de la literatura, y se pondera cada uno según su relevancia:

| Parámetro | Columna | Peso |
|---|---|---|
| Oxígeno Disuelto | `wDO` | 28.1% |
| Coliformes Fecales | `wFecal` | 28.1% |
| Conductividad | `wCOND` | 23.4% |
| pH | `wpH` | 16.5% |
| Nitratos/Nitritos | `wNN` | 2.8% |
| BOD | `wBOD` | 0.9% |

**Clasificación final del WQI:**

| Rango | Categoría |
|---|---|
| 0 – 25 | Excelente |
| 25 – 50 | Buena |
| 50 – 75 | Baja |
| 75 – 100 | Muy Baja |
| > 100 | Inadecuada |

### 5. Visualización geográfica
- Mapas coropléticos con **GeoPandas** integrando los shapefiles de estados de la India.
- Homologación de nombres de estados entre el dataset de Spark y la cartografía.
- Histograma horizontal de WQI por estado.

### 6. Modelo de clasificación (Keras)
- **Features:** 7 mediciones fisicoquímicas crudas (TEMP, DO, pH, CONDUCTIVITY, BOD, NITRATE_N_NITRITE_N, FECAL_COLIFORM).
- **Target:** Categoría de calidad (`CALIDAD`) — 5 clases.
- **Preprocesamiento:** `StandardScaler` + codificación con `LabelEncoder`.
- **Arquitectura:** `Dense(64, relu) → Dropout(0.3) → Dense(32, relu) → Dropout(0.3) → Dense(5, softmax)`.
- **Entrenamiento:** `EarlyStopping(patience=15)` sobre `val_loss`, con `validation_split=0.2`.
- **Métricas:** Accuracy, Precision, Recall, F1 Score (ponderado) y Matriz de Confusión.

---

## Resultados principales

- La categoría **Baja** domina el dataset (>55% de los registros), lo que refleja una degradación generalizada de los cuerpos hídricos analizados.
- La categoría **Excelente** representa apenas ~3% del total.
- Los focos de contaminación bacteriológica más intensos se concentran en zonas costeras y de alta densidad poblacional.
- El modelo de red neuronal enfrenta desbalance de clases; el **F1 ponderado** es la métrica más representativa del rendimiento real.

---

## Notas

- El WQI calculado tiene propósito **educativo y de demostración técnica**. No debe usarse como referencia oficial para decisiones de salud pública o gestión ambiental.
- La ruta de Spark (`/Almacen/Spark`) debe ajustarse al entorno de ejecución.
- Los shapefiles de India deben estar en el mismo directorio que el notebook.

---

## Referencia bibliográfica

> IntechOpen — Water Quality Parameters: [https://www.intechopen.com/chapters/69568](https://www.intechopen.com/chapters/69568)