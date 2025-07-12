import os
import re
import shutil
from pathlib import Path
from collections import defaultdict

def limpiar_fotos_productos():
    """
    Script para limpiar y organizar todas las fotos de productos TPG
    """
    
    # ============= CONFIGURACIÓN =============
    CARPETA_ORIGEN = "/media/santiago/KINGSTON/PRODUCTOS"  # 📝 CAMBIAR POR TU RUTA DEL PENDRIVE
    CARPETA_DESTINO = "/home/santiago/TPG_FOTOS_LIMPIAS"  # 📝 CAMBIAR POR DONDE QUIERES LA COPIA
    
    # Extensiones de imágenes válidas
    EXTENSIONES_VALIDAS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    
    print("🚀 INICIANDO LIMPIEZA DE FOTOS TPG")
    print(f"📂 Carpeta origen: {CARPETA_ORIGEN}")
    print(f"📁 Carpeta destino: {CARPETA_DESTINO}")
    print("=" * 60)
    
    # Verificar que existe la carpeta origen
    if not os.path.exists(CARPETA_ORIGEN):
        print(f"❌ ERROR: No se encuentra la carpeta {CARPETA_ORIGEN}")
        print("💡 Cambia la variable CARPETA_ORIGEN por la ruta correcta")
        return
    
    # Crear carpeta destino
    os.makedirs(CARPETA_DESTINO, exist_ok=True)
    
    # ============= BUSCAR TODOS LOS ARCHIVOS =============
    print("🔍 Buscando archivos de imagen...")
    
    archivos_encontrados = []
    
    # Recorrer recursivamente toda la carpeta
    for root, dirs, files in os.walk(CARPETA_ORIGEN):
        for file in files:
            ruta_completa = os.path.join(root, file)
            extension = Path(file).suffix.lower()
            
            # Solo procesar archivos de imagen
            if extension in EXTENSIONES_VALIDAS:
                archivos_encontrados.append({
                    'ruta_original': ruta_completa,
                    'nombre_original': file,
                    'extension': extension,
                    'carpeta': root
                })
    
    print(f"📸 Encontrados {len(archivos_encontrados)} archivos de imagen")
    
    # ============= EXTRAER IDs Y PROCESAR =============
    print("🔢 Extrayendo IDs de los nombres...")
    
    archivos_procesados = []
    ids_duplicados = defaultdict(list)
    
    for archivo in archivos_encontrados:
        nombre = archivo['nombre_original']
        
        # Extraer números del inicio del nombre
        match = re.match(r'^(\d+)', nombre)
        
        if match:
            id_producto = match.group(1)
            extension = archivo['extension']
            
            # Determinar nueva extensión (preferir .jpg)
            if extension in ['.jpeg']:
                nueva_extension = '.jpg'
            else:
                nueva_extension = extension
            
            nuevo_nombre = f"{id_producto}{nueva_extension}"
            
            archivo_procesado = {
                **archivo,
                'id_producto': id_producto,
                'nuevo_nombre': nuevo_nombre
            }
            
            archivos_procesados.append(archivo_procesado)
            ids_duplicados[id_producto].append(archivo_procesado)
        else:
            print(f"⚠️ No se pudo extraer ID de: {nombre}")
    
    # ============= MANEJAR DUPLICADOS =============
    print("🔄 Manejando duplicados...")
    
    archivos_finales = {}
    reporte_duplicados = []
    
    for id_producto, archivos_con_mismo_id in ids_duplicados.items():
        if len(archivos_con_mismo_id) > 1:
            # Hay duplicados - elegir el mejor
            print(f"🔄 ID {id_producto}: {len(archivos_con_mismo_id)} archivos")
            
            # Criterios de prioridad:
            # 1. Extensión .jpg > .png > otros
            # 2. Archivo más grande
            # 3. Nombre más simple (menos caracteres)
            
            def prioridad_archivo(archivo):
                ext = archivo['extension']
                tamaño = os.path.getsize(archivo['ruta_original'])
                simplicidad = len(archivo['nombre_original'])
                
                prioridad_ext = {'jpg': 3, '.jpeg': 3, '.png': 2, '.gif': 1}
                return (
                    prioridad_ext.get(ext, 0),  # Prioridad por extensión
                    tamaño,                      # Tamaño (más grande mejor)
                    -simplicidad                 # Simplicidad (menos caracteres mejor)
                )
            
            # Ordenar por prioridad y tomar el mejor
            mejor_archivo = max(archivos_con_mismo_id, key=prioridad_archivo)
            archivos_finales[id_producto] = mejor_archivo
            
            # Registrar duplicados para el reporte
            duplicados_descartados = [a for a in archivos_con_mismo_id if a != mejor_archivo]
            reporte_duplicados.append({
                'id': id_producto,
                'elegido': mejor_archivo['nombre_original'],
                'descartados': [a['nombre_original'] for a in duplicados_descartados]
            })
            
        else:
            # No hay duplicados
            archivos_finales[id_producto] = archivos_con_mismo_id[0]
    
    # ============= COPIAR ARCHIVOS =============
    print("📋 Copiando archivos limpios...")
    
    archivos_copiados = 0
    errores = []
    
    for id_producto, archivo in archivos_finales.items():
        try:
            origen = archivo['ruta_original']
            destino = os.path.join(CARPETA_DESTINO, archivo['nuevo_nombre'])
            
            shutil.copy2(origen, destino)
            archivos_copiados += 1
            
            # Mostrar progreso cada 100 archivos
            if archivos_copiados % 100 == 0:
                print(f"📸 Copiados {archivos_copiados} archivos...")
                
        except Exception as e:
            errores.append(f"Error copiando {archivo['nombre_original']}: {e}")
    
    # ============= GENERAR REPORTE =============
    print("\n" + "=" * 60)
    print("📊 REPORTE FINAL")
    print("=" * 60)
    
    print(f"✅ Archivos procesados exitosamente: {archivos_copiados}")
    print(f"📁 Carpeta destino: {CARPETA_DESTINO}")
    print(f"🔍 Archivos originales encontrados: {len(archivos_encontrados)}")
    print(f"🆔 IDs únicos procesados: {len(archivos_finales)}")
    print(f"🔄 Duplicados resueltos: {len(reporte_duplicados)}")
    
    if errores:
        print(f"❌ Errores: {len(errores)}")
        for error in errores[:5]:  # Mostrar solo primeros 5 errores
            print(f"   {error}")
        if len(errores) > 5:
            print(f"   ... y {len(errores) - 5} errores más")
    
    # Guardar reporte detallado
    reporte_archivo = os.path.join(CARPETA_DESTINO, "REPORTE_LIMPIEZA.txt")
    with open(reporte_archivo, 'w', encoding='utf-8') as f:
        f.write("REPORTE DE LIMPIEZA TPG FOTOS\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"Archivos procesados: {archivos_copiados}\n")
        f.write(f"Duplicados resueltos: {len(reporte_duplicados)}\n\n")
        
        if reporte_duplicados:
            f.write("DUPLICADOS RESUELTOS:\n")
            f.write("-" * 20 + "\n")
            for dup in reporte_duplicados:
                f.write(f"ID {dup['id']}:\n")
                f.write(f"  ✅ Elegido: {dup['elegido']}\n")
                for desc in dup['descartados']:
                    f.write(f"  ❌ Descartado: {desc}\n")
                f.write("\n")
        
        if errores:
            f.write("ERRORES:\n")
            f.write("-" * 20 + "\n")
            for error in errores:
                f.write(f"{error}\n")
    
    print(f"\n📄 Reporte detallado guardado en: {reporte_archivo}")
    
    # ============= VERIFICACIÓN FINAL =============
    print("\n🔍 VERIFICACIÓN FINAL:")
    archivos_destino = list(Path(CARPETA_DESTINO).glob("*.*"))
    archivos_imagen_destino = [f for f in archivos_destino if f.suffix.lower() in EXTENSIONES_VALIDAS]
    
    print(f"📸 Archivos de imagen en destino: {len(archivos_imagen_destino)}")
    
    # Mostrar algunos ejemplos
    print("\n📋 Ejemplos de archivos procesados:")
    for i, archivo in enumerate(sorted(archivos_imagen_destino)[:10]):
        print(f"   {archivo.name}")
    
    if len(archivos_imagen_destino) > 10:
        print(f"   ... y {len(archivos_imagen_destino) - 10} archivos más")
    
    print("\n🎉 ¡LIMPIEZA COMPLETADA!")
    print("📁 Próximo paso: Subir estos archivos a Vercel /public/productos/")


if __name__ == "__main__":
    limpiar_fotos_productos()