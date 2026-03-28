import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

# Fixture completo según la imagen
FIXTURE_IMAGEN = {
    'Zona A': [
        {'parejas': ['Emiliano Lucero', 'Facundo Folledo', 'Agustín Mercado', 'Cesar Zaracho'], 'fecha': '2026-03-27 23:59:00'},
        {'parejas': ['Joselin Silva', 'Dilan Aguilar', 'Emiliano Lucero', 'Facundo Folledo'], 'fecha': '2026-03-28 10:00:00'},
        {'parejas': ['Joselin Silva', 'Dilan Aguilar', 'Agustín Mercado', 'Cesar Zaracho'], 'fecha': '2026-03-28 17:00:00'},
    ],
    'Zona B': [
        {'parejas': ['Imanol Yaryura', 'Santino Díaz', 'Nazareno Diaz', 'Ismael Salido'], 'fecha': '2026-03-28 10:00:00'},
        {'parejas': ['Imanol Yaryura', 'Santino Díaz', 'Leo Diaz', 'Valentín Barroca'], 'fecha': '2026-03-27 23:30:00'},
        {'parejas': ['Nazareno Diaz', 'Ismael Salido', 'Leo Diaz', 'Valentín Barroca'], 'fecha': '2026-03-28 12:30:00'},
    ],
    'Zona C': [
        {'parejas': ['Fabricio Barros', 'Mariano Cruz', 'Esteban Bedini', 'Benicio Johannesen'], 'fecha': '2026-03-27 20:30:00'},
        {'parejas': ['Esteban Bedini', 'Benicio Johannesen', 'Exequiel Diaz', 'Yamil Jofre'], 'fecha': '2026-03-27 22:30:00'},
        {'parejas': ['Fabricio Barros', 'Mariano Cruz', 'Exequiel Diaz', 'Yamil Jofre'], 'fecha': '2026-03-27 23:30:00'},
    ],
    'Zona D': [
        {'parejas': ['Diego Bicet', 'Marcelo Aguilar', 'Renzo Gonzales', 'Erik Letterucci'], 'fecha': '2026-03-28 19:00:00'},
    ],
    'Zona E': [
        {'parejas': ['Lucas Juin', 'Tiago López', 'Dante Saldaño', 'Alejandro Vásquez'], 'fecha': '2026-03-28 19:00:00'},
        {'parejas': ['Álvaro Díaz', 'Federico William Montivero', 'Lucas Juin', 'Tiago López'], 'fecha': '2026-03-27 20:30:00'},
        {'parejas': ['Álvaro Díaz', 'Federico William Montivero', 'Dante Saldaño', 'Alejandro Vásquez'], 'fecha': '2026-03-27 22:00:00'},
    ],
    'Zona F': [
        {'parejas': ['Gustavo Millicay', 'Ezequiel Heredia', 'Aron Brizuela', 'Valentín Moreno'], 'fecha': '2026-03-28 08:00:00'},
        {'parejas': ['Gustavo Millicay', 'Ezequiel Heredia', 'Federico Millicay', 'Exequiel Carrizo'], 'fecha': '2026-03-28 09:30:00'},
        {'parejas': ['Aron Brizuela', 'Valentín Moreno', 'Federico Millicay', 'Exequiel Carrizo'], 'fecha': '2026-03-28 11:00:00'},
    ],
    'Zona G': [
        {'parejas': ['Matias Moreno', 'christian moreno', 'Martín Aredes', 'Matías Aredes'], 'fecha': '2026-03-28 16:00:00'},
        {'parejas': ['Axel Alfaro', 'Matías Alfaro', 'Martín Aredes', 'Matías Aredes'], 'fecha': '2026-03-28 19:00:00'},
        {'parejas': ['Matias Moreno', 'christian moreno', 'Axel Alfaro', 'Matías Alfaro'], 'fecha': '2026-03-27 23:30:00'},
    ],
    'Zona H': [
        {'parejas': ['Juan Pablo Romero', 'Juan Romero', 'Leonardo Villarrubia', 'Alberto Ibañaz'], 'fecha': '2026-03-27 20:30:00'},
        {'parejas': ['Juan Pablo Romero', 'Juan Romero', 'Mariano Nieto', 'Federico Olivera'], 'fecha': '2026-03-27 22:00:00'},
        {'parejas': ['Leonardo Villarrubia', 'Alberto Ibañaz', 'Mariano Nieto', 'Federico Olivera'], 'fecha': '2026-03-27 23:30:00'},
    ],
}

def buscar_pareja_por_nombres(cur, nombre1, apellido1, nombre2, apellido2, categoria_id):
    """Busca una pareja por los nombres de los jugadores"""
    cur.execute("""
        SELECT tp.id
        FROM torneos_parejas tp
        JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
        JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
        WHERE tp.torneo_id = 46 
        AND tp.categoria_id = %s
        AND (
            (pu1.nombre ILIKE %s AND pu1.apellido ILIKE %s AND pu2.nombre ILIKE %s AND pu2.apellido ILIKE %s)
            OR
            (pu2.nombre ILIKE %s AND pu2.apellido ILIKE %s AND pu1.nombre ILIKE %s AND pu1.apellido ILIKE %s)
        )
    """, (categoria_id, nombre1, apellido1, nombre2, apellido2, nombre1, apellido1, nombre2, apellido2))
    
    result = cur.fetchone()
    return result['id'] if result else None

def recrear_fixture():
    conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Obtener categoria_id de 7ma
        cur.execute("SELECT id FROM torneo_categorias WHERE torneo_id = 46 AND nombre = '7ma'")
        categoria_id = cur.fetchone()['id']
        
        print(f"Categoría 7ma: ID {categoria_id}\n")
        
        # 1. ELIMINAR todos los partidos de 7ma
        cur.execute("""
            DELETE FROM partidos 
            WHERE id_torneo = 46 AND categoria_id = %s
        """, (categoria_id,))
        
        partidos_eliminados = cur.rowcount
        print(f"✅ Eliminados {partidos_eliminados} partidos existentes\n")
        
        # 2. RECREAR partidos según la imagen
        print("🔨 Creando partidos según imagen:\n")
        
        partidos_creados = 0
        
        for zona_nombre, partidos in FIXTURE_IMAGEN.items():
            # Obtener zona_id
            cur.execute("""
                SELECT id FROM torneo_zonas 
                WHERE torneo_id = 46 AND categoria_id = %s AND nombre = %s
            """, (categoria_id, zona_nombre))
            
            zona = cur.fetchone()
            if not zona:
                print(f"❌ Zona {zona_nombre} no encontrada")
                continue
            
            zona_id = zona['id']
            print(f"{zona_nombre}:")
            
            for partido_data in partidos:
                nombres = partido_data['parejas']
                fecha = partido_data['fecha']
                
                # Parsear nombres (formato: "Nombre1 Apellido1", "Nombre2 Apellido2", "Nombre3 Apellido3", "Nombre4 Apellido4")
                # Pareja 1: nombres[0] y nombres[1]
                # Pareja 2: nombres[2] y nombres[3]
                
                partes1 = nombres[0].rsplit(' ', 1)
                nombre1_p1 = partes1[0] if len(partes1) > 1 else nombres[0]
                apellido1_p1 = partes1[1] if len(partes1) > 1 else ''
                
                partes2 = nombres[1].rsplit(' ', 1)
                nombre2_p1 = partes2[0] if len(partes2) > 1 else nombres[1]
                apellido2_p1 = partes2[1] if len(partes2) > 1 else ''
                
                partes3 = nombres[2].rsplit(' ', 1)
                nombre1_p2 = partes3[0] if len(partes3) > 1 else nombres[2]
                apellido1_p2 = partes3[1] if len(partes3) > 1 else ''
                
                partes4 = nombres[3].rsplit(' ', 1)
                nombre2_p2 = partes4[0] if len(partes4) > 1 else nombres[3]
                apellido2_p2 = partes4[1] if len(partes4) > 1 else ''
                
                # Buscar parejas
                pareja1_id = buscar_pareja_por_nombres(cur, nombre1_p1, apellido1_p1, nombre2_p1, apellido2_p1, categoria_id)
                pareja2_id = buscar_pareja_por_nombres(cur, nombre1_p2, apellido1_p2, nombre2_p2, apellido2_p2, categoria_id)
                
                if not pareja1_id or not pareja2_id:
                    print(f"  ❌ No se encontraron parejas: {nombres[0]}/{nombres[1]} vs {nombres[2]}/{nombres[3]}")
                    continue
                
                # Crear partido
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
                """, (46, categoria_id, zona_id, pareja1_id, pareja2_id, fecha))
                
                partido_id = cur.fetchone()['id_partido']
                partidos_creados += 1
                print(f"  ✅ Partido {partido_id}: P{pareja1_id} vs P{pareja2_id} - {fecha}")
            
            print()
        
        conn.commit()
        
        print(f"\n🎉 FIXTURE RECREADO:")
        print(f"   - {partidos_eliminados} partidos eliminados")
        print(f"   - {partidos_creados} partidos creados")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    recrear_fixture()
