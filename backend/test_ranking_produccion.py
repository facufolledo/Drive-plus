"""
Script para verificar el endpoint de ranking en producción
y limpiar el caché si es necesario
"""
import requests
import json
from dotenv import load_dotenv
import os

load_dotenv('.env.production')

# URLs
BASE_URL = "https://drive-plus-production.up.railway.app"
# BASE_URL = "http://localhost:8000"  # Descomentar para probar local

def test_ranking_endpoint():
    """Probar el endpoint de ranking"""
    print("=" * 60)
    print("VERIFICANDO ENDPOINT DE RANKING")
    print("=" * 60)
    
    try:
        # 1. Obtener ranking general (más jugadores para encontrar los que tienen partidos)
        print("\n1. Obteniendo ranking general...")
        response = requests.get(f"{BASE_URL}/ranking/?limit=100")
        
        if response.status_code != 200:
            print(f"❌ Error: Status {response.status_code}")
            print(response.text)
            return
        
        data = response.json()
        print(f"✅ Respuesta exitosa - {len(data)} jugadores")
        
        # 2. Buscar jugadores específicos que sabemos tienen partidos
        print("\n2. Verificando jugadores con partidos conocidos:")
        print("-" * 60)
        
        usuarios_con_partidos = [
            'bautistaoliva',  # ID 200, 2 partidos
            'coppedejoaco',   # ID 221, 3 partidos, 2 victorias
            'cristiancampos', # ID 213, 4 partidos, 3 victorias
            'nahuelmolina',   # ID 212, 4 partidos, 3 victorias
        ]
        
        encontrados = []
        for jugador in data:
            if jugador.get('nombre_usuario') in usuarios_con_partidos:
                encontrados.append(jugador)
                print(f"\n{jugador.get('nombre', '')} {jugador.get('apellido', '')} (@{jugador.get('nombre_usuario', 'N/A')})")
                print(f"   ID: {jugador.get('id_usuario')}")
                print(f"   Rating: {jugador.get('rating')}")
                print(f"   Partidos jugados: {jugador.get('partidos_jugados')}")
                print(f"   Partidos ganados: {jugador.get('partidos_ganados')}")
                print(f"   Tendencia: {jugador.get('tendencia')}")
                
                # Calcular winrate
                pj = jugador.get('partidos_jugados', 0)
                pg = jugador.get('partidos_ganados', 0)
                winrate = round((pg / pj) * 100) if pj > 0 else 0
                print(f"   Winrate calculado: {winrate}%")
                
                # Verificar si hay problema
                if pj > 0 and pg == 0:
                    print(f"   ⚠️  PROBLEMA: Tiene {pj} partidos pero 0 victorias")
        
        if len(encontrados) == 0:
            print("\n⚠️  No se encontraron los jugadores con partidos conocidos")
            print("Esto puede indicar un problema con el endpoint")
        
        # 3. Contar cuántos jugadores tienen el problema
        print("\n3. Análisis general:")
        print("-" * 60)
        
        jugadores_con_partidos = [j for j in data if j.get('partidos_jugados', 0) > 0]
        jugadores_con_problema = [j for j in jugadores_con_partidos if j.get('partidos_ganados', 0) == 0]
        
        print(f"Total jugadores en respuesta: {len(data)}")
        print(f"Jugadores con partidos: {len(jugadores_con_partidos)}")
        print(f"Jugadores con problema (partidos > 0 pero victorias = 0): {len(jugadores_con_problema)}")
        
        if len(jugadores_con_problema) > 0:
            print(f"\n⚠️  HAY {len(jugadores_con_problema)} JUGADORES CON EL PROBLEMA")
            print("\nJugadores afectados:")
            for j in jugadores_con_problema[:5]:
                print(f"  - {j.get('nombre_usuario')} (ID: {j.get('id_usuario')}): {j.get('partidos_jugados')} partidos, 0 victorias")
            return False
        else:
            print("\n✅ TODOS LOS DATOS SE VEN CORRECTOS")
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def clear_cache(token: str):
    """Limpiar el caché de rankings (requiere ser admin)"""
    print("\n" + "=" * 60)
    print("LIMPIANDO CACHÉ DE RANKINGS")
    print("=" * 60)
    
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{BASE_URL}/ranking/clear-cache",
            headers=headers
        )
        
        if response.status_code == 200:
            print("✅ Caché limpiado exitosamente")
            return True
        elif response.status_code == 403:
            print("❌ Error: No tienes permisos de administrador")
            return False
        else:
            print(f"❌ Error: Status {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    # Probar endpoint
    datos_correctos = test_ranking_endpoint()
    
    if not datos_correctos:
        print("\n" + "=" * 60)
        print("SOLUCIÓN")
        print("=" * 60)
        print("\nPara limpiar el caché, necesitas:")
        print("1. Obtener tu token de Firebase desde localStorage")
        print("2. Ejecutar este script con el token:")
        print("   python test_ranking_produccion.py --clear-cache YOUR_TOKEN")
        print("\nO desde el frontend:")
        print("1. Abre la consola del navegador")
        print("2. Ejecuta: localStorage.getItem('firebase_token')")
        print("3. Copia el token")
        print("4. Llama al endpoint: POST /ranking/clear-cache con Authorization: Bearer TOKEN")
