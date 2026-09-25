import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="whitegrid")
def reporte_calidad_datos(df):
print(f"Duplicados: {df.duplicated().sum()}")
print("Nulos:\n", df.isnull().sum()[df.isnull().sum() > 0])
def graficar_contexto_temporal(df):
if 'Dia_semana' in df.columns:
plt.figure(figsize=(8, 5))
sns.countplot(data=df, x='Dia_semana', palette='magma')
plt.title('Siniestros por Día')
plt.xticks(rotation=45)
plt.show()