"""
Migrar cuenta temporal de Rodrigo Saad a su cuenta real
- Transferir todas las parejas, partidos, historial de rating
- Eliminar cuenta temporal
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from sqlalchemy.orm import Session
from src.database.config import get_db
from src.models.driveplus_models import Usuario, Partido, PartidoJugador, HistorialRating, PerfilUsuario
from src.models.torneo_models import TorneoPareja

load_dotenv()

def migrar_rodrigo_saad():
    """Migra la cuenta temporal de Rodrigo Saad a su cuenta real"""
    db = next(get_db())
    
    try:
        print("\n" + "="*80)
        print("🔄 MIGRACIÓN: RODRIGO SAAD - CUENTA TEMPORAL → CUENTA REAL")
        print("="*80 + "\n")
        
        # 1. Identificar las cuentas directamente
        print("🔍 Identificando cuentas...")
        
        cuenta_temporal_id = 176  # rodrisaad (temporal)
        cuenta_real_id = 223  # rodrisaad88 (real)
        
        cuenta_temporal = db.query(Usuario).filter(Usuario.id_usuario == cuenta_temporal_id).first()
        cuenta_real = db.query(Usuario).filter(Usuario.id_usuario == cuenta_real_id).first()
        
        if not cuenta_temporal or not cuenta_real:
            print("❌ No se encontraron las cuentas especificadas")
            return
        
        print("\n" + "="*80)
        print("📌 IDENTIFICACIÓN DE CUENTAS")
        print("="*80)
        print(f"\n🔴 CUENTA TEMPORAL (a eliminar):")
        print(f"   ID: {cuenta_temporal.id_usuario}")
        print(f"   Username: {cuenta_temporal.nombre_usuario}")
        print(f"   Email: {cuenta_temporal.email}")
        print(f"   Rating: {cuenta_temporal.rating}")
        print(f"   Partidos: {cuenta_temporal.partidos_jugados}")
        
        print(f"\n🟢 CUENTA REAL (destino):")
        print(f"   ID: {cuenta_real.id_usuario}")
        print(f"   Username: {cuenta_real.nombre_usuario}")
        print(f"   Email: {cuenta_real.email}")
        print(f"   Rating: {cuenta_real.rating}")
        print(f"   Partidos: {cuenta_real.partidos_jugados}")
        
        print("\n⚠️  ¿Es correcta esta identificación? (Verifica antes de continuar)")
        print("   Si no es correcta, cancela el script y ajusta la lógica.")
        
        # 2. Migrar parejas de torneos
        print("\n" + "="*80)
        print("🔄 MIGRANDO DATOS")
        print("="*80)
        
        print("\n1️⃣ Migrando parejas de torneos...")
        parejas_temporal = db.query(TorneoPareja).filter(
            (TorneoPareja.jugador1_id == cuenta_temporal.id_usuario) |
            (TorneoPareja.jugador2_id == cuenta_temporal.id_usuario)
        ).all()
        
        print(f"   Parejas encontradas: {len(parejas_temporal)}")
        
        for pareja in parejas_temporal:
            if pareja.jugador1_id == cuenta_temporal.id_usuario:
                print(f"   Pareja {pareja.id}: Actualizando jugador1_id")
                pareja.jugador1_id = cuenta_real.id_usuario
            if pareja.jugador2_id == cuenta_temporal.id_usuario:
                print(f"   Pareja {pareja.id}: Actualizando jugador2_id")
                pareja.jugador2_id = cuenta_real.id_usuario
        
        # 3. Migrar partidos (partido_jugadores)
        print("\n2️⃣ Migrando partidos...")
        partidos_jugador = db.query(PartidoJugador).filter(
            PartidoJugador.id_usuario == cuenta_temporal.id_usuario
        ).all()
        
        print(f"   Registros de partidos encontrados: {len(partidos_jugador)}")
        
        for pj in partidos_jugador:
            print(f"   Partido {pj.id_partido}: Actualizando jugador")
            pj.id_usuario = cuenta_real.id_usuario
        
        # 4. Migrar historial de rating
        print("\n3️⃣ Migrando historial de rating...")
        historial = db.query(HistorialRating).filter(
            HistorialRating.id_usuario == cuenta_temporal.id_usuario
        ).all()
        
        print(f"   Registros de historial encontrados: {len(historial)}")
        
        for h in historial:
            print(f"   Historial {h.id_historial}: Actualizando usuario")
            h.id_usuario = cuenta_real.id_usuario
        
        # 5. Transferir rating y estadísticas
        print("\n4️⃣ Transfiriendo rating y estadísticas...")
        print(f"   Rating temporal: {cuenta_temporal.rating}")
        print(f"   Rating real: {cuenta_real.rating}")
        
        # Usar el rating de la cuenta temporal si tiene partidos jugados
        if cuenta_temporal.partidos_jugados > 0:
            print(f"   → Usando rating de cuenta temporal: {cuenta_temporal.rating}")
            cuenta_real.rating = cuenta_temporal.rating
            cuenta_real.partidos_jugados = cuenta_temporal.partidos_jugados
        
        # 6. Eliminar cuenta temporal
        print("\n5️⃣ Eliminando cuenta temporal...")
        
        # Eliminar perfil si existe
        perfil_temporal = db.query(PerfilUsuario).filter(
            PerfilUsuario.id_usuario == cuenta_temporal.id_usuario
        ).first()
        if perfil_temporal:
            print(f"   Eliminando perfil de usuario temporal")
            db.delete(perfil_temporal)
        
        # Eliminar usuario temporal
        print(f"   Eliminando usuario temporal (ID: {cuenta_temporal.id_usuario})")
        db.delete(cuenta_temporal)
        
        # Commit de todos los cambios
        db.commit()
        
        print("\n" + "="*80)
        print("✅ MIGRACIÓN COMPLETADA")
        print("="*80)
        print(f"\n📊 Resumen:")
        print(f"   • Parejas migradas: {len(parejas_temporal)}")
        print(f"   • Partidos migrados: {len(partidos_jugador)}")
        print(f"   • Historial migrado: {len(historial)}")
        print(f"   • Rating final: {cuenta_real.rating}")
        print(f"   • Partidos jugados: {cuenta_real.partidos_jugados}")
        print(f"\n🟢 Cuenta activa: {cuenta_real.nombre_usuario} (ID: {cuenta_real.id_usuario})")
        print(f"🔴 Cuenta eliminada: {cuenta_temporal.nombre_usuario} (ID: {cuenta_temporal.id_usuario})")
        print("\n" + "="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("\n⚠️  ADVERTENCIA: Este script migrará todos los datos de la cuenta temporal a la real")
    print("y eliminará la cuenta temporal. Verifica que la identificación sea correcta.")
    print("\n¿Deseas continuar? (escribe 'SI' para confirmar)")
    
    # En producción, descomentar esta línea
    # confirmacion = input("> ")
    # if confirmacion.upper() == "SI":
    migrar_rodrigo_saad()
    # else:
    #     print("Operación cancelada")
