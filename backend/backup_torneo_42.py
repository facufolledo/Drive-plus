"""
Script para hacer backup completo del torneo 42 antes de ocultarlo
Guarda todos los datos en formato JSON para poder recrearlo después
"""
import os
import sys
import json
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

from src.models.driveplus_models import Usuario, Partido
from src.models.torneo_models import (
    Torneo, TorneoCategoria, TorneoPareja, TorneoZona, 
    TorneoOrganizador, TorneoCancha, TorneoSlot
)

def serialize_datetime(obj):
    """Convierte datetime y date a string ISO"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if hasattr(obj, 'isoformat'):  # Para date, time, etc.
        return obj.isoformat()
    return obj

def backup_torneo_42():
    db = SessionLocal()
    try:
        torneo_id = 42
        
        print(f"🔍 Buscando torneo {torneo_id}...")
        torneo = db.query(Torneo).filter(Torneo.id == torneo_id).first()
        
        if not torneo:
            print(f"❌ Torneo {torneo_id} no encontrado")
            return
        
        print(f"✅ Torneo encontrado: {torneo.nombre}")
        
        # Estructura del backup
        backup = {
            "metadata": {
                "backup_date": datetime.now().isoformat(),
                "torneo_id": torneo_id,
                "torneo_nombre": torneo.nombre
            },
            "torneo": {},
            "categorias": [],
            "parejas": [],
            "zonas": [],
            "partidos": [],
            "organizadores": [],
            "canchas": [],
            "slots": []
        }
        
        # 1. DATOS DEL TORNEO
        print("\n📋 Guardando datos del torneo...")
        torneo_dict = {
            "nombre": torneo.nombre,
            "descripcion": torneo.descripcion,
            "categoria": torneo.categoria,
            "estado": torneo.estado,
            "fecha_inicio": serialize_datetime(torneo.fecha_inicio),
            "fecha_fin": serialize_datetime(torneo.fecha_fin),
            "lugar": torneo.lugar,
            "genero": getattr(torneo, 'genero', 'masculino'),
            "formato": getattr(torneo, 'formato', 'grupos'),
            "creado_por": torneo.creado_por,
            "horarios_disponibles": getattr(torneo, 'horarios_disponibles', None),
            "requiere_pago": getattr(torneo, 'requiere_pago', False),
            "monto_inscripcion": float(torneo.monto_inscripcion) if getattr(torneo, 'monto_inscripcion', None) else None,
            "alias_cbu_cvu": getattr(torneo, 'alias_cbu_cvu', None),
            "titular_cuenta": getattr(torneo, 'titular_cuenta', None),
            "banco": getattr(torneo, 'banco', None),
            "telefono_contacto": getattr(torneo, 'telefono_contacto', None),
            "created_at": serialize_datetime(torneo.created_at)
        }
        backup["torneo"] = torneo_dict
        
        # 2. CATEGORÍAS
        print("📂 Guardando categorías...")
        categorias = db.query(TorneoCategoria).filter(
            TorneoCategoria.torneo_id == torneo_id
        ).all()
        
        for cat in categorias:
            backup["categorias"].append({
                "id": cat.id,
                "nombre": cat.nombre,
                "genero": cat.genero,
                "rating_minimo": getattr(cat, 'rating_minimo', None),
                "rating_maximo": getattr(cat, 'rating_maximo', None),
                "max_parejas": getattr(cat, 'max_parejas', None)
            })
        print(f"   ✓ {len(categorias)} categorías")
        
        # 3. PAREJAS
        print("👥 Guardando parejas...")
        parejas = db.query(TorneoPareja).filter(
            TorneoPareja.torneo_id == torneo_id
        ).all()
        
        for pareja in parejas:
            backup["parejas"].append({
                "id": pareja.id,
                "jugador1_id": pareja.jugador1_id,
                "jugador2_id": pareja.jugador2_id,
                "nombre_pareja": getattr(pareja, 'nombre_pareja', None),
                "estado": pareja.estado,
                "categoria_id": getattr(pareja, 'categoria_id', None),
                "disponibilidad_horaria": getattr(pareja, 'disponibilidad_horaria', None),
                "created_at": serialize_datetime(getattr(pareja, 'created_at', None))
            })
        print(f"   ✓ {len(parejas)} parejas")
        
        # 4. ZONAS
        print("🗺️  Guardando zonas...")
        zonas = db.query(TorneoZona).filter(
            TorneoZona.torneo_id == torneo_id
        ).all()
        
        for zona in zonas:
            backup["zonas"].append({
                "id": zona.id,
                "nombre": zona.nombre,
                "categoria_id": getattr(zona, 'categoria_id', None),
                "parejas_ids": getattr(zona, 'parejas_ids', None)
            })
        print(f"   ✓ {len(zonas)} zonas")
        
        # 5. PARTIDOS - Omitidos (se pueden regenerar)
        print("⚽ Partidos omitidos (se regeneran automáticamente)")
        partidos = []
        
        # 6. ORGANIZADORES
        print("👔 Guardando organizadores...")
        organizadores = db.query(TorneoOrganizador).filter(
            TorneoOrganizador.torneo_id == torneo_id
        ).all()
        
        for org in organizadores:
            backup["organizadores"].append({
                "user_id": org.user_id
            })
        print(f"   ✓ {len(organizadores)} organizadores")
        
        # 7. CANCHAS
        print("🏟️  Guardando canchas...")
        canchas = db.query(TorneoCancha).filter(
            TorneoCancha.torneo_id == torneo_id
        ).all()
        
        for cancha in canchas:
            backup["canchas"].append({
                "id": cancha.id,
                "nombre": cancha.nombre
            })
        print(f"   ✓ {len(canchas)} canchas")
        
        # 8. SLOTS
        print("⏰ Guardando slots horarios...")
        slots = db.query(TorneoSlot).filter(
            TorneoSlot.torneo_id == torneo_id
        ).all()
        
        for slot in slots:
            backup["slots"].append({
                "id": slot.id,
                "fecha": serialize_datetime(getattr(slot, 'fecha', None)),
                "hora_inicio": getattr(slot, 'hora_inicio', None),
                "hora_fin": getattr(slot, 'hora_fin', None)
            })
        print(f"   ✓ {len(slots)} slots")
        
        # Guardar backup en archivo JSON
        filename = f"backup_torneo_{torneo_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(backup, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Backup guardado en: {filename}")
        print(f"\n📊 RESUMEN:")
        print(f"   - Torneo: {torneo.nombre}")
        print(f"   - Categorías: {len(categorias)}")
        print(f"   - Parejas: {len(parejas)}")
        print(f"   - Zonas: {len(zonas)}")
        print(f"   - Partidos: {len(partidos)}")
        print(f"   - Organizadores: {len(organizadores)}")
        print(f"   - Canchas: {len(canchas)}")
        print(f"   - Slots: {len(slots)}")
        
        return filename
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    backup_torneo_42()
