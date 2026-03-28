import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

# Cargar variables de entorno de producción
load_dotenv('.env.production')

def generar_fixture_5ta():
    """Genera fixture de zona para 5ta del torneo 46"""
    
    # Convertir URL de pg8000 a psycopg2
    db_url = os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://')
    conn = psycopg2.connect(db_url)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # 1. Verificar categoría 5ta
        cur.execute("""
            SELECT id, nombre 
            FROM torneo_categorias 
            WHERE torneo_id = 46 AND nombre = '5ta'
        """)
        categoria = cur.fetchone()
        
        if not categoria:
            print("❌ No se encontró categoría 5ta en torneo 46")
            return
        
        categoria_id = categoria['id']
        print(f"✅ Categoría 5ta encontrada: ID {categoria_id}")
        
        # 2. Obtener parejas inscritas con nombres
        cur.execute("""
            SELECT 
                tp.id, 
                tp.jugador1_id, 
                tp.jugador2_id,
                p1.nombre || ' ' || p1.apellido as jugador1_nombre,
                p2.nombre || ' ' || p2.apellido as jugador2_nombre
            FROM torneos_parejas tp
            JOIN perfil_usuarios p1 ON tp.jugador1_id = p1.id_usuario
            JOIN perfil_usuarios p2 ON tp.jugador2_id = p2.id_usuario
            WHERE tp.torneo_id = 46 AND tp.categoria_id = %s
            ORDER BY tp.id
        """, (categoria_id,))
        
        parejas = cur.fetchall()
        print(f"\n📋 Parejas inscritas: {len(parejas)}")
        for p in parejas:
            print(f"  - Pareja {p['id']}: {p['jugador1_nombre']} / {p['jugador2_nombre']}")
        
        if len(parejas) < 2:
            print("❌ No hay suficientes parejas para generar fixture")
            return
        
        # 3. Crear zonas (2 parejas por zona para 14 parejas = 7 zonas)
        zonas_creadas = []
        parejas_por_zona = 2
        num_zonas = (len(parejas) + parejas_por_zona - 1) // parejas_por_zona
        
        letras_zonas = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']
        
        for i in range(num_zonas):
            letra = letras_zonas[i]
            cur.execute("""
                INSERT INTO torneo_zonas (torneo_id, categoria_id, nombre, numero_orden)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (46, categoria_id, f"Zona {letra}", i + 1))
            
            zona_id = cur.fetchone()['id']
            zonas_creadas.append({'id': zona_id, 'nombre': f"Zona {letra}"})
            print(f"✅ Creada {letra}: ID {zona_id}")
        
        # 4. Generar partidos de zona (asignar parejas a zonas mediante partidos)
        partidos_creados = 0
        
        for idx in range(0, len(parejas), 2):
            if idx + 1 < len(parejas):
                zona_idx = idx // 2
                zona = zonas_creadas[zona_idx]
                
                p1 = parejas[idx]
                p2 = parejas[idx + 1]
                
                cur.execute("""
                    INSERT INTO partidos (
                        id_torneo, categoria_id, zona_id,
                        pareja1_id, pareja2_id,
                        fase, estado, fecha, id_creador
                    ) VALUES (
                        %s, %s, %s,
                        %s, %s,
                        'zona', 'pendiente', NOW(), 1
                    )
                    RETURNING id_partido
                """, (
                    46, categoria_id, zona['id'],
                    p1['id'], p2['id']
                ))
                
                partido_id = cur.fetchone()['id_partido']
                partidos_creados += 1
                print(f"  ✅ Partido {partido_id} ({zona['nombre']}): {p1['jugador1_nombre']}/{p1['jugador2_nombre']} vs {p2['jugador1_nombre']}/{p2['jugador2_nombre']}")
        
        conn.commit()
        
        print(f"\n🎉 FIXTURE GENERADO:")
        print(f"   - {num_zonas} zonas creadas")
        print(f"   - {partidos_creados} partidos de zona creados")
        print(f"   - Todos los partidos sin horario asignado (pendiente de programación)")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    generar_fixture_5ta()
