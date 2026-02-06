"""
Script para configurar horarios y canchas del torneo 37
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import json

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def configurar_torneo37():
    """Configura horarios y canchas del torneo 37"""
    session = Session()
    
    try:
        print("=" * 80)
        print("CONFIGURAR HORARIOS Y CANCHAS - TORNEO 37")
        print("=" * 80)
        
        # Verificar que el torneo existe
        torneo = session.execute(
            text("SELECT id, nombre, fecha_inicio, fecha_fin FROM torneos WHERE id = 37")
        ).fetchone()
        
        if not torneo:
            print("❌ El torneo 37 no existe")
            return
        
        print(f"\n✅ Torneo: {torneo[1]}")
        print(f"   Fechas: {torneo[2]} al {torneo[3]}")
        
        # Solicitar horarios
        print(f"\n{'=' * 80}")
        print("CONFIGURACIÓN DE HORARIOS")
        print(f"{'=' * 80}")
        print("\nFormato: día,horaInicio,horaFin")
        print("Ejemplo: viernes,09:00,23:00")
        print("Escribe 'fin' cuando termines\n")
        
        horarios = []
        while True:
            entrada = input("Horario (o 'fin'): ").strip()
            if entrada.lower() == 'fin':
                break
            
            try:
                partes = entrada.split(',')
                if len(partes) != 3:
                    print("❌ Formato incorrecto. Usa: día,horaInicio,horaFin")
                    continue
                
                dia = partes[0].strip().lower()
                hora_inicio = partes[1].strip()
                hora_fin = partes[2].strip()
                
                # Validar día
                dias_validos = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
                if dia not in dias_validos:
                    print(f"❌ Día inválido. Usa: {', '.join(dias_validos)}")
                    continue
                
                horarios.append({
                    "dias": [dia],
                    "horaInicio": hora_inicio,
                    "horaFin": hora_fin
                })
                print(f"   ✅ Agregado: {dia} de {hora_inicio} a {hora_fin}")
                
            except Exception as e:
                print(f"❌ Error: {e}")
        
        if not horarios:
            print("\n⚠️  No se agregaron horarios")
        else:
            print(f"\n📋 Horarios configurados: {len(horarios)}")
            for h in horarios:
                print(f"   • {h['dias'][0]}: {h['horaInicio']} - {h['horaFin']}")
        
        # Solicitar canchas
        print(f"\n{'=' * 80}")
        print("CONFIGURACIÓN DE CANCHAS")
        print(f"{'=' * 80}")
        print("\nEscribe el nombre de cada cancha")
        print("Ejemplo: Cancha 1, Cancha Techada, etc.")
        print("Escribe 'fin' cuando termines\n")
        
        canchas = []
        while True:
            nombre = input("Nombre de cancha (o 'fin'): ").strip()
            if nombre.lower() == 'fin':
                break
            
            if nombre:
                canchas.append(nombre)
                print(f"   ✅ Agregada: {nombre}")
        
        if not canchas:
            print("\n⚠️  No se agregaron canchas")
        else:
            print(f"\n🏟️  Canchas configuradas: {len(canchas)}")
            for c in canchas:
                print(f"   • {c}")
        
        # Confirmar cambios
        if not horarios and not canchas:
            print("\n⚠️  No hay cambios para guardar")
            return
        
        print(f"\n{'=' * 80}")
        confirmar = input("¿Guardar configuración? (si/no): ").strip().lower()
        
        if confirmar != 'si':
            print("\n❌ Cambios descartados")
            return
        
        # Guardar horarios
        if horarios:
            horarios_json = json.dumps(horarios)
            session.execute(
                text("""
                    UPDATE torneos 
                    SET horarios_disponibles = CAST(:horarios AS jsonb)
                    WHERE id = 37
                """),
                {"horarios": horarios_json}
            )
            print(f"\n✅ Horarios guardados")
        
        # Guardar canchas
        if canchas:
            for nombre in canchas:
                session.execute(
                    text("""
                        INSERT INTO torneo_canchas (torneo_id, nombre, activa)
                        VALUES (37, :nombre, true)
                    """),
                    {"nombre": nombre}
                )
            print(f"✅ {len(canchas)} cancha(s) guardada(s)")
        
        session.commit()
        print(f"\n{'=' * 80}")
        print("✅ CONFIGURACIÓN COMPLETADA")
        print(f"{'=' * 80}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    configurar_torneo37()
