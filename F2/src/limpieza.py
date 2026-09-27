import pandas as pd

def limpiar_datos(df_raw):
    df = df_raw.copy().drop_duplicates()

    if 'Lat' in df.columns and 'Lon' in df.columns:
        df = df.dropna(subset=['Lat', 'Lon'])

    columnas_texto = ['Ruta', 'Calle_Uno', 'Calle_Dos', 'Intersecci', 'Condición', 'Ubicación']
    for col in columnas_texto:
        if col in df.columns:
            df[col] = df[col].fillna('Desconocido').astype(str).str.strip()
            df[col] = df[col].replace('', 'Desconocido')

    if 'Fecha' in df.columns:
        df['Fecha'] = pd.to_datetime(df['Fecha']).dt.date

    cols_eliminar = ['XYFID', 'CUT_REG', 'CUT_PROV', 'CUT_COM']
    return df.drop(columns=[c for c in cols_eliminar if c in df.columns], errors='ignore')