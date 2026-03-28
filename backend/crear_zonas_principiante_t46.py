import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("CREAR ZONAS PRINCIPIANTE - TORNEO 46")
print("=" * 80)

# Obtener categoría Principiante
cur.execute("""
    SELECT id FROM torneo_categorias
    WHERE torneo_id = 46 AND nombre = 'Principiante'
""")

categoria = cur.fetchone()
if not categoria:
    print("❌ Categoría Principiante no encontrada")
    cur.close()
    conn.close()
    exit(1)

categoria_id = categoria['id']
print(f"✅ Categoría Principiante ID: {categoria_id}")

# Obtener todas las parejas inscritas
cur.execute("""
    SELECT 
        tp.id,
        pu1.nombre || ' ' || pu1.apellido as jugador1,
        pu2.nombre || ' ' || pu2.apellido as jugador2
    FROM torneos_parejas tp
    JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
    JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
    WHERE tp.torneo_id = 46
    AND tp.categoria_id = %s
    ORDER BY tp.id
""", (categoria_id,))

parejas = cur.fetchall()

print(f"\n📋 PAREJAS INSCRITAS ({len(parejas)}):")
for p in parejas:
    print(f"  {p['id']}: {p['jugador1']} / {p['jugador2']}")

# Distribución de zonas (4 zonas de 3 parejas)
# Zona A: Ludueña/Apostolo (1048) + Aballay/Ríos (1042) + otra pareja
# Zonas B, C, D: 3 parejas cada una

zonas_config = [
    {
        'nombre': 'Zona A',
        'parejas': [1048, 1042, 1041]  # Ludueña/Apostolo, Aballay/Ríos, Jatuff/Alcazar
    },
    {
        'nombre': 'Zona B',
        'parejas': [1043, 1044, 1045]  # Velázquez/Zurita, Córdoba/Paez, Sotomayor/Diaz
    },
    {
        'nombre': 'Zona C',
        'parejas': [1046, 1047, 1049]  # Morales/Vera, Vera/Calderón, Agostini/Paez
    },
    {
        'nombre': 'Zona D',
        'parejas': [1050, 1051, 1052]  # Villalba/Alvarado, Toledo/Barrionuevo, Molina/Dávila
    }
]

print(f"\n" + "=" * 80)
print("CREANDO ZONAS")
print("=" * 80)

try:
    zonas_creadas = []
    
    for idx, zona_config in enumerate(zonas_config, 1):
        # Crear zona
        cur.execute("""
            INSERT INTO torneo_zonas (torneo_id, nombre, categoria_id, numero_orden)
            VALUES (46, %s, %s, %s)
            RETURNING id
        """, (zona_config['nombre'], categoria_id, idx))
        
        zona_id = cur.fetchone()['id']
        zonas_creadas.append(zona_id)
        
        print(f"\n✅ {zona_config['nombre']} creada (ID: {zona_id})")
        
        # Asignar parejas a la zona (actualizar zona_id en torneos_parejas)
        # Nota: Si la tabla no tiene zona_id, necesitamos crear los partidos directamente
        
        # Verificar si existe columna zona_id en torneos_parejas
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'torneos_parejas' AND column_name = 'zona_id'
        """)
        
        tiene_zona_id = cur.fetchone() is not None
        
        if tiene_zona_id:
            # Actualizar zona_id en parejas
            for pareja_id in zona_config['parejas']:
                cur.execute("""
                    UPDATE torneos_parejas
                    SET zona_id = %s
                    WHERE id = %s
                """, (zona_id, pareja_id))
                
                # Obtener nombres de la pareja
                pareja_info = next((p for p in parejas if p['id'] == pareja_id), None)
                if pareja_info:
                    print(f"  - Pareja {pareja_id}: {pareja_info['jugador1']} / {pareja_info['jugador2']}")
        else:
            print(f"  Parejas asignadas (se crearán partidos después):")
            for pareja_id in zona_config['parejas']:
                pareja_info = next((p for p in parejas if p['id'] == pareja_id), None)
                if pareja_info:
                    print(f"  - Pareja {pareja_id}: {pareja_info['jugador1']} / {pareja_info['jugador2']}")
    
    conn.commit()
    
    print(f"\n" + "=" * 80)
    print(f"✅ {len(zonas_creadas)} ZONAS CREADAS EXITOSAMENTE")
    print("=" * 80)
    
    print(f"\n📊 RESUMEN:")
    print(f"  - Zona A: Ludueña/Apostolo + Aballay/Ríos + Jatuff/Alcazar")
    print(f"  - Zona B: 3 parejas")
    print(f"  - Zona C: 3 parejas")
    print(f"  - Zona D: 3 parejas")
    print(f"\n  Total: 12 parejas en 4 zonas")
    
    if not tiene_zona_id:
        print(f"\n⚠️  NOTA: La tabla torneos_parejas no tiene columna zona_id.")
        print(f"   Las zonas se asignarán al crear los partidos.")

except Exception as e:
    conn.rollback()
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    cur.close()
    conn.close()
