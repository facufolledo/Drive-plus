"""
Script para verificar solapamientos en el fixture del torneo 37
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def verificar_solapamientos():
    """Verifica solapamientos en todos los partidos del torneo 37"""
    session = Session()
    
    try:
        print("=" * 80)
        print("VERIFICAR SOLAPAMIENTOS EN TORNEO 37")
        print("=" * 80)
        
        # Obtener todos los partidos programados
        partidos = session.execute(
            text("""
                SELECT 
                    p.id_partido,
                    p.pareja1_id,
                    p.pareja2_id,
                    p.cancha_id,
                    p.fecha_hora,
                    c.nombre as cancha,
                    tp1.categoria_id
                FROM partidos p
                LEFT JOIN torneo_canchas c ON p.cancha_id = c.id
                LEFT JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
                WHERE tp1.torneo_id = 37
                AND p.fecha_hora IS NOT NULL
                ORDER BY p.fecha_hora, p.cancha_id
            """)
        ).fetchall()
        
        if not partidos:
            print("\nNo hay partidos programados en el torneo 37")
            return
        
        print(f"\nTotal de partidos programados: {len(partidos)}")
        
        # Obtener nombres de categorías
        categorias = {}
        cats = session.execute(
            text("SELECT id, nombre FROM torneo_categorias WHERE torneo_id = 37")
        ).fetchall()
        for cat_id, cat_nombre in cats:
            categorias[cat_id] = cat_nombre
        
        # Obtener parejas con sus jugadores
        parejas_jugadores = {}
        parejas = session.execute(
            text("""
                SELECT id, jugador1_id, jugador2_id
                FROM torneos_parejas
                WHERE torneo_id = 37
            """)
        ).fetchall()
        
        for pareja_id, j1, j2 in parejas:
            parejas_jugadores[pareja_id] = (j1, j2)
        
        # Verificar solapamientos
        solapamientos_cancha = []
        solapamientos_jugador = []
        
        for i, partido1 in enumerate(partidos):
            p1_id, p1_pareja1, p1_pareja2, p1_cancha, p1_fecha, p1_cancha_nombre, p1_cat_id = partido1
            
            if not p1_fecha:
                continue
            
            p1_cat = categorias.get(p1_cat_id, "Sin categoría")
            p1_inicio = p1_fecha
            p1_fin = p1_inicio + timedelta(minutes=90)  # Duración partido
            
            # Obtener jugadores del partido 1
            p1_jugadores = set()
            if p1_pareja1 in parejas_jugadores:
                p1_jugadores.update(parejas_jugadores[p1_pareja1])
            if p1_pareja2 in parejas_jugadores:
                p1_jugadores.update(parejas_jugadores[p1_pareja2])
            
            # Comparar con partidos posteriores
            for partido2 in partidos[i+1:]:
                p2_id, p2_pareja1, p2_pareja2, p2_cancha, p2_fecha, p2_cancha_nombre, p2_cat_id = partido2
                
                if not p2_fecha:
                    continue
                
                p2_cat = categorias.get(p2_cat_id, "Sin categoría")
                p2_inicio = p2_fecha
                p2_fin = p2_inicio + timedelta(minutes=90)
                
                # Verificar solapamiento de cancha
                if p1_cancha == p2_cancha:
                    # Mismo horario o solapamiento
                    if p1_inicio == p2_inicio or (p1_inicio < p2_fin and p2_inicio < p1_fin):
                        solapamientos_cancha.append({
                            'partido1_id': p1_id,
                            'partido2_id': p2_id,
                            'cancha': p1_cancha_nombre,
                            'fecha1': p1_inicio,
                            'fecha2': p2_inicio,
                            'cat1': p1_cat,
                            'cat2': p2_cat
                        })
                
                # Verificar solapamiento de jugadores
                p2_jugadores = set()
                if p2_pareja1 in parejas_jugadores:
                    p2_jugadores.update(parejas_jugadores[p2_pareja1])
                if p2_pareja2 in parejas_jugadores:
                    p2_jugadores.update(parejas_jugadores[p2_pareja2])
                
                jugadores_comunes = p1_jugadores & p2_jugadores
                
                if jugadores_comunes:
                    # Verificar si hay solapamiento temporal
                    if p1_inicio < p2_fin and p2_inicio < p1_fin:
                        solapamientos_jugador.append({
                            'partido1_id': p1_id,
                            'partido2_id': p2_id,
                            'jugadores': list(jugadores_comunes),
                            'fecha1': p1_inicio,
                            'fecha2': p2_inicio,
                            'cat1': p1_cat,
                            'cat2': p2_cat,
                            'diferencia_minutos': int((p2_inicio - p1_inicio).total_seconds() / 60)
                        })
        
        # Mostrar resultados
        print("\n" + "=" * 80)
        print("RESULTADOS")
        print("=" * 80)
        
        if solapamientos_cancha:
            print(f"\n[!] SOLAPAMIENTOS DE CANCHA: {len(solapamientos_cancha)}")
            print("-" * 80)
            for s in solapamientos_cancha:
                print(f"\nCancha: {s['cancha']}")
                print(f"  Partido {s['partido1_id']} ({s['cat1']}): {s['fecha1']}")
                print(f"  Partido {s['partido2_id']} ({s['cat2']}): {s['fecha2']}")
        else:
            print("\n[OK] No hay solapamientos de cancha")
        
        if solapamientos_jugador:
            print(f"\n[!] SOLAPAMIENTOS DE JUGADORES: {len(solapamientos_jugador)}")
            print("-" * 80)
            for s in solapamientos_jugador:
                print(f"\nJugadores: {s['jugadores']}")
                print(f"  Partido {s['partido1_id']} ({s['cat1']}): {s['fecha1']}")
                print(f"  Partido {s['partido2_id']} ({s['cat2']}): {s['fecha2']}")
                print(f"  Diferencia: {s['diferencia_minutos']} minutos")
        else:
            print("\n[OK] No hay solapamientos de jugadores")
        
        # Verificar intervalo mínimo de 3 horas
        print("\n" + "=" * 80)
        print("VERIFICAR INTERVALO MÍNIMO (180 minutos)")
        print("=" * 80)
        
        intervalos_cortos = []
        
        for i, partido1 in enumerate(partidos):
            p1_id, p1_pareja1, p1_pareja2, p1_cancha, p1_fecha, p1_cancha_nombre, p1_cat_id = partido1
            
            if not p1_fecha:
                continue
            
            p1_cat = categorias.get(p1_cat_id, "Sin categoría")
            
            p1_jugadores = set()
            if p1_pareja1 in parejas_jugadores:
                p1_jugadores.update(parejas_jugadores[p1_pareja1])
            if p1_pareja2 in parejas_jugadores:
                p1_jugadores.update(parejas_jugadores[p1_pareja2])
            
            for partido2 in partidos[i+1:]:
                p2_id, p2_pareja1, p2_pareja2, p2_cancha, p2_fecha, p2_cancha_nombre, p2_cat_id = partido2
                
                if not p2_fecha:
                    continue
                
                p2_cat = categorias.get(p2_cat_id, "Sin categoría")
                
                p2_jugadores = set()
                if p2_pareja1 in parejas_jugadores:
                    p2_jugadores.update(parejas_jugadores[p2_pareja1])
                if p2_pareja2 in parejas_jugadores:
                    p2_jugadores.update(parejas_jugadores[p2_pareja2])
                
                jugadores_comunes = p1_jugadores & p2_jugadores
                
                if jugadores_comunes:
                    diferencia_minutos = int((p2_fecha - p1_fecha).total_seconds() / 60)
                    
                    if 0 < diferencia_minutos < 180:
                        intervalos_cortos.append({
                            'partido1_id': p1_id,
                            'partido2_id': p2_id,
                            'jugadores': list(jugadores_comunes),
                            'fecha1': p1_fecha,
                            'fecha2': p2_fecha,
                            'cat1': p1_cat,
                            'cat2': p2_cat,
                            'diferencia_minutos': diferencia_minutos
                        })
        
        if intervalos_cortos:
            print(f"\n[!] INTERVALOS MENORES A 180 MINUTOS: {len(intervalos_cortos)}")
            print("-" * 80)
            for s in intervalos_cortos:
                print(f"\nJugadores: {s['jugadores']}")
                print(f"  Partido {s['partido1_id']} ({s['cat1']}): {s['fecha1']}")
                print(f"  Partido {s['partido2_id']} ({s['cat2']}): {s['fecha2']}")
                print(f"  [!] Diferencia: {s['diferencia_minutos']} minutos (minimo: 180)")
        else:
            print("\n[OK] Todos los intervalos son >= 180 minutos")
        
        # Resumen final
        print("\n" + "=" * 80)
        print("RESUMEN FINAL")
        print("=" * 80)
        print(f"Total partidos programados: {len(partidos)}")
        print(f"Solapamientos de cancha: {len(solapamientos_cancha)}")
        print(f"Solapamientos de jugadores: {len(solapamientos_jugador)}")
        print(f"Intervalos < 180 min: {len(intervalos_cortos)}")
        
        if not solapamientos_cancha and not solapamientos_jugador and not intervalos_cortos:
            print("\n[OK] FIXTURE PERFECTO! No hay problemas")
        else:
            print("\n[!] Hay problemas que requieren atencion")
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    verificar_solapamientos()
