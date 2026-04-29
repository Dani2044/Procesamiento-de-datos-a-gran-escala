"""
Script: extraer_tasas_municipio_powerbi.py
Fuente: Power BI embebido en INS Colombia
Salida: CSV con codigo_dane, municipio, tasa_incidencia, tasa_mortalidad

Uso:
    pip install requests pandas
    python extraer_tasas_municipio_powerbi.py

Nota: el X-PowerBI-ResourceKey expira con la sesión. Si recibes 401,
actualiza la constante desde DevTools → Network → cURL.
"""

import json
import requests
import pandas as pd
from pathlib import Path

# ── CONFIGURACIÓN ─────────────────────────────────────────────────────────────

URL = "https://wabi-south-central-us-api.analysis.windows.net/public/reports/querydata"

HEADERS = {
    "User-Agent":            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:149.0) Gecko/20100101 Firefox/149.0",
    "Accept":                "application/json, text/plain, */*",
    "Accept-Language":       "en-US,en;q=0.9",
    "X-PowerBI-ResourceKey": "5aab936c-a15a-4e36-9855-8b5e2cb51cef",  # ← actualizar si expira
    "Content-Type":          "application/json;charset=UTF-8",
    "Origin":                "https://app.powerbi.com",
    "Referer":               "https://app.powerbi.com/",
}

DATASET_ID     = "755c5696-b95d-497c-94e4-f0b59839f4b9"
REPORT_ID      = "c1868109-0049-4bd7-b4ab-727e932eda15"
MODEL_ID       = 2827883
ARCHIVO_SALIDA = "tasas_covid_municipio.csv"
DEBUG          = False   # guarda respuestas crudas para diagnóstico


# ── PAYLOADS ──────────────────────────────────────────────────────────────────

def _base_payload(visual_id: str, select: list) -> dict:
    return {
        "version": "1.0.0",
        "queries": [{
            "Query": {"Commands": [{"SemanticQueryDataShapeCommand": {
                "Query": {
                    "Version": 2,
                    "From": [
                        {"Name": "t", "Entity": "T_municipios",   "Type": 0},
                        {"Name": "d", "Entity": "DANE_Municipios", "Type": 0},
                    ],
                    "Select": select,
                    "GroupBy": [{"SourceRef": {"Source": "t"}, "Name": "T_municipios"}],
                },
                "Binding": {
                    "Primary": {"Groupings": [{"Projections": [0, 1, 2], "GroupBy": [0]}]},
                    "DataReduction": {"Primary": {"Top": {"Count": 1200}}},
                    "Version": 1,
                },
                "ExecutionMetricsKind": 1,
            }}]},
            "QueryId": "",
            "ApplicationContext": {
                "DatasetId": DATASET_ID,
                "Sources": [{"ReportId": REPORT_ID, "VisualId": visual_id}],
            },
        }],
        "cancelQueries": [],
        "modelId": MODEL_ID,
    }


def payload_incidencia() -> dict:
    # Select: [codigo, nombre, tasa_incidencia]
    return _base_payload("1e822d562c67695e6010", [
        {"Column": {"Expression": {"SourceRef": {"Source": "t"}}, "Property": "CodMunicipioC"},
         "Name": "T_municipios.CodMunicipioC"},
        {"Column": {"Expression": {"SourceRef": {"Source": "d"}}, "Property": "NombreMunicipio"},
         "Name": "Min(DANE_Municipios.NombreMunicipio)"},
        {"Column": {"Expression": {"SourceRef": {"Source": "t"}}, "Property": "TIncidenciaMunicipio"},
         "Name": "Sum(T_municipios.TIncidenciaMunicipio)"},
    ])


def payload_mortalidad() -> dict:
    # Select: [tasa_mortalidad, codigo, nombre]
    return _base_payload("ccba5a08f5cce1c9d256", [
        {"Column": {"Expression": {"SourceRef": {"Source": "t"}}, "Property": "TMortalidadMunicipio"},
         "Name": "Sum(T_municipios.TMortalidadMunicipio)"},
        {"Column": {"Expression": {"SourceRef": {"Source": "t"}}, "Property": "CodMunicipioC"},
         "Name": "T_municipios.CodMunicipioC"},
        {"Column": {"Expression": {"SourceRef": {"Source": "d"}}, "Property": "NombreMunicipio"},
         "Name": "Min(DANE_Municipios.NombreMunicipio)"},
    ])


# ── PARSER ────────────────────────────────────────────────────────────────────

def parsear_dsr(response_json: dict,
                col_codigo: int,
                col_nombre: int,
                col_tasa: int) -> list[dict]:
    """
    Parsea DM0 con delta-encoding (bitmask R) y nulos (bitmask Ø).

    La API mezcla dos formatos en el mismo DM0:
      - Items 0..N:  C contiene índices enteros a ValueDicts D0/D1
      - Items N+1..: C contiene los valores directamente como strings

    Para cada campo se resuelve así:
      - Si es int  → buscar en el ValueDict correspondiente (D0 para codigo, D1 para nombre)
      - Si es str  → usar directamente
      - Si es float/int para la tasa → convertir a float

    Los items con código DANE inválido (no 5 dígitos numéricos) se descartan:
    corresponden a Áreas No Municipalizadas (ANM) u otras entidades.
    """
    ds  = response_json["results"][0]["result"]["data"]["dsr"]["DS"][0]
    dm0 = ds["PH"][0]["DM0"]
    vd  = ds.get("ValueDicts", {})
    D0  = vd.get("D0", [])   # índice → código DANE
    D1  = vd.get("D1", [])   # índice → nombre municipio

    n_cols = 3
    prev   = [None] * n_cols
    filas  = []

    for item in dm0:
        nulos = item.get("Ø", 0)
        c     = item.get("C", [])
        r     = item.get("R", 0)
        curr  = list(prev)

        col_c = 0
        for col_idx in range(n_cols):
            if (nulos >> col_idx) & 1:          # valor nulo explícito
                curr[col_idx] = None
            elif not ((r >> col_idx) & 1):      # no repetido → viene en C
                if col_c < len(c):
                    curr[col_idx] = c[col_c]
                    col_c += 1

        # Resolver código DANE
        raw_cod = curr[col_codigo]
        if isinstance(raw_cod, int) and D0:
            codigo = D0[raw_cod] if raw_cod < len(D0) else None
        else:
            codigo = str(raw_cod) if raw_cod is not None else None

        # Resolver nombre municipio
        raw_nom = curr[col_nombre]
        if isinstance(raw_nom, int) and D1:
            nombre = D1[raw_nom] if raw_nom < len(D1) else None
        else:
            nombre = str(raw_nom) if raw_nom is not None else None

        # Resolver tasa
        raw_tasa = curr[col_tasa]
        try:
            tasa = round(float(raw_tasa), 4) if raw_tasa is not None else None
        except (ValueError, TypeError):
            tasa = None

        # Filtrar solo códigos DANE válidos (5 dígitos numéricos)
        # Los ANM tienen código válido pero nombre con "(ANM)" — se incluyen
        if codigo and len(codigo) == 5 and codigo.isdigit():
            filas.append({
                "codigo_dane": codigo,
                "municipio":   nombre,
                "tasa":        tasa,
            })

        prev = curr

    return filas


# ── LÓGICA PRINCIPAL ──────────────────────────────────────────────────────────

def main():
    session = requests.Session()

    # ── Llamada 1: tasa de incidencia ─────────────────────────────────────────
    print("Consultando tasa de incidencia...")
    r_inc = session.post(URL, headers=HEADERS, json=payload_incidencia())
    r_inc.raise_for_status()
    data_inc = r_inc.json()
    if DEBUG:
        script_dir = Path(__file__).parent
        debug_inc = script_dir / "response_debug_incidencia.json"
        with open(debug_inc, "w", encoding="utf-8") as f:
            json.dump(data_inc, f, ensure_ascii=False, indent=2)

    # incidencia: col_codigo=0, col_nombre=1, col_tasa=2
    filas_inc = parsear_dsr(data_inc, col_codigo=0, col_nombre=1, col_tasa=2)
    print(f"  → {len(filas_inc)} registros")

    # ── Llamada 2: tasa de mortalidad ─────────────────────────────────────────
    print("Consultando tasa de mortalidad...")
    r_mor = session.post(URL, headers=HEADERS, json=payload_mortalidad())
    r_mor.raise_for_status()
    data_mor = r_mor.json()
    if DEBUG:
        script_dir = Path(__file__).parent
        debug_mor = script_dir / "response_debug_mortalidad.json"
        with open(debug_mor, "w", encoding="utf-8") as f:
            json.dump(data_mor, f, ensure_ascii=False, indent=2)

    # mortalidad: col_tasa=0, col_codigo=1, col_nombre=2
    filas_mor = parsear_dsr(data_mor, col_codigo=1, col_nombre=2, col_tasa=0)
    print(f"  → {len(filas_mor)} registros")

    if not filas_inc and not filas_mor:
        print("⚠️  Ambas respuestas vacías. Verifica el ResourceKey.")
        return

    # ── Merge ─────────────────────────────────────────────────────────────────
    df_inc = pd.DataFrame(filas_inc).rename(columns={"tasa": "tasa_incidencia"})
    df_mor = pd.DataFrame(filas_mor)[["codigo_dane", "tasa"]].rename(
        columns={"tasa": "tasa_mortalidad"}
    )

    df = pd.merge(df_inc, df_mor, on="codigo_dane", how="outer")
    df["codigo_dane"] = df["codigo_dane"].astype(str).str.zfill(5)
    df = df[["codigo_dane", "municipio", "tasa_incidencia", "tasa_mortalidad"]]
    df = df.sort_values("municipio").reset_index(drop=True)

    script_dir = Path(__file__).parent
    ruta_salida = script_dir.parent / "data" / ARCHIVO_SALIDA
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(ruta_salida, index=False, encoding='utf-8')
    print(f"\n✅ {len(df)} municipios guardados en 'data/{ARCHIVO_SALIDA}'")


if __name__ == "__main__":
    main()
