import pandas as pd

def eliminar_columnas_productos_tpg(csv_path):
    df = pd.read_csv(csv_path)
    df = df.drop(columns=['precio_bulto_sin_iva', 'precio_unitario_sin_iva'], errors='ignore')
    df.to_csv(csv_path, index=False)

eliminar_columnas_productos_tpg('/home/santiago/TPG/backend/productos_tpg_CORREGIDO.csv')