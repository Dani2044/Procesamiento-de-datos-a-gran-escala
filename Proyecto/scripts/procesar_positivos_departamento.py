"""
Script: procesar_positivos_departamento.py
Fuente: JSON de accesibilidad exportado desde INS Colombia
        (clic derecho > Print to JSON en el panel Accessibility de DevTools)
Salida: CSV con departamento, positivos del día y positivos totales
"""

import json
import re
from pathlib import Path
import pandas as pd


def extraer_positivos_departamento(ruta_json: str) -> list[dict]:
    """
    Recorre recursivamente el árbol de accesibilidad y extrae
    todos los nodos con role='button' que tengan el patrón:
    '{departamento}. Casos positivos de hoy: {n}. {total} Casos totales'
    """
    with open(ruta_json, 'r', encoding='utf-8') as f:
        data = json.load(f)

    registros = []
    patron = re.compile(
        r'^(.+?)\.\s+Casos positivos de hoy:\s*(\d+)\.\s*(\d+)\s+Casos totales$'
    )

    def recorrer(nodo):
        nombre = nodo.get('name', '')
        rol    = nodo.get('role', '')

        if rol == 'button' and nombre:
            match = patron.match(nombre)
            if match:
                registros.append({
                    'departamento':      match.group(1).strip(),
                    'positivos_hoy':     int(match.group(2)),
                    'positivos_totales': int(match.group(3)),
                })

        for hijo in nodo.get('children', []):
            recorrer(hijo)

    recorrer(data)
    return registros


if __name__ == "__main__":
    # Definir rutas de forma multiplataforma
    script_dir = Path(__file__).parent
    ruta_json = script_dir / "positivos_covid_departamento_raw.json"
    ruta_salida = script_dir.parent / "data" / "positivos_covid_departamento.csv"
    
    registros = extraer_positivos_departamento(str(ruta_json))

    df = pd.DataFrame(registros).sort_values('departamento').reset_index(drop=True)

    df.to_csv(ruta_salida, index=False)
    print(f"✅ {len(df)} departamentos guardados en {ruta_salida.relative_to(script_dir.parent)}")

