import pandas as pd
import PyPDF2
import re
import csv
import os
from typing import List, Dict, Tuple
import gspread
from oauth2client.service_account import ServiceAccountCredentials

class TPGProductExtractor:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.products = []
        
    def extract_text_from_pdf(self) -> str:
        """Extrae todo el texto del PDF"""
        try:
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"Error al leer PDF: {e}")
            return ""
    
    def clean_description(self, desc: str) -> str:
        """Limpia la descripción del producto"""
        # Remover marcadores especiales
        desc = re.sub(r'\*\*|\*|ªª|//|\(.*?\)', '', desc)
        desc = re.sub(r'\s+', ' ', desc).strip()
        return desc
    
    def parse_price(self, price_str: str) -> float:
        """Convierte string de precio a float"""
        try:
            # Remover espacios y convertir
            price_str = price_str.replace(' ', '').replace(',', '.')
            return float(price_str)
        except:
            return 0.0
    
    def extract_products_from_text(self, text: str) -> List[Dict]:
        """Extrae productos del texto del PDF"""
        products = []
        current_category = ""
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Detectar categorías (líneas que son solo texto en mayúsculas)
            if (line.isupper() and 
                len(line) > 3 and 
                len(line) < 30 and 
                not re.search(r'\d', line) and
                line not in ['LISTA DE PRECIOS POR RUBRO', 'TODO PARA LA GASTRONOMIA S.A.']):
                current_category = line
                continue
            
            # Buscar líneas de productos (empiezan con código numérico)
            product_match = re.match(r'^(\d{1,5})\s+(.+?)\s+(\d+\.?\d*)\s+(\d+\.?\d*)\s+(\d+\.?\d*)\s+(\d+\.?\d*)$', line)
            
            if product_match:
                codigo = product_match.group(1)
                descripcion = self.clean_description(product_match.group(2))
                precio_unitario_sin_iva = self.parse_price(product_match.group(3))
                precio_caja_sin_iva = self.parse_price(product_match.group(4))
                precio_unitario_con_iva = self.parse_price(product_match.group(5))
                precio_caja_con_iva = self.parse_price(product_match.group(6))
                
                # Determinar si tiene stock crítico
                stock_critico = ('*' in product_match.group(2) or 'ªª' in product_match.group(2))
                
                product = {
                    'codigo': codigo,
                    'descripcion': descripcion,
                    'categoria': current_category,
                    'precio_unitario': precio_unitario_con_iva,  # Usar precio con IVA
                    'precio_bulto': precio_caja_con_iva,         # Usar precio con IVA
                    'precio_unitario_sin_iva': precio_unitario_sin_iva,
                    'precio_bulto_sin_iva': precio_caja_sin_iva,
                    'imagen_url': f"{codigo}.jpg",
                    'activo': True,
                    'stock_critico': stock_critico
                }
                products.append(product)
        
        return products
    
    def save_to_csv(self, products: List[Dict], filename: str = "productos_tpg.csv"):
        """Guarda productos en CSV"""
        if not products:
            print("No hay productos para guardar")
            return
        
        # Columnas según estructura requerida en Google Sheets
        columns = [
            'codigo', 'descripcion', 'categoria', 
            'precio_unitario', 'precio_bulto', 
            'precio_unitario_sin_iva', 'precio_bulto_sin_iva',
            'imagen_url', 'activo', 'stock_critico'
        ]
        
        df = pd.DataFrame(products)
        df = df[columns]  # Ordenar columnas
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"✅ Productos guardados en: {filename}")
        print(f"📊 Total productos extraídos: {len(products)}")
        
        # Mostrar resumen por categoría
        category_counts = df['categoria'].value_counts()
        print("\n📋 Productos por categoría:")
        for cat, count in category_counts.head(10).items():
            print(f"  {cat}: {count} productos")
    
    def upload_to_google_sheets(self, products: List[Dict], 
                               credentials_file: str, 
                               sheet_name: str = "TPG Productos"):
        """Sube productos a Google Sheets"""
        try:
            # Configurar credenciales
            scope = ['https://spreadsheets.google.com/feeds',
                    'https://www.googleapis.com/auth/drive']
            
            creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
            client = gspread.authorize(creds)
            
            # Crear o abrir hoja
            try:
                sheet = client.open(sheet_name).sheet1
                sheet.clear()  # Limpiar datos existentes
            except gspread.SpreadsheetNotFound:
                spreadsheet = client.create(sheet_name)
                sheet = spreadsheet.sheet1
                # Compartir con tu email (opcional)
                # spreadsheet.share('tu-email@gmail.com', perm_type='user', role='writer')
            
            # Preparar datos
            headers = [
                'codigo', 'descripcion', 'categoria', 
                'precio_unitario', 'precio_bulto', 
                'precio_unitario_sin_iva', 'precio_bulto_sin_iva',
                'imagen_url', 'activo', 'stock_critico'
            ]
            
            # Convertir productos a lista de listas
            data = [headers]
            for product in products:
                row = [
                    product['codigo'],
                    product['descripcion'],
                    product['categoria'],
                    product['precio_unitario'],
                    product['precio_bulto'],
                    product['precio_unitario_sin_iva'],
                    product['precio_bulto_sin_iva'],
                    product['imagen_url'],
                    'TRUE' if product['activo'] else 'FALSE',
                    'TRUE' if product['stock_critico'] else 'FALSE'
                ]
                data.append(row)
            
            # Subir datos
            sheet.update('A1', data)
            
            print(f"✅ Productos subidos a Google Sheets: {sheet_name}")
            print(f"🔗 URL: {sheet.spreadsheet.url}")
            
        except Exception as e:
            print(f"❌ Error al subir a Google Sheets: {e}")
            print("💡 Asegúrate de tener el archivo de credenciales JSON de Google")
    
    def process_pdf(self, save_csv: bool = True, upload_sheets: bool = False, 
                   credentials_file: str = None):
        """Proceso completo de extracción"""
        print("🚀 Iniciando extracción de productos del PDF...")
        
        # Extraer texto
        print("📄 Extrayendo texto del PDF...")
        text = self.extract_text_from_pdf()
        
        if not text:
            print("❌ No se pudo extraer texto del PDF")
            return
        
        # Extraer productos
        print("🔍 Analizando productos...")
        products = self.extract_products_from_text(text)
        
        if not products:
            print("❌ No se encontraron productos")
            return
        
        self.products = products
        
        # Guardar CSV
        if save_csv:
            self.save_to_csv(products)
        
        # Subir a Google Sheets
        if upload_sheets and credentials_file:
            self.upload_to_google_sheets(products, credentials_file)
        
        return products

def main():
    """Función principal"""
    # Configuración
    PDF_FILE = "listaDePrecios26-4-2025.pdf"  # Cambiar por ruta real
    CREDENTIALS_FILE = "google_credentials.json"  # Archivo de credenciales de Google
    
    # Verificar archivos
    if not os.path.exists(PDF_FILE):
        print(f"❌ No se encontró el archivo PDF: {PDF_FILE}")
        print("💡 Asegúrate de que el archivo esté en el directorio actual")
        return
    
    # Crear extractor
    extractor = TPGProductExtractor(PDF_FILE)
    
    # Procesar
    products = extractor.process_pdf(
        save_csv=True,
        upload_sheets=os.path.exists(CREDENTIALS_FILE),
        credentials_file=CREDENTIALS_FILE if os.path.exists(CREDENTIALS_FILE) else None
    )
    
    if products:
        print(f"\n🎉 Proceso completado exitosamente!")
        print(f"📊 {len(products)} productos procesados")
        
        # Mostrar algunos ejemplos
        print("\n📋 Primeros 3 productos:")
        for i, product in enumerate(products[:3]):
            print(f"  {i+1}. [{product['codigo']}] {product['descripcion'][:50]}...")
            print(f"     Categoría: {product['categoria']}")
            print(f"     Precio: ${product['precio_unitario']}")

if __name__ == "__main__":
    main()