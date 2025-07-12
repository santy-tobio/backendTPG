import pandas as pd
import PyPDF2
import re
import os
from typing import List, Dict

def extract_products_from_pdf(pdf_path: str) -> List[Dict]:
    """
    Extrae productos del PDF de TPG y los convierte a formato para Google Sheets
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
        
        # Detectar categorías (líneas en mayúsculas sin números)
        if (line.isupper() and 
            3 < len(line) < 30 and 
            not re.search(r'\d', line) and
            line not in ['LISTA DE PRECIOS POR RUBRO', 'TODO PARA LA GASTRONOMIA S.A.',
                        'EL PRECIO UNITARIO ES POR BULTO CERRADO']):
            current_category = line
            print(f"📂 Categoría encontrada: {current_category}")
            continue
        
        # Buscar líneas de productos con el patrón: CODIGO DESCRIPCION PRECIO1 PRECIO2 PRECIO3 PRECIO4
        # Patrón más flexible para capturar productos
        product_patterns = [
            # Patrón principal: codigo descripcion precio1 precio2 precio3 precio4
            r'^(\d{1,5})\s+(.+?)\s+(\d+[\.,]?\d*)\s+(\d+[\.,]?\d*)\s+(\d+[\.,]?\d*)\s+(\d+[\.,]?\d*)$',
            # Patrón alternativo para casos especiales
            r'^(\d{1,5})\s+(.+?)\s+(\d+[\.,]?\d*)\s+(\d+[\.,]?\d*)\s+(\d+[\.,]?\d*)\s+(\d+[\.,]?\d*)'
        ]
        
        for pattern in product_patterns:
            match = re.search(pattern, line)
            if match:
                codigo = match.group(1)
                descripcion_raw = match.group(2)
                
                # Limpiar descripción
                descripcion = re.sub(r'\*\*|\*|ªª|//|\([^)]*\)', '', descripcion_raw)
                descripcion = re.sub(r'\s+', ' ', descripcion).strip()
                
                # Parsear precios (CORREGIDO según columnas del PDF)
                def parse_price(price_str):
                    try:
                        return float(price_str.replace(',', '.').replace(' ', ''))
                    except:
                        return 0.0
                
                # MAPEO CORRECTO DE COLUMNAS:
                precio_unit_sin_iva = parse_price(match.group(3))    # Col 1: Precio por UNIDAD SIN IVA
                precio_bulto_sin_iva = parse_price(match.group(4))   # Col 2: Precio por BULTO SIN IVA  
                precio_unit_con_iva = parse_price(match.group(5))    # Col 3: Precio por UNIDAD CON IVA
                precio_caja_con_iva = parse_price(match.group(6))    # Col 4: Precio por CAJA CON IVA
                
                # Detectar stock crítico
                stock_critico = bool(re.search(r'\*|ªª', descripcion_raw))
                
                product = {
                    'codigo': codigo,
                    'descripcion': descripcion,
                    'categoria': current_category,
                    'precio_unitario': precio_unit_con_iva,           # Col 3: Unidad con IVA (principal)
                    'precio_bulto': precio_caja_con_iva,              # Col 4: Caja con IVA (mayorista)
                    'precio_unitario_sin_iva': precio_unit_sin_iva,   # Col 1: Unidad sin IVA
                    'precio_bulto_sin_iva': precio_bulto_sin_iva,     # Col 2: Bulto sin IVA
                    'imagen_url': f"{codigo}.jpg",
                    'activo': 'TRUE',
                    'stock_critico': 'TRUE' if stock_critico else 'FALSE'
                }
                
                products.append(product)
                break  # Salir del bucle de patrones si encontró coincidencia
    
    print(f"✅ Productos extraídos: {len(products)}")
    return products

def save_products_excel(products: List[Dict], filename: str = "productos_tpg.xlsx"):
    """Guarda productos en Excel con formato mejorado"""
    if not products:
        print("❌ No hay productos para guardar")
        return
    
    # Crear DataFrame
    df = pd.DataFrame(products)
    
    # Reordenar columnas según estructura de Google Sheets
    column_order = [
        'codigo', 'descripcion', 'categoria', 
        'precio_unitario', 'precio_bulto',
        'precio_unitario_sin_iva', 'precio_bulto_sin_iva',
        'imagen_url', 'activo', 'stock_critico'
    ]
    
    df = df[column_order]
    
    # Guardar en Excel con formato
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Productos', index=False)
        
        # Obtener workbook y worksheet para formatear
        workbook = writer.book
        worksheet = writer.sheets['Productos']
        
        # Ajustar ancho de columnas
        for idx, col in enumerate(df.columns):
            max_length = max(
                df[col].astype(str).map(len).max(),
                len(col)
            ) + 2
            worksheet.column_dimensions[chr(65 + idx)].width = min(max_length, 50)
    
    print(f"✅ Archivo Excel guardado: {filename}")

def save_products_csv(products: List[Dict], filename: str = "productos_tpg.csv"):
    """Guarda productos en CSV"""
    if not products:
        print("❌ No hay productos para guardar")
        return
    
    df = pd.DataFrame(products)
    
    # Reordenar columnas
    column_order = [
        'codigo', 'descripcion', 'categoria', 
        'precio_unitario', 'precio_bulto',
        'precio_unitario_sin_iva', 'precio_bulto_sin_iva',
        'imagen_url', 'activo', 'stock_critico'
    ]
    
    df = df[column_order]
    df.to_csv(filename, index=False, encoding='utf-8')
    print(f"✅ Archivo CSV guardado: {filename}")

def show_summary(products: List[Dict]):
    """Muestra resumen de productos extraídos"""
    if not products:
        return
    
    df = pd.DataFrame(products)
    
    print(f"\n📊 RESUMEN DE EXTRACCIÓN")
    print(f"=" * 50)
    print(f"Total productos: {len(products)}")
    
    # Productos por categoría
    print(f"\n📋 Productos por categoría:")
    category_counts = df['categoria'].value_counts()
    for categoria, count in category_counts.head(15).items():
        print(f"  {categoria:20} {count:3} productos")
    
    if len(category_counts) > 15:
        print(f"  ... y {len(category_counts) - 15} categorías más")
    
    # Productos con stock crítico
    stock_critico_count = len(df[df['stock_critico'] == 'TRUE'])
    print(f"\n⚠️  Productos con stock crítico: {stock_critico_count}")
    
    # Rangos de precios (CORREGIDO)
    print(f"\n💰 Rangos de precios (con IVA):")
    print(f"  Precio unitario: ${df['precio_unitario'].min():.2f} - ${df['precio_unitario'].max():.2f}")
    print(f"  Precio caja: ${df['precio_bulto'].min():.2f} - ${df['precio_bulto'].max():.2f}")
    
    # Ejemplos
    print(f"\n📋 Primeros 5 productos (con precios corregidos):")
    for i, product in enumerate(products[:5]):
        print(f"  {i+1:2}. [{product['codigo']:4}] {product['descripcion'][:40]}...")
        print(f"      Categoría: {product['categoria']:15}")
        print(f"      Unidad c/IVA: ${product['precio_unitario']} | Caja c/IVA: ${product['precio_bulto']}")

def main():
    """Función principal"""
    # Configuración
    PDF_FILE = "listaDePrecios26-4-2025.pdf"
    
    print("🏪 TPG - Extractor de Productos (PRECIOS CORREGIDOS)")
    print("=" * 60)
    
    # Verificar archivo PDF
    if not os.path.exists(PDF_FILE):
        print(f"❌ No se encontró el archivo PDF: {PDF_FILE}")
        print("💡 Asegúrate de que el archivo esté en el directorio actual")
        print("💡 Si tiene otro nombre, cambia la variable PDF_FILE en el script")
        return
    
    # Extraer productos
    products = extract_products_from_pdf(PDF_FILE)
    
    if not products:
        print("❌ No se pudieron extraer productos del PDF")
        print("💡 Verifica que el PDF no esté dañado y tenga el formato esperado")
        return
    
    # Guardar archivos
    save_products_excel(products, "productos_tpg_CORREGIDO.xlsx")
    save_products_csv(products, "productos_tpg_CORREGIDO.csv")
    
    # Mostrar resumen
    show_summary(products)
    
    print(f"\n🎉 ¡Proceso completado con PRECIOS CORREGIDOS!")
    print(f"📁 Archivos generados:")
    print(f"   • productos_tpg_CORREGIDO.xlsx (para subir a Google Sheets)")
    print(f"   • productos_tpg_CORREGIDO.csv (formato CSV)")
    print(f"\n✅ MAPEO DE PRECIOS CORREGIDO:")
    print(f"   • precio_unitario → Col 3 PDF (Unidad CON IVA)")
    print(f"   • precio_bulto → Col 4 PDF (Caja CON IVA)")
    print(f"   • precio_unitario_sin_iva → Col 1 PDF (Unidad SIN IVA)")
    print(f"   • precio_bulto_sin_iva → Col 2 PDF (Bulto SIN IVA)")

if __name__ == "__main__":
    main()