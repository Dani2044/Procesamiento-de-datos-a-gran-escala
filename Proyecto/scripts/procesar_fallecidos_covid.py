"""
Script: procesar_fallecidos_covid.py
Fuente: JSON de accesibilidad exportado desde INS Colombia
        (clic derecho > Print to JSON en el panel Accessibility de DevTools)
Salida: CSV con fecha y fallecidos por día
"""

import json
import re
from pathlib import Path
import pandas as pd


def extraer_fallecidos(ruta_json: str) -> list[dict]:
    """
    Recorre recursivamente el árbol de accesibilidad y extrae
    todos los nodos con role='image' que tengan el patrón:
    '{acumulado} Fallecidos: {valor_dia}: {dd/mm/yyyy}'
    """
    with open(ruta_json, 'r', encoding='utf-8') as f:
        data = json.load(f)

    registros = []
    patron = re.compile(r'(\d+)\s+Fallecidos:\s*(\d+):\s*(\d{2}/\d{2}/\d{4})')

    def recorrer(nodo):
        nombre = nodo.get('name', '')
        rol    = nodo.get('role', '')

        if rol == 'image' and nombre:
            match = patron.match(nombre)
            if match:
                registros.append({
                    'fecha':           match.group(3),
                    'cant_fallecidos':  int(match.group(2))
                })

        for hijo in nodo.get('children', []):
            recorrer(hijo)

    recorrer(data)
    return registros


if __name__ == "__main__":
    # Definir rutas de forma multiplataforma
    script_dir = Path(__file__).parent
    ruta_json = script_dir / "muertos_covid_fecha_raw.json"
    ruta_salida = script_dir.parent / "data" / "fallecidos_covid_colombia.csv"
    
    registros = extraer_fallecidos(str(ruta_json))

    df = pd.DataFrame(registros)
    df['fecha'] = pd.to_datetime(df['fecha'], format='%d/%m/%Y')
    df = df.sort_values('fecha').reset_index(drop=True)

    df.to_csv(ruta_salida, index=False)
    print(f"✅ {len(df)} registros guardados en {ruta_salida.relative_to(script_dir.parent)}")
