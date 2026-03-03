"""
Script para verificar qué categorías devuelve el endpoint de torneos
"""
import requests
import json

# Endpoint local
url = "http://localhost:8000/torneos"

try:
    response = requests.get(url)
    response.raise_for_status()
    
    torneos = response.json()
    
    print(f"\n📊 Total de torneos: {len(torneos)}\n")
    
    for torneo in torneos[:3]:  # Mostrar solo los primeros 3
        print(f"🏆 Torneo ID {torneo['id']}: {torneo['nombre']}")
        print(f"   Categoría (campo viejo): {torneo.get('categoria', 'N/A')}")
        print(f"   Género (campo viejo): {torneo.get('genero', 'N/A')}")
        print(f"   Total categorías: {torneo.get('total_categorias', 0)}")
        
        if 'categorias' in torneo and torneo['categorias']:
            print(f"   ✅ Categorías (nuevo):")
            for cat in torneo['categorias']:
                print(f"      - {cat['nombre']} ({cat['genero']})")
        else:
            print(f"   ❌ No tiene array de categorías")
        print()

except requests.exceptions.ConnectionError:
    print("❌ Error: No se puede conectar al backend en http://localhost:8000")
    print("   Asegúrate de que el backend esté corriendo")
except Exception as e:
    print(f"❌ Error: {e}")
