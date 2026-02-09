import requests
import json

# Test del endpoint de ranking en PRODUCCIÓN
BASE_URL = "https://drive-plus-production.up.railway.app"

def test_ranking_produccion():
    """Probar endpoint de ranking en producción"""
    print("🔍 Probando endpoint /ranking/ en PRODUCCIÓN")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/ranking/", params={"limit": 5})
        
        print(f"Status Code: {response.status_code}")
        print(f"\nRespuesta:")
        
        if response.status_code == 200:
            data = response.json()
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # Verificar campos importantes
            if data and len(data) > 0:
                primer_jugador = data[0]
                print(f"\n✅ Primer jugador:")
                print(f"   - ID: {primer_jugador.get('id_usuario')}")
                print(f"   - Nombre: {primer_jugador.get('nombre')} {primer_jugador.get('apellido')}")
                print(f"   - Rating: {primer_jugador.get('rating')}")
                print(f"   - Partidos jugados: {primer_jugador.get('partidos_jugados')}")
                print(f"   - Partidos ganados: {primer_jugador.get('partidos_ganados')}")
                print(f"   - Tendencia: {primer_jugador.get('tendencia')}")
                
                # Verificar si los campos existen
                campos_faltantes = []
                if 'partidos_ganados' not in primer_jugador:
                    campos_faltantes.append('partidos_ganados')
                if 'tendencia' not in primer_jugador:
                    campos_faltantes.append('tendencia')
                
                if campos_faltantes:
                    print(f"\n⚠️  Campos faltantes: {', '.join(campos_faltantes)}")
                else:
                    print(f"\n✅ Todos los campos están presentes")
                    
                # Verificar valores
                if primer_jugador.get('partidos_ganados') == 0 and primer_jugador.get('partidos_jugados', 0) > 0:
                    print(f"\n⚠️  PROBLEMA: Tiene {primer_jugador.get('partidos_jugados')} partidos jugados pero 0 ganados")
                    print(f"   Esto indica que el cálculo de partidos_ganados no está funcionando")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_ranking_produccion()
