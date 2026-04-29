"""
Script: extraer_casos_municipio_powerbi.py
Fuente: Power BI embebido en INS Colombia
Salida: CSV con municipio, fecha y casos por día para todos los municipios

Uso:
    pip install requests pandas
    python extraer_casos_municipio_powerbi.py

Nota: el X-PowerBI-ResourceKey expira con la sesión. Si recibes 401,
vuelve a copiar el cURL desde DevTools y actualiza la constante.
"""

import json
import time
from pathlib import Path
import requests
import pandas as pd
from datetime import datetime, timezone

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

DATASET_ID           = "755c5696-b95d-497c-94e4-f0b59839f4b9"
REPORT_ID            = "c1868109-0049-4bd7-b4ab-727e932eda15"
MODEL_ID             = 2827883
PAUSA_ENTRE_REQUESTS = 0.4
ARCHIVO_SALIDA       = "casos_covid_por_municipio.csv"


# ── PAYLOADS ──────────────────────────────────────────────────────────────────

def payload_lista_municipios() -> dict:
    return {
        "version": "1.0.0",
        "queries": [{
            "Query": {"Commands": [{"SemanticQueryDataShapeCommand": {
                "Query": {
                    "Version": 2,
                    "From": [{"Name": "c", "Entity": "Casos", "Type": 0}],
                    "Select": [{
                        "Column": {
                            "Expression": {"SourceRef": {"Source": "c"}},
                            "Property": "ciudad"
                        },
                        "Name": "Casos.ciudad"
                    }],
                    "OrderBy": [{"Direction": 1, "Expression": {
                        "Column": {
                            "Expression": {"SourceRef": {"Source": "c"}},
                            "Property": "ciudad"
                        }
                    }}]
                },
                "Binding": {
                    "Primary": {"Groupings": [{"Projections": [0]}]},
                    "DataReduction": {"DataVolume": 4, "Primary": {"Top": {}}},
                    "Version": 1
                },
                "ExecutionMetricsKind": 1
            }}]},
            "QueryId": "",
            "ApplicationContext": {
                "DatasetId": DATASET_ID,
                "Sources": [{"ReportId": REPORT_ID, "VisualId": "69b020b9ebb8be336d33"}]
            }
        }],
        "cancelQueries": [],
        "modelId": MODEL_ID
    }


def payload_casos_por_fecha(municipio: str) -> dict:
    return {
        "version": "1.0.0",
        "queries": [{
            "Query": {"Commands": [{"SemanticQueryDataShapeCommand": {
                "Query": {
                    "Version": 2,
                    "From": [{"Name": "s", "Entity": "Casos", "Type": 0}],
                    "Select": [
                        {
                            "Column": {
                                "Expression": {"SourceRef": {"Source": "s"}},
                                "Property": "fecha"
                            },
                            "Name": "Casos.fecha"
                        },
                        {
                            "Aggregation": {
                                "Expression": {"Column": {
                                    "Expression": {"SourceRef": {"Source": "s"}},
                                    "Property": "Casos"
                                }},
                                "Function": 0
                            },
                            "Name": "Sum(Casos.Casos)"
                        }
                    ],
                    "Where": [{
                        "Condition": {"In": {
                            "Expressions": [{"Column": {
                                "Expression": {"SourceRef": {"Source": "s"}},
                                "Property": "ciudad"
                            }}],
                            "Values": [[{"Literal": {"Value": f"'{municipio}'"}}]]
                        }}
                    }]
                },
                "Binding": {
                    "Primary": {"Groupings": [{"Projections": [0, 1]}]},
                    "DataReduction": {"DataVolume": 4, "Primary": {"BinnedLineSample": {}}},
                    "Version": 1
                },
                "ExecutionMetricsKind": 1
            }}]},
            "QueryId": "",
            "ApplicationContext": {
                "DatasetId": DATASET_ID,
                "Sources": [{"ReportId": REPORT_ID, "VisualId": "69b020b9ebb8be336d33"}]
            }
        }],
        "cancelQueries": [],
        "modelId": MODEL_ID
    }


# ── PARSERS ───────────────────────────────────────────────────────────────────

def parsear_municipios(response_json: dict) -> list[str]:
    """Los municipios vienen en campo G0 de cada elemento DM0."""
    try:
        dm0 = response_json["results"][0]["result"]["data"]["dsr"]["DS"][0]["PH"][0]["DM0"]
        return [item["G0"] for item in dm0 if "G0" in item]
    except (KeyError, IndexError) as e:
        print(f"  ⚠️  Error parseando municipios: {e}")
        return []


def parsear_casos(response_json: dict, municipio: str) -> list[dict]:
    """
    Parsea la respuesta de fecha+casos.

    Estructura real de la API:
      - C[0]: timestamp en milisegundos (fecha)
      - C[1]: cantidad de casos (Sum)
      - R: bitmask de delta-encoding
            bit 0 activo → C[0] (fecha) repite el valor anterior
            bit 1 activo → C[1] (casos) repite el valor anterior
    """
    try:
        dm0 = response_json["results"][0]["result"]["data"]["dsr"]["DS"][0]["PH"][0]["DM0"]
    except (KeyError, IndexError):
        return []

    registros = []
    prev = [None, None]   # [timestamp, casos]

    for item in dm0:
        c    = item.get("C", [])
        r    = item.get("R", 0)
        curr = list(prev)

        col_c = 0
        for col_idx in range(2):
            if not ((r >> col_idx) & 1):   # bit NO activo → viene nuevo valor en C
                if col_c < len(c):
                    curr[col_idx] = c[col_c]
                    col_c += 1

        if curr[0] is not None and curr[1] is not None:
            fecha = datetime.fromtimestamp(curr[0] / 1000, tz=timezone.utc).date()
            registros.append({
                "municipio": municipio,
                "fecha":     fecha,
                "casos":     int(curr[1]),
            })

        prev = curr

    return registros


# ── LÓGICA PRINCIPAL ──────────────────────────────────────────────────────────

def obtener_municipios(session: requests.Session) -> list[str]:
    print("Obteniendo lista de municipios...")
    r = session.post(URL, headers=HEADERS, json=payload_lista_municipios())
    r.raise_for_status()
    municipios = parsear_municipios(r.json())
    print(f"  → {len(municipios)} municipios encontrados")
    return municipios


def obtener_casos_municipio(session: requests.Session, municipio: str) -> list[dict]:
    r = session.post(URL, headers=HEADERS, json=payload_casos_por_fecha(municipio))
    r.raise_for_status()
    return parsear_casos(r.json(), municipio)


def main():
    session = requests.Session()
    todos_los_registros = []
    errores = []

    municipios = obtener_municipios(session)

    if not municipios:
        print("❌ No se encontraron municipios. Verifica el ResourceKey.")
        return

    total = len(municipios)
    for i, municipio in enumerate(municipios, 1):
        try:
            registros = obtener_casos_municipio(session, municipio)
            todos_los_registros.extend(registros)
            print(f"[{i:4}/{total}] {municipio:<40} {len(registros)} registros")
        except requests.HTTPError as e:
            print(f"[{i:4}/{total}] ❌ {municipio}: HTTP {e.response.status_code}")
            errores.append({"municipio": municipio, "error": str(e)})
        except Exception as e:
            print(f"[{i:4}/{total}] ❌ {municipio}: {e}")
            errores.append({"municipio": municipio, "error": str(e)})

        time.sleep(PAUSA_ENTRE_REQUESTS)

    if not todos_los_registros:
        print("⚠️  No se obtuvieron registros.")
        return

    script_dir = Path(__file__).parent
    ruta_salida = script_dir.parent / "data" / ARCHIVO_SALIDA
    ruta_errores = script_dir.parent / "data" / "errores_municipios.csv"

    df = pd.DataFrame(todos_los_registros)
    df["fecha"] = pd.to_datetime(df["fecha"])
    df = df.sort_values(["municipio", "fecha"]).reset_index(drop=True)

    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(ruta_salida, index=False, encoding='utf-8')

    print(f"\n✅ {len(df)} registros guardados en '{ruta_salida.relative_to(script_dir.parent)}'")
    print(f"   Municipios procesados : {total - len(errores)}/{total}")

    if errores:
        pd.DataFrame(errores).to_csv(ruta_errores, index=False, encoding='utf-8')
        print(f"⚠️  {len(errores)} errores guardados en '{ruta_errores.relative_to(script_dir.parent)}'")


if __name__ == "__main__":
    main()
