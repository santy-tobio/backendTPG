import pandas as pd
import PyPDF2
import re
import os
from typing import List, Dict

def extract_products_from_pdf(pdf_path: str) -> List[Dict]:
    """
    Extrae productos del PDF de TPG con enfoque simple: código + descripción + 4 precios
    """
    print("🚀 Iniciando extracción del PDF...")
    
    # Leer PDF
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        print(f"❌ Error al leer PDF: {e}")
        return []
    
    products = []
    current_category = ""
    lines = text.split('\n')
    
    print("🔍 Analizando líneas del PDF...")
    
    for line in lines:
        line = line.strip()
        
        # Detectar categorías
        if (line.isupper() and 
            3 < len(line) < 30 and 
            not re.search(r'\d', line) and
            line not in ['LISTA DE PRECIOS POR RUBRO', 'TODO PARA LA GASTRONOMIA S.A.',
                        'EL PRECIO UNITARIO ES POR BULTO CERRADO', 'CODIGO', 'DESCRIPCION']):
            current_category = line
            print(f"📂 Categoría encontrada: {current_category}")
            continue
        
        # Buscar líneas que empiecen con código (1-5 dígitos)
        if not re.match(r'^\d{1,5}\s', line):
            continue
        
        # Dividir la línea en tokens
        tokens = line.split()
        
        # Necesitamos al menos: código + descripción + 4 precios = 6 tokens mínimo
        if len(tokens) < 6:
            continue
        
        # El primer token es el código
        codigo = tokens[0]
        
        # Los últimos 4 tokens deberían ser precios (formato: números con hasta 2 decimales)
        precios = []
        precio_tokens = []
        
        # Buscar los últimos 4 tokens que sean números válidos
        for i in range(len(tokens) - 1, -1, -1):
            token = tokens[i]
            # Verificar si es un número válido (entero o decimal)
            if re.match(r'^\d{1,6}(?:\.\d{1,2})?$', token):
                precios.insert(0, float(token))
                precio_tokens.insert(0, i)
                if len(precios) == 4:
                    break
        
        # Si no encontramos exactamente 4 precios, saltar esta línea
        if len(precios) != 4:
            continue
        
        # La descripción está entre el código y los precios
        descripcion_tokens = tokens[1:precio_tokens[0]]
        descripcion_raw = ' '.join(descripcion_tokens)
        
        # Limpiar descripción
        descripcion = re.sub(r'\*\*|\*|ªª|//|\([^)]*\)', '', descripcion_raw)
        descripcion = re.sub(r'\s+', ' ', descripcion).strip()
        
        # Debug: primera línea procesada
        if len(products) == 0:
            print(f"🔍 Primera línea procesada:")
            print(f"   Línea: {line}")
            print(f"   Código: {codigo}")
            print(f"   Descripción: '{descripcion}'")
            print(f"   Precios: {precios}")
        
        # Mapeo de precios:
        # precios[0] = Col 1: Unitario SIN IVA
        # precios[1] = Col 2: Caja SIN IVA  
        # precios[2] = Col 3: Unitario CON IVA ⭐
        # precios[3] = Col 4: Caja CON IVA ⭐
        precio_unitario = precios[2]  # Col 3: Unitario CON IVA
        precio_bulto = precios[3]     # Col 4: Caja CON IVA
        
        # Detectar stock crítico
        stock_critico = bool(re.search(r'\*|ªª', descripcion_raw))
        
        # Crear producto
        product = {
            'codigo': codigo,
            'descripcion': descripcion,
            'categoria': current_category,
            'precio_unitario': precio_unitario,
            'precio_bulto': precio_bulto,
            'imagen_url': f"{codigo}.jpg",
            'activo': 'TRUE',
            'stock_critico': 'TRUE' if stock_critico else 'FALSE'
        }
        
        products.append(product)
    
    print(f"✅ Productos extraídos: {len(products)}")
    return products

def save_products_csv(products: List[Dict], filename: str = "productos_tpg_limpio.csv"):
    """Guarda productos en CSV"""
    if not products:
        print("❌ No hay productos para guardar")
        return
    
    df = pd.DataFrame(products)
    
    # Orden de columnas
    column_order = [
        'codigo', 'descripcion', 'categoria', 
        'precio_unitario', 'precio_bulto',
        'imagen_url', 'activo', 'stock_critico'
    ]
    
    df = df[column_order]
    df.to_csv(filename, index=False, encoding='utf-8')
    print(f"✅ Archivo CSV guardado: {filename}")

def save_products_excel(products: List[Dict], filename: str = "productos_tpg_limpio.xlsx"):
    """Guarda productos en Excel"""
    if not products:
        print("❌ No hay productos para guardar")
        return
    
    df = pd.DataFrame(products)
    
    column_order = [
        'codigo', 'descripcion', 'categoria', 
        'precio_unitario', 'precio_bulto',
        'imagen_url', 'activo', 'stock_critico'
    ]
    
    df = df[column_order]
    
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Productos', index=False)
        
        workbook = writer.book
        worksheet = writer.sheets['Productos']
        
        # Ajustar columnas
        for idx, col in enumerate(df.columns):
            max_length = max(df[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.column_dimensions[chr(65 + idx)].width = min(max_length, 50)
    
    print(f"✅ Archivo Excel guardado: {filename}")

def show_summary(products: List[Dict]):
    """Muestra resumen"""
    if not products:
        return
    
    df = pd.DataFrame(products)
    
    print(f"\n📊 RESUMEN")
    print(f"=" * 40)
    print(f"Total productos: {len(products)}")
    
    # Por categoría
    print(f"\n📋 Por categoría:")
    category_counts = df['categoria'].value_counts()
    for categoria, count in category_counts.head(10).items():
        print(f"  {categoria:15} {count:3} productos")
    
    # Stock crítico
    stock_critico_count = len(df[df['stock_critico'] == 'TRUE'])
    print(f"\n⚠️  Stock crítico: {stock_critico_count}")
    
    # Precios
    print(f"\n💰 Precios:")
    print(f"  Unitario: ${df['precio_unitario'].min():.2f} - ${df['precio_unitario'].max():.2f}")
    print(f"  Bulto: ${df['precio_bulto'].min():.2f} - ${df['precio_bulto'].max():.2f}")
    
    # Ejemplos
    print(f"\n📋 Ejemplos:")
    for i, product in enumerate(products[:3]):
        print(f"  {i+1}. [{product['codigo']}] {product['descripcion']}")
        print(f"     💲 ${product['precio_unitario']} | ${product['precio_bulto']}")

def main():
    """Función principal"""
    PDF_FILE = "listaDePrecios26-4-2025.pdf"
    
    print("🏪 TPG - Extractor LIMPIO")
    print("=" * 40)
    
    if not os.path.exists(PDF_FILE):
        print(f"❌ No se encontró: {PDF_FILE}")
        return
    
    # Extraer
    products = extract_products_from_pdf(PDF_FILE)
    
    if not products:
        print("❌ No se extrajeron productos")
        return
    
    # Guardar
    save_products_csv(products)
    save_products_excel(products)
    
    # Resumen
    show_summary(products)
    
    print(f"\n🎉 ¡Listo!")
    print(f"📁 Archivos: productos_tpg_limpio.csv/xlsx")

if __name__ == "__main__":
    main()