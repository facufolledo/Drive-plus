"""
Script para verificar el fixture del torneo 37 en detalle
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from sqlalchemy.orm import Session
from src.database.config import get_db
from src.models.driveplus_models import Partido, PerfilUsuario
from src.models.torneo_models import TorneoPareja, TorneoCancha, TorneoCategoria
from datetime import datetime, timedelta
import pytz

load_dotenv()

def verificar_fixture():
    """Verifica el fixture del torneo 37"""
    db = next(get_db())
    
    try:
        print("\n" + "="*80)
        print("🔍 FIXTURE TORNEO 37 - DETALLADO")
        print("="*80 + "\n")
        
        # Obtener partidos del torneo 37
        partidos = db.query(Partido).filter(
            Partido.id_torneo == 37,
            Partido.fecha_hora.isnot(None)
        ).order_by(Partido.fecha_hora).all()
        
        print(f"Total de partidos programados: {len(partidos)}\n")
        
        # Agrupar por día
        partidos_por_dia = {}
        for partido in partidos:
            fecha = partido.fecha_hora.date()
            if fecha not in partidos_por_dia:
                partidos_por_dia[fecha] = []
            partidos_por_dia[fecha].append(partido)
        
        # Mostrar por día
        for fecha in sorted(partidos_por_dia.keys()):
            print(f"📅 {fecha.strftime('%Y-%m-%d')}")
            print("-" * 80)
            
            partidos_dia = sorted(partidos_por_dia[fecha], key=lambda p: p.fecha_hora)
            
            for partido in partidos_dia:
                # Obtener categoría
                categoria = db.query(TorneoCategoria).filter(
                    TorneoCategoria.id == partido.categoria_id
                ).first()
                cat_nombre = categoria.nombre if categoria else "Sin cat"
                
                # Obtener cancha
                cancha = db.query(TorneoCancha).filter(
                    TorneoCancha.id == partido.cancha_id
                ).first()
                cancha_nombre = cancha.nombre if cancha else "Sin cancha"
                
                # Obtener parejas
                pareja1 = db.query(TorneoPareja).filter(TorneoPareja.id == partido.pareja1_id).first()
                pareja2 = db.query(TorneoPareja).filter(TorneoPareja.id == partido.pareja2_id).first()
                
                if pareja1 and pareja2:
                    # Nombres pareja 1
                    p1_j1 = db.query(PerfilUsuario).filter(PerfilUsuario.id_usuario == pareja1.jugador1_id).first()
                    p1_j2 = db.query(PerfilUsuario).filter(PerfilUsuario.id_usuario == pareja1.jugador2_id).first()
                    nombre_p1 = f"{p1_j1.apellido}/{p1_j2.apellido}" if p1_j1 and p1_j2 else f"Pareja {pareja1.id}"
                    
                    # Nombres pareja 2
                    p2_j1 = db.query(PerfilUsuario).filter(PerfilUsuario.id_usuario == pareja2.jugador1_id).first()
                    p2_j2 = db.query(PerfilUsuario).filter(PerfilUsuario.id_usuario == pareja2.jugador2_id).first()
                    nombre_p2 = f"{p2_j1.apellido}/{p2_j2.apellido}" if p2_j1 and p2_j2 else f"Pareja {pareja2.id}"
                    
                    # Calcular hora fin (70 minutos)
                    hora_fin = partido.fecha_hora + timedelta(minutes=70)
                    
                    hora_inicio_str = partido.fecha_hora.strftime('%H:%M')
                    hora_fin_str = hora_fin.strftime('%H:%M')
                    
                    print(f"  {hora_inicio_str}-{hora_fin_str} | {cancha_nombre} | {cat_nombre:12} | {nombre_p1:20} vs {nombre_p2:20} | ID: {partido.id_partido}")
            
            print()
        
        # Verificar partidos sin programar
        partidos_sin_programar = db.query(Partido).filter(
            Partido.id_torneo == 37,
            Partido.fecha_hora.is_(None)
        ).count()
        
        print("="*80)
        print(f"📊 RESUMEN")
        print("="*80)
        print(f"Partidos programados: {len(partidos)}")
        print(f"Partidos sin programar: {partidos_sin_programar}")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    verificar_fixture()
