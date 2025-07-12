import pandas as pd
import re

def clean_descriptions(csv_file: str, output_file: str = None):
    """
    Limpia las descripciones del CSV quitando números al final
    """
    print(f"🧹 Limpiando descripciones de: {csv_file}")
    
    # Leer CSV
    try:
        df = pd.read_csv(csv_file)
    except Exception as e:
        print(f"❌ Error al leer CSV: {e}")
        return
    
    # Función para limpiar descripción
    def clean_description(desc):
        if pd.isna(desc):
            return desc
        
        desc_str = str(desc)
        
        # Quitar números decimales al final (ej: 1339.0, 1966.00, 3227.4)
        desc_str = re.sub(r'\s+\d+\.\d+\s*$', '', desc_str)
        
        # Quitar números enteros grandes al final (ej: 3117)
        desc_str = re.sub(r'\s+\d{4,}\s*$', '', desc_str)
        
        # Quitar números entre paréntesis al final (ej: (2283)
        desc_str = re.sub(r'\s+\(\d+\)\s*$', '', desc_str)
        
        # Limpiar espacios extra
        desc_str = re.sub(r'\s+', ' ', desc_str).strip()
        
        return desc_str
    
    # Mostrar algunos ejemplos antes
    print(f"\n📋 Ejemplos ANTES de limpiar:")
    for i in range(min(5, len(df))):
        print(f"  {df.iloc[i]['codigo']}: {df.iloc[i]['descripcion']}")
    
    # Aplicar limpieza
    df['descripcion'] = df['descripcion'].apply(clean_description)
    
    # Mostrar ejemplos después
    print(f"\n✨ Ejemplos DESPUÉS de limpiar:")
    for i in range(min(5, len(df))):
        print(f"  {df.iloc[i]['codigo']}: {df.iloc[i]['descripcion']}")
    
    # Guardar archivo limpio
    if output_file is None:
        output_file = csv_file.replace('.csv', '_limpio.csv')
    
    df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"\n✅ Archivo limpio guardado: {output_file}")
    
    # Estadísticas
    print(f"\n📊 Resumen:")
    print(f"  Total productos: {len(df)}")
    print(f"  Categorías: {df['categoria'].nunique()}")
    print(f"  Stock crítico: {len(df[df['stock_critico'] == 'TRUE'])}")

def main():
    """Función principal"""
    CSV_FILE = '/home/santiago/TPG/backend/productos_tpg_limpio.csv'  # Cambiar por tu archivo
    
    print("🧹 TPG - Limpiador de Descripciones")
    print("=" * 40)
    
    # Verificar archivo
    import os
    if not os.path.exists(CSV_FILE):
        print(f"❌ No se encontró: {CSV_FILE}")
        print("💡 Cambia CSV_FILE por el nombre de tu archivo")
        return
    
    # Limpiar
    clean_descriptions(CSV_FILE)
    
    print(f"\n🎉 ¡Listo! Descripciones limpiadas")

if __name__ == "__main__":
    main()