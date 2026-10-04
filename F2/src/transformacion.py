# transformacion.py
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer

def generar_nuevas_variables(df):

    df = df.copy()
    
    # Asegurar que la variable objetivo es binaria 
    if 'Fallecidos' in df.columns:
        df['Es_Fatal'] = np.where(df['Fallecidos'] > 0, 1, 0)
        
    # Extraer la hora limpia 
    if 'Hora' in df.columns:
        df['Hora_limpia'] = pd.to_datetime(df['Hora']).dt.hour
        
    return df

def preprocesar_modelo(df, target_col='Es_Fatal', test_size=0.2, random_state=42):

    # 1. Separar características y variable objetivo
    X = df.drop(columns=[target_col, 'Fallecidos', 'IdAccident', 'Fecha', 'Hora', 'Mes', 'REGION', 'PROVINCIA', 'COMUNA', 'Direccion'], errors='ignore')
    y = df[target_col]
    
    # 2. División de datos 
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    
    # 3. Identificar tipos de columnas para el transformer

    columnas_numericas = ['Hora_limpia', 'Lat', 'Lon']
    columnas_categoricas = ['Dia_semana', 'Tipo_direc', 'REGION_str'] 
    

    columnas_numericas = [col for col in columnas_numericas if col in X_train.columns]
    columnas_categoricas = [col for col in columnas_categoricas if col in X_train.columns]

    # 4. Crear el pipeline de transformación
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), columnas_numericas),
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), columnas_categoricas)
        ],
        remainder='passthrough'
    )
    
    # 5. Ajustar y transformar datos de entrenamiento
    X_train_transformado = preprocessor.fit_transform(X_train)
    X_test_transformado = preprocessor.transform(X_test)
    
    # Obtener los nombres de las columnas resultantes
    nombres_columnas = preprocessor.get_feature_names_out()
    
    return X_train_transformado, X_test_transformado, y_train, y_test, nombres_columnas, preprocessor