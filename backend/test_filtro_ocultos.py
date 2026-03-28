"""
Script para verificar que el endpoint de producción filtre torneos ocultos
"""
import requests

def test_filtro():
    # URL de producción
    url = "https://drive-plus-production.up.railway.app/torneos"
    
    print("🔍 Consultando torneos en producción...")
    print(f"URL: {url}\n")
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Error: Status code {response.status_code}")
            print(response.text)
            return
        
        torneos = response.json()
        print(f"✅ Respuesta exitosa: {len(torneos)} torneos")
        
        # Buscar torneo 42
        torneo_42 = None
        for t in torneos:
            if t.get('id') == 42:
                torneo_42 = t
                break
        
        if torneo_42:
            print(f"\n❌ PROBLEMA: El torneo 42 APARECE en el listado")
            print(f"   Nombre: {torneo_42.get('nombre')}")
            print(f"   Estado: {torneo_42.get('estado')}")
            print(f"\n⚠️  El backend aún no tiene el filtro actualizado")
            print(f"   Railway puede tardar unos minutos en deployar")
        else:
            print(f"\n✅ CORRECTO: El torneo 42 NO aparece en el listado")
            print(f"   El filtro está funcionando correctamente")
        
        # Mostrar algunos torneos para verificar
        print(f"\n📋 Primeros 5 torneos visibles:")
        for t in torneos[:5]:
            print(f"   - ID {t.get('id')}: {t.get('nombre')} (estado: {t.get('estado')})")
        
    except requests.exceptions.Timeout:
        print("❌ Timeout: El servidor no respondió")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_filtro()
