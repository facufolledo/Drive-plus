#!/usr/bin/env python3
"""
Migrar usuarios duplicados específicos identificados manualmente
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)

# Casos a migrar
MIGRACIONES = [
    # TEMP -> REAL (usar Firebase)
    {"temp_id": 855, "real_id": 67, "nombre": "Carlos Gudiño"},
    {"temp_id": 829, "real_id": 228, "nombre": "Jere Vera"},
    {"temp_id": 845, "real_id": 88, "nombre": "Ignacio Villegas"},
    
    # TEMP -> TEMP (usar el que tiene más partidos)
    {"temp_id": 861, "real_id": None, "nombre": "Jere Arrebola", "nota": "Buscar Jeremias Arrebola"},
    {"temp_id": 828, "real_id": None, "nombre": "Jere Arrebola", "nota": "Buscar Jeremias Arrebola"},
    {"temp_id": 195, "real_id": 551, "nombre": "Tiago Córdoba", "nota": "Usar el que tiene partidos"},
    {"temp_id": 863, "real_id": 510, "nombre": "Kevin Gurgone", "nota": "Usar el que tiene partidos"},
    {"temp_id": 841, "real_id": 865, "nombre": "Juan Magui", "nota": "Usar el que tiene partidos"},
    {"temp_id": 768, "real_id": 814, "nombre": "Axel Nieto", "nota": "Usar el que tiene partidos"},
    {"temp_id": 852, "real_id": 864, "nombre": "Matias Olivera", "nota": "Usar el que tiene partidos"},
    {"temp_id": 801, "real_id": 493, "nombre": "Mario Santander", "nota": "Usar el que tiene partidos"},
    {"temp_id": 868, "real_id": 767, "nombre": "Suarez Suarez", "nota": "Usar el que tiene partidos"},
    {"temp_id": 838, "real_id": 193, "nombre": "Agustin Chumbita", "nota": "Usar el que tiene partidos"},
]

def contar_partidos(session, user_id):
    """Cuenta partidos jugados por un usuario"""
    result = session.execute(text("""
        SELECT COUNT(DISTINCT p.id_partido) as total
        FROM partidos p
        JOIN torneos_parejas tp ON (p.pareja1_id = tp.id OR p.pareja2_id = tp.id)
        WHERE (tp.jugador1_id = :uid OR tp.jugador2_id = :uid)
        AND p.estado IN ('finalizado', 'en_curso')
    """), {"uid": user_id}).fetchone()
    return result.total if result else 0

def verificar_usuario(session, user_id):
    """Obtiene info de un usuario"""
    result = session.execute(text("""
        SELECT u.id_usuario, u.nombre_usuario, u.email, u.rating,
               COALESCE(p.nombre, '') as nombre, COALESCE(p.apellido, '') as apellido,
               CASE 
                   WHEN u.email LIKE '%@driveplus.temp' THEN 'TEMP'
                   WHEN u.password_hash IS NULL OR u.password_hash = '' THEN 'FIREBASE'
                   ELSE 'LOCAL'
               END as tipo
        FROM usuarios u
        LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        WHERE u.id_usuario = :uid
    """), {"uid": user_id}).fetchone()
    return result

def main():
    s = Session()
    try:
        print("=" * 80)
        print("ANÁLISIS DE MIGRACIONES - USUARIOS DUPLICADOS")
        print("=" * 80)
        
        # Primero buscar "Jeremias Arrebola"
        jeremias = s.execute(text("""
            SELECT u.id_usuario, u.nombre_usuario, u.rating,
                   p.nombre, p.apellido
            FROM usuarios u
            LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
            WHERE (p.nombre ILIKE '%jeremias%' AND p.apellido ILIKE '%arrebola%')
               OR u.nombre_usuario ILIKE '%jeremias%arrebola%'
        """)).fetchall()
        
        print("\n🔍 Buscando Jeremias Arrebola:")
        if jeremias:
            for j in jeremias:
                partidos = contar_partidos(s, j.id_usuario)
                print(f"   ID={j.id_usuario}, user={j.nombre_usuario}, rating={j.rating}")
                print(f"   Nombre: {j.nombre} {j.apellido}")
                print(f"   Partidos: {partidos}")
        else:
            print("   ❌ No encontrado")
        
        print("\n" + "=" * 80)
        print("ANÁLISIS POR CASO")
        print("=" * 80)
        
        for caso in MIGRACIONES:
            temp_id = caso["temp_id"]
            real_id = caso.get("real_id")
            nombre = caso["nombre"]
            nota = caso.get("nota", "")
            
            print(f"\n📋 {nombre}")
            if nota:
                print(f"   Nota: {nota}")
            
            # Info del temp
            temp = verificar_usuario(s, temp_id)
            if temp:
                partidos_temp = contar_partidos(s, temp_id)
                print(f"   TEMP: ID={temp.id_usuario}, user={temp.nombre_usuario}")
                print(f"         {temp.nombre} {temp.apellido}, rating={temp.rating}")
                print(f"         Partidos: {partidos_temp}, Tipo: {temp.tipo}")
            else:
                print(f"   ❌ TEMP ID={temp_id} no encontrado")
                continue
            
            # Info del real (si existe)
            if real_id:
                real = verificar_usuario(s, real_id)
                if real:
                    partidos_real = contar_partidos(s, real_id)
                    print(f"   REAL: ID={real.id_usuario}, user={real.nombre_usuario}")
                    print(f"         {real.nombre} {real.apellido}, rating={real.rating}")
                    print(f"         Partidos: {partidos_real}, Tipo: {real.tipo}")
                    
                    # Decidir cuál mantener
                    if real.tipo == 'FIREBASE':
                        print(f"   ✅ MIGRAR: {temp_id} -> {real_id} (usar Firebase)")
                    elif partidos_real > partidos_temp:
                        print(f"   ✅ MIGRAR: {temp_id} -> {real_id} (más partidos: {partidos_real} vs {partidos_temp})")
                    elif partidos_temp > partidos_real:
                        print(f"   ⚠️  MIGRAR: {real_id} -> {temp_id} (más partidos: {partidos_temp} vs {partidos_real})")
                    else:
                        print(f"   ⚠️  EMPATE: ambos tienen {partidos_temp} partidos")
                else:
                    print(f"   ❌ REAL ID={real_id} no encontrado")
        
        print("\n" + "=" * 80)
        print("RESUMEN")
        print("=" * 80)
        print(f"Total casos analizados: {len(MIGRACIONES)}")
        print("\nPara ejecutar migraciones, usar el script migrar_usuario_especifico.py")
        print("Ejemplo: python migrar_usuario_especifico.py --origen 855 --destino 67")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    main()
