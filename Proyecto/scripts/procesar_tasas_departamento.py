"""
Script: procesar_tasas_departamento.py
Fuente: JSONs de accesibilidad exportados desde INS Colombia
        - tasa_mortalidad_departamento.json
        - tasa_incidencia_departamento.json
Salida: CSV con codigo_dane, departamento, tasa_incidencia, tasa_mortalidad
"""

import json
from pathlib import Path
import pandas as pd


def extraer_filas(ruta_json: str) -> list[dict]:
    """
    Cada fila tiene role='row' y 3 hijos:
      [0] rowheader → código DANE departamento
      [1] gridcell  → valor de la tasa (con comas como separador de miles)
      [2] gridcell  → nombre del departamento
    """
    with open(ruta_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    filas = []
    for child in data.get("children", []):
        if child.get("role") != "row":
            continue
        cols = child.get("children", [])
        if len(cols) < 3:
            continue
        def valor_col(col):
            hijos = col.get("children", [])
            return hijos[0].get("name", "").strip() if hijos else col.get("name", "").strip()

        filas.append({
            "codigo_dane": valor_col(cols[0]),
            "tasa":        valor_col(cols[1]),
            "departamento": valor_col(cols[2]),
        })
    return filas


def limpiar_tasa(valor: str) -> float:
    """Convierte '22,783.70' → 22783.70"""
    try:
        return float(valor.replace(",", ""))
    except ValueError:
        return None


if __name__ == "__main__":
    filas_inc = extraer_filas("tasa_incidencia_departamento.json")
    filas_mor = extraer_filas("tasa_mortalidad_departamento.json")

    df_inc = pd.DataFrame(filas_inc).rename(columns={"tasa": "tasa_incidencia"})
    df_mor = pd.DataFrame(filas_mor).rename(columns={"tasa": "tasa_mortalidad"})

    df = pd.merge(df_inc, df_mor, on=["codigo_dane", "departamento"], how="outer")

    df["tasa_incidencia"] = df["tasa_incidencia"].apply(limpiar_tasa)
    df["tasa_mortalidad"] = df["tasa_mortalidad"].apply(limpiar_tasa)
    df["codigo_dane"]     = df["codigo_dane"].str.zfill(2)

    df = df[["codigo_dane", "departamento", "tasa_incidencia", "tasa_mortalidad"]]
    df = df.sort_values("departamento").reset_index(drop=True)

    script_dir = Path(__file__).parent
    ruta_salida = script_dir.parent / "data" / "tasas_covid_departamento.csv"
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(ruta_salida, index=False)
    print(f"✅ {len(df)} departamentos guardados en {ruta_salida.relative_to(script_dir.parent)}")
