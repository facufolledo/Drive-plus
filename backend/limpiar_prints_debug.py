"""
Script para eliminar prints de debug del código manteniendo solo los de errores
"""
import re
import os

def limpiar_prints_archivo(filepath):
    """Elimina prints de debug de un archivo manteniendo solo los de errores"""
    with open(filepath, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    lineas = contenido.split('\n')
    lineas_limpias = []
    
    for linea in lineas:
        # Mantener la línea si:
        # 1. No es un print
        # 2. Es un print dentro de un except (error handling)
        # 3. Es un print de error crítico
        
        es_print = 'print(' in linea or 'print (' in linea
        
        if not es_print:
            lineas_limpias.append(linea)
            continue
        
        # Verificar si es un print de error (dentro de except o con "Error" en el mensaje)
        es_error = (
            'Error' in linea or 
            'error' in linea or
            '❌' in linea or
            'Exception' in linea
        )
        
        if es_error:
            lineas_limpias.append(linea)
        else:
            # Es un print de debug, comentarlo en lugar de eliminarlo
            # (por si acaso necesitamos reactivarlo)
            lineas_limpias.append('# DEBUG: ' + linea.lstrip())
    
    contenido_limpio = '\n'.join(lineas_limpias)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(contenido_limpio)
    
    return contenido != contenido_limpio

# Archivos a limpiar
archivos = [
    'src/services/torneo_fixture_global_service.py',
    'src/services/notification_service.py',
    'src/services/torneo_confirmacion_service.py',
]

print("🧹 Limpiando prints de debug...\n")

for archivo in archivos:
    filepath = os.path.join('backend', archivo)
    if os.path.exists(filepath):
        if limpiar_prints_archivo(filepath):
            print(f"✅ Limpiado: {archivo}")
        else:
            print(f"⏭️  Sin cambios: {archivo}")
    else:
        print(f"⚠️  No encontrado: {archivo}")

print("\n✅ Limpieza completada")
