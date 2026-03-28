import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("ELIMINAR PARTIDOS PRINCIPIANTE - TORNEO 46")
print("=" * 80)

try:
    # Contar partidos antes de eliminar
    cur.execute("""
        SELECT COUNT(*) as total
        FROM partidos
        WHERE id_torneo = 46
        AND categoria_id = 125
        AND fase = 'zona'
    """)
    
    total_antes = cur.fetchone()['total']
    print(f"\n📊 Partidos de Principiante encontrados: {total_antes}")
    
    if total_antes == 0:
        print("\n⚠️  No hay partidos de Principiante para eliminar")
    else:
        # Eliminar partidos
        cur.execute("""
            DELETE FROM partidos
            WHERE id_torneo = 46
            AND categoria_id = 125
            AND fase = 'zona'
        """)
        
        partidos_eliminados = cur.rowcount
        conn.commit()
        
        print(f"\n✅ {partidos_eliminados} partidos eliminados")
        
        # Verificar que se eliminaron
        cur.execute("""
            SELECT COUNT(*) as total
            FROM partidos
            WHERE id_torneo = 46
            AND categoria_id = 125
            AND fase = 'zona'
        """)
        
        total_despues = cur.fetchone()['total']
        print(f"📊 Partidos restantes: {total_despues}")
    
    print("\n" + "=" * 80)
    print("✅ LISTO - Esperando instrucciones para regenerar")
    print("=" * 80)

except Exception as e:
    conn.rollback()
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    cur.close()
    conn.close()
