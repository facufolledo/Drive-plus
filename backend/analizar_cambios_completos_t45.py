#!/usr/bin/env python3
"""
Analizar estado actual vs estado deseado según imágenes del usuario
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)

TORNEO_ID = 45

def main():
    s = Session()
    try:
        print("=" * 80)
        print("ANÁLISIS COMPLETO - TORNEO 45")
        print("=" * 80)
        
        # Obtener todas las categorías y sus zonas
        categorias = s.execute(text("""
            SELECT DISTINCT 
                tc.id,
                tc.nombre as categoria,
                tz.id as zona_id,
                tz.nombre as zona
            FROM torneo_categorias tc
            LEFT JOIN torneo_zonas tz ON tz.categoria_id = tc.id
            WHERE tc.torneo_id = :tid
            ORDER BY tc.nombre, tz.nombre
        """), {"tid": TORNEO_ID}).fetchall()
        
        print("\n📊 CATEGORÍAS Y ZONAS ACTUALES:")
        print("=" * 80)
        for cat in categorias:
            print(f"  {cat.categoria} - Zona {cat.zona} (Zona ID: {cat.zona_id})")
        
        # Obtener todas las parejas por categoría
        print("\n\n👥 PAREJAS POR CATEGORÍA:")
        print("=" * 80)
        
        parejas = s.execute(text("""
            SELECT 
                tc.nombre as categoria,
                tz.nombre as zona,
                tp.id as pareja_id,
                tp.nombre_pareja,
                u1.nombre_usuario as j1,
                u2.nombre_usuario as j2
            FROM torneos_parejas tp
            JOIN torneo_categorias tc ON tp.categoria_id = tc.id
            LEFT JOIN torneo_zonas tz ON tp.zona_id = tz.id
            JOIN usuarios u1 ON tp.jugador1_id = u1.id_usuario
            JOIN usuarios u2 ON tp.jugador2_id = u2.id_usuario
            WHERE tp.torneo_id = :tid
            ORDER BY tc.nombre, tz.nombre, tp.nombre_pareja
        """), {"tid": TORNEO_ID}).fetchall()
        
        cat_actual = None
        zona_actual = None
        for p in parejas:
            if p.categoria != cat_actual:
                cat_actual = p.categoria
                print(f"\n{cat_actual}:")
                print("-" * 80)
            if p.zona != zona_actual:
                zona_actual = p.zona
                print(f"  Zona {zona_actual}:")
            print(f"    {p.pareja_id:3d}. {p.nombre_pareja:40s} ({p.j1} - {p.j2})")
        
        # Obtener todos los partidos programados
        print("\n\n📅 PARTIDOS PROGRAMADOS:")
        print("=" * 80)
        
        partidos = s.execute(text("""
            SELECT 
                tc.nombre as categoria,
                tz.nombre as zona,
                p.id_partido,
                tp1.nombre_pareja as pareja1,
                tp2.nombre_pareja as pareja2,
                p.fecha_hora,
                tca.nombre as cancha,
                EXTRACT(DOW FROM p.fecha_hora) as dow
            FROM partidos p
            JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
            JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
            JOIN torneo_categorias tc ON tp1.categoria_id = tc.id
            LEFT JOIN torneo_zonas tz ON p.zona_id = tz.id
            LEFT JOIN torneo_canchas tca ON p.cancha_id = tca.id
            WHERE tp1.torneo_id = :tid
            ORDER BY tc.nombre, tz.nombre, p.fecha_hora
        """), {"tid": TORNEO_ID}).fetchall()
        
        cat_actual = None
        zona_actual = None
        dias = {4: 'JUEVES', 5: 'VIERNES', 6: 'SÁBADO', 0: 'DOMINGO'}
        
        for p in partidos:
            if p.categoria != cat_actual:
                cat_actual = p.categoria
                print(f"\n{cat_actual}:")
                print("-" * 80)
            if p.zona != zona_actual:
                zona_actual = p.zona
                print(f"  Zona {zona_actual}:")
            
            dia = dias.get(int(p.dow), 'DESCONOCIDO')
            hora = p.fecha_hora.strftime('%H:%M')
            print(f"    P{p.id_partido:3d}: {p.pareja1:30s} vs {p.pareja2:30s} | {dia:8s} {hora} | {p.cancha}")
        
        print("\n" + "=" * 80)
        print("ANÁLISIS COMPLETADO")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    main()
