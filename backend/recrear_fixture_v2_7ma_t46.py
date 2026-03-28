import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

# Mapeo manual de parejas según IDs conocidos
PAREJAS_MAP = {
    'Emiliano Lucero / Facundo Folledo': 1002,
    'Agustín Mercado / Cesar Zaracho': 1017,
    'Joselin Silva / Dilan Aguilar': 1011,
    'Imanol Yaryura / Santino Díaz': 1009,
    'Nazareno Diaz / Ismael Salido': 1012,
    'Leo Diaz / Valentín Barroca': 1025,
    'Fabricio Barros / Mariano Cruz': 1006,
    'Esteban Bedini / Benicio Johannesen': 1010,
    'Exequiel Diaz / Yamil Jofre': 1024,
    'Diego Bicet / Marcelo Aguilar': 1016,
    'Renzo Gonzales / Erik Letterucci': 1023,
    'Lucas Juin / Tiago López': 1008,
    'Dante Saldaño / Alejandro Vásquez': 1022,
    'Álvaro Díaz / Federico William Montivero': 1003,
    'Gustavo Millicay / Ezequiel Heredia': 1007,
    'Aron Brizuela / Valentín Moreno': 1014,
    'Federico Millicay / Exequiel Carrizo': 1021,
    'Matias Moreno / christian moreno': 1004,
    'Martín Aredes / Matías Aredes': 1020,
    'Axel Alfaro / Matías Alfaro': 1015,
    'Juan Pablo Romero / Juan Romero': 1013,
    'Leonardo Villarrubia / Alberto Ibañaz': 1018,
    'Mariano Nieto / Federico Olivera': 1019,
    'Lucas Apostolo / Mariano Roldán': 1005,  # La pareja que faltaba en Zona D
}

# Fixture completo según la imagen
FIXTURE_IMAGEN = [
    # Zona A
    {'zona': 'Zona A', 'pareja1': 'Emiliano Lucero / Facundo Folledo', 'pareja2': 'Agustín Mercado / Cesar Zaracho', 'fecha': '2026-03-27 23:59:00'},
    {'zona': 'Zona A', 'pareja1': 'Joselin Silva / Dilan Aguilar', 'pareja2': 'Emiliano Lucero / Facundo Folledo', 'fecha': '2026-03-28 10:00:00'},
    {'zona': 'Zona A', 'pareja1': 'Joselin Silva / Dilan Aguilar', 'pareja2': 'Agustín Mercado / Cesar Zaracho', 'fecha': '2026-03-28 17:00:00'},
    
    # Zona B
    {'zona': 'Zona B', 'pareja1': 'Imanol Yaryura / Santino Díaz', 'pareja2': 'Nazareno Diaz / Ismael Salido', 'fecha': '2026-03-28 10:00:00'},
    {'zona': 'Zona B', 'pareja1': 'Imanol Yaryura / Santino Díaz', 'pareja2': 'Leo Diaz / Valentín Barroca', 'fecha': '2026-03-27 23:30:00'},
    {'zona': 'Zona B', 'pareja1': 'Nazareno Diaz / Ismael Salido', 'pareja2': 'Leo Diaz / Valentín Barroca', 'fecha': '2026-03-28 12:30:00'},
    
    # Zona C
    {'zona': 'Zona C', 'pareja1': 'Fabricio Barros / Mariano Cruz', 'pareja2': 'Esteban Bedini / Benicio Johannesen', 'fecha': '2026-03-27 20:30:00'},
    {'zona': 'Zona C', 'pareja1': 'Esteban Bedini / Benicio Johannesen', 'pareja2': 'Exequiel Diaz / Yamil Jofre', 'fecha': '2026-03-27 22:30:00'},
    {'zona': 'Zona C', 'pareja1': 'Fabricio Barros / Mariano Cruz', 'pareja2': 'Exequiel Diaz / Yamil Jofre', 'fecha': '2026-03-27 23:30:00'},
    
    # Zona D
    {'zona': 'Zona D', 'pareja1': 'Diego Bicet / Marcelo Aguilar', 'pareja2': 'Renzo Gonzales / Erik Letterucci', 'fecha': '2026-03-28 19:00:00'},
    
    # Zona E
    {'zona': 'Zona E', 'pareja1': 'Lucas Juin / Tiago López', 'pareja2': 'Dante Saldaño / Alejandro Vásquez', 'fecha': '2026-03-28 19:00:00'},
    {'zona': 'Zona E', 'pareja1': 'Álvaro Díaz / Federico William Montivero', 'pareja2': 'Lucas Juin / Tiago López', 'fecha': '2026-03-27 20:30:00'},
    {'zona': 'Zona E', 'pareja1': 'Álvaro Díaz / Federico William Montivero', 'pareja2': 'Dante Saldaño / Alejandro Vásquez', 'fecha': '2026-03-27 22:00:00'},
    
    # Zona F
    {'zona': 'Zona F', 'pareja1': 'Gustavo Millicay / Ezequiel Heredia', 'pareja2': 'Aron Brizuela / Valentín Moreno', 'fecha': '2026-03-28 08:00:00'},
    {'zona': 'Zona F', 'pareja1': 'Gustavo Millicay / Ezequiel Heredia', 'pareja2': 'Federico Millicay / Exequiel Carrizo', 'fecha': '2026-03-28 09:30:00'},
    {'zona': 'Zona F', 'pareja1': 'Aron Brizuela / Valentín Moreno', 'pareja2': 'Federico Millicay / Exequiel Carrizo', 'fecha': '2026-03-28 11:00:00'},
    
    # Zona G
    {'zona': 'Zona G', 'pareja1': 'Matias Moreno / christian moreno', 'pareja2': 'Martín Aredes / Matías Aredes', 'fecha': '2026-03-28 16:00:00'},
    {'zona': 'Zona G', 'pareja1': 'Axel Alfaro / Matías Alfaro', 'pareja2': 'Martín Aredes / Matías Aredes', 'fecha': '2026-03-28 19:00:00'},
    {'zona': 'Zona G', 'pareja1': 'Matias Moreno / christian moreno', 'pareja2': 'Axel Alfaro / Matías Alfaro', 'fecha': '2026-03-27 23:30:00'},
    
    # Zona H
    {'zona': 'Zona H', 'pareja1': 'Juan Pablo Romero / Juan Romero', 'pareja2': 'Leonardo Villarrubia / Alberto Ibañaz', 'fecha': '2026-03-27 20:30:00'},
    {'zona': 'Zona H', 'pareja1': 'Juan Pablo Romero / Juan Romero', 'pareja2': 'Mariano Nieto / Federico Olivera', 'fecha': '2026-03-27 22:00:00'},
    {'zona': 'Zona H', 'pareja1': 'Leonardo Villarrubia / Alberto Ibañaz', 'pareja2': 'Mariano Nieto / Federico Olivera', 'fecha': '2026-03-27 23:30:00'},
]

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
        zona_actual = None
        
        for partido_data in FIXTURE_IMAGEN:
            zona_nombre = partido_data['zona']
            pareja1_nombre = partido_data['pareja1']
            pareja2_nombre = partido_data['pareja2']
            fecha = partido_data['fecha']
            
            if zona_actual != zona_nombre:
                if zona_actual:
                    print()
                zona_actual = zona_nombre
                print(f"{zona_nombre}:")
            
            # Obtener zona_id
            cur.execute("""
                SELECT id FROM torneo_zonas 
                WHERE torneo_id = 46 AND categoria_id = %s AND nombre = %s
            """, (categoria_id, zona_nombre))
            
            zona = cur.fetchone()
            if not zona:
                print(f"  ❌ Zona {zona_nombre} no encontrada")
                continue
            
            zona_id = zona['id']
            
            # Obtener IDs de parejas
            pareja1_id = PAREJAS_MAP.get(pareja1_nombre)
            pareja2_id = PAREJAS_MAP.get(pareja2_nombre)
            
            if not pareja1_id or not pareja2_id:
                print(f"  ❌ No se encontraron parejas: {pareja1_nombre} vs {pareja2_nombre}")
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
        
        conn.commit()
        
        print(f"\n\n🎉 FIXTURE RECREADO:")
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
