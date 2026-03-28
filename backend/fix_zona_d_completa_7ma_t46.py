import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

try:
    # Obtener IDs
    cur.execute("SELECT id FROM torneo_categorias WHERE torneo_id = 46 AND nombre = '7ma'")
    categoria_id = cur.fetchone()['id']
    
    cur.execute("SELECT id FROM torneo_zonas WHERE torneo_id = 46 AND categoria_id = %s AND nombre = 'Zona D'", (categoria_id,))
    zona_d_id = cur.fetchone()['id']
    
    print(f"Categoría 7ma: ID {categoria_id}")
    print(f"Zona D: ID {zona_d_id}\n")
    
    # Ver partidos actuales de Zona D
    cur.execute("""
        SELECT 
            p.id_partido,
            p.pareja1_id,
            p.pareja2_id,
            p.fecha_hora
        FROM partidos p
        WHERE p.id_torneo = 46 AND p.zona_id = %s
        ORDER BY p.id_partido
    """, (zona_d_id,))
    
    partidos_actuales = cur.fetchall()
    print(f"Partidos actuales en Zona D: {len(partidos_actuales)}")
    for p in partidos_actuales:
        fecha = p['fecha_hora'].strftime('%Y-%m-%d %H:%M') if p['fecha_hora'] else 'Sin horario'
        print(f"  Partido {p['id_partido']}: P{p['pareja1_id']} vs P{p['pareja2_id']} - {fecha}")
    
    # Obtener todas las parejas únicas en Zona D
    parejas_en_zona = set()
    for p in partidos_actuales:
        parejas_en_zona.add(p['pareja1_id'])
        parejas_en_zona.add(p['pareja2_id'])
    
    print(f"\nParejas en Zona D: {sorted(parejas_en_zona)}")
    
    # Si solo hay 2 parejas, agregar la pareja 1005
    if len(parejas_en_zona) == 2:
        print("\n⚠️  Zona D tiene solo 2 parejas, agregando pareja 1005 (Lucas Apostolo / Mariano Roldán)")
        
        pareja_nueva = 1005
        parejas_existentes = sorted(parejas_en_zona)
        
        # Crear 2 partidos nuevos
        partidos_a_crear = [
            (pareja_nueva, parejas_existentes[0], '2026-03-27 20:00:00'),
            (pareja_nueva, parejas_existentes[1], '2026-03-27 21:00:00')
        ]
        
        for p1_id, p2_id, fecha in partidos_a_crear:
            cur.execute("""
                INSERT INTO partidos (
                    id_torneo, categoria_id, zona_id,
                    pareja1_id, pareja2_id,
                    fase, estado, fecha, fecha_hora, id_creador
                ) VALUES (
                    %s, %s, %s,
                    %s, %s,
                    'zona', 'pendiente', NOW(), %s, 1
                )
                RETURNING id_partido
            """, (46, categoria_id, zona_d_id, p1_id, p2_id, fecha))
            
            partido_id = cur.fetchone()['id_partido']
            print(f"  ✅ Creado partido {partido_id}: P{p1_id} vs P{p2_id} - {fecha}")
        
        conn.commit()
        print("\n🎉 Zona D completada con 3 parejas y 3 partidos")
    
    elif len(parejas_en_zona) == 3:
        print("\n✅ Zona D ya tiene 3 parejas")
        
        # Verificar que haya 3 partidos
        if len(partidos_actuales) < 3:
            print(f"⚠️  Pero solo tiene {len(partidos_actuales)} partidos, deberían ser 3")
            
            # Encontrar qué partidos faltan
            parejas_list = sorted(parejas_en_zona)
            partidos_esperados = [
                (parejas_list[0], parejas_list[1]),
                (parejas_list[0], parejas_list[2]),
                (parejas_list[1], parejas_list[2])
            ]
            
            partidos_existentes = [(p['pareja1_id'], p['pareja2_id']) for p in partidos_actuales]
            
            for p1, p2 in partidos_esperados:
                existe = (p1, p2) in partidos_existentes or (p2, p1) in partidos_existentes
                if not existe:
                    print(f"  ❌ Falta partido: P{p1} vs P{p2}")
                    # Crear partido faltante
                    cur.execute("""
                        INSERT INTO partidos (
                            id_torneo, categoria_id, zona_id,
                            pareja1_id, pareja2_id,
                            fase, estado, fecha, fecha_hora, id_creador
                        ) VALUES (
                            %s, %s, %s,
                            %s, %s,
                            'zona', 'pendiente', NOW(), '2026-03-27 22:00:00', 1
                        )
                        RETURNING id_partido
                    """, (46, categoria_id, zona_d_id, p1, p2))
                    
                    partido_id = cur.fetchone()['id_partido']
                    print(f"  ✅ Creado partido {partido_id}: P{p1} vs P{p2}")
            
            conn.commit()
        else:
            print("✅ Y tiene 3 partidos completos")
    
except Exception as e:
    conn.rollback()
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    cur.close()
    conn.close()
