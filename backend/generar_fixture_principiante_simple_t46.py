import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
import requests

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("GENERAR FIXTURE PRINCIPIANTE - TORNEO 46")
print("=" * 80)

try:
    # 1. Eliminar partidos existentes de Principiante
    print("\n🗑️  Eliminando partidos existentes de Principiante...")
    
    cur.execute("""
        SELECT id FROM torneo_categorias 
        WHERE torneo_id = 46 AND nombre = 'Principiante'
    """)
    categoria = cur.fetchone()
    categoria_id = categoria['id']
    
    cur.execute("""
        DELETE FROM partidos
        WHERE id_torneo = 46
        AND categoria_id = %s
    """, (categoria_id,))
    
    partidos_eliminados = cur.rowcount
    print(f"   ✅ {partidos_eliminados} partidos eliminados")
    
    conn.commit()
    
    print(f"\n" + "=" * 80)
    print("LLAMANDO AL ENDPOINT DE GENERAR FIXTURE")
    print("=" * 80)
    
    # 2. Llamar al endpoint de generar fixture
    # Nota: Necesitarás un token de autenticación válido
    backend_url = "https://drive-plus-production.up.railway.app"
    
    print(f"\n⚠️  Para generar el fixture con horarios, ejecuta:")
    print(f"\n   POST {backend_url}/torneos/46/generar-fixture")
    print(f"   Headers: Authorization: Bearer <tu_token>")
    print(f"\n   O desde el frontend, haz clic en 'Generar Fixture' para el torneo 46")
    
    # Verificar estado actual
    cur.execute("""
        SELECT COUNT(*) as total
        FROM partidos
        WHERE id_torneo = 46
        AND categoria_id = %s
    """, (categoria_id,))
    
    total_partidos = cur.fetchone()['total']
    
    print(f"\n📊 ESTADO ACTUAL:")
    print(f"   Partidos de Principiante: {total_partidos}")
    print(f"   Zonas creadas: 4 (A, B, C, D)")
    print(f"   Parejas inscritas: 12")
    
    if total_partidos == 0:
        print(f"\n✅ Listo para generar fixture desde el frontend")

except Exception as e:
    conn.rollback()
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    cur.close()
    conn.close()
