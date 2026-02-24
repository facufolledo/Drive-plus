"""
Migración completa:
1. Buscar temp de Lucas (574) - perfil dice "Lucas Mercado Luna"
2. Migrar Lucas si hay temp
3. Arreglar partidos_jugados de todos los migrados (568, 562, 564)
4. Borrar temps ya migrados
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
engine = create_engine(os.getenv("DATABASE_URL"))

def contar_partidos_reales(conn, uid):
    """Contar partidos confirmados y ganados de un usuario"""
    parejas = conn.execute(text("""
        SELECT id FROM torneos_parejas WHERE jugador1_id = :uid OR jugador2_id = :uid
    """), {"uid": uid}).fetchall()
    pareja_ids = [p[0] for p in parejas]
    if not pareja_ids:
        return 0, 0
    
    placeholders = ','.join(str(pid) for pid in pareja_ids)
    partidos = conn.execute(text(f"""
        SELECT id_partido, pareja1_id, pareja2_id, ganador_pareja_id
        FROM partidos
        WHERE estado = 'confirmado'
          AND (pareja1_id IN ({placeholders}) OR pareja2_id IN ({placeholders}))
    """)).fetchall()
    
    total = len(partidos)
    ganados = sum(1 for p in partidos if p[3] in pareja_ids)
    return total, ganados

with engine.connect() as conn:
    # ============ 1. BUSCAR TEMP DE LUCAS 574 ============
    print("=" * 60)
    print("1. BUSCAR TEMP DE LUCAS (574) - perfil: Lucas Mercado Luna")
    print("=" * 60)
    
    # Buscar por "Mercado" o "Luna"
    temps = conn.execute(text("""
        SELECT u.id_usuario, u.nombre_usuario, u.rating, u.id_categoria, u.partidos_jugados,
               p.nombre, p.apellido
        FROM usuarios u
        LEFT JOIN perfil_usuarios p ON p.id_usuario = u.id_usuario
        WHERE u.password_hash = 'temp_no_login'
          AND (LOWER(p.apellido) LIKE '%mercado%' OR LOWER(p.apellido) LIKE '%luna%'
               OR (LOWER(p.nombre) LIKE '%lucas%' AND (LOWER(p.apellido) LIKE '%mercado%' OR LOWER(p.apellido) LIKE '%luna%')))
    """)).fetchall()
    
    temp_lucas = None
    for t in temps:
        print(f"  TEMP {t[0]}: {t[5]} {t[6]}, user={t[1]}, rating={t[2]}, cat={t[3]}, pj={t[4]}")
        parejas = conn.execute(text("""
            SELECT tp.id, tp.jugador1_id, tp.jugador2_id, tp.torneo_id
            FROM torneos_parejas tp WHERE tp.jugador1_id = :tid OR tp.jugador2_id = :tid
        """), {"tid": t[0]}).fetchall()
        for pa in parejas:
            print(f"    Pareja {pa[0]}: j1={pa[1]} j2={pa[2]} torneo={pa[3]}")
        total, ganados = contar_partidos_reales(conn, t[0])
        print(f"    Partidos confirmados: {total}, ganados: {ganados}")
        temp_lucas = t[0]
    
    if not temps:
        # Buscar también por "apostolo" por si acaso
        temps2 = conn.execute(text("""
            SELECT u.id_usuario, u.nombre_usuario, u.rating, u.id_categoria,
                   p.nombre, p.apellido
            FROM usuarios u
            LEFT JOIN perfil_usuarios p ON p.id_usuario = u.id_usuario
            WHERE u.password_hash = 'temp_no_login'
              AND (LOWER(p.apellido) LIKE '%apostolo%' OR LOWER(u.nombre_usuario) LIKE '%apostolo%'
                   OR LOWER(u.nombre_usuario) LIKE '%mercado%' OR LOWER(u.nombre_usuario) LIKE '%luna%')
        """)).fetchall()
        for t in temps2:
            print(f"  TEMP {t[0]}: {t[4]} {t[5]}, user={t[1]}, rating={t[2]}, cat={t[3]}")
        if not temps2:
            print("  No se encontró temp para Lucas")

    # ============ 2. MIGRAR LUCAS SI HAY TEMP ============
    if temp_lucas:
        print(f"\n  Migrando temp {temp_lucas} -> real 574...")
        temp_info = conn.execute(text("""
            SELECT rating, id_categoria FROM usuarios WHERE id_usuario = :tid
        """), {"tid": temp_lucas}).fetchone()
        
        # Copiar rating y categoría
        conn.execute(text("""
            UPDATE usuarios SET rating = :rating, id_categoria = :cat WHERE id_usuario = 574
        """), {"rating": temp_info[0], "cat": temp_info[1]})
        
        # Cambiar jugador en parejas
        updated1 = conn.execute(text("""
            UPDATE torneos_parejas SET jugador1_id = 574 WHERE jugador1_id = :tid
        """), {"tid": temp_lucas}).rowcount
        updated2 = conn.execute(text("""
            UPDATE torneos_parejas SET jugador2_id = 574 WHERE jugador2_id = :tid
        """), {"tid": temp_lucas}).rowcount
        print(f"  ✅ Rating/cat copiados, parejas actualizadas: {updated1 + updated2}")
    else:
        print("\n  No hay temp para migrar Lucas")

    # ============ 3. ACTUALIZAR partidos_jugados DE TODOS ============
    print("\n" + "=" * 60)
    print("3. ACTUALIZAR partidos_jugados")
    print("=" * 60)
    
    for uid, nombre in [(568, "Benjamin Hrellac"), (562, "Juan Magi"), (564, "Flavio Palacio"), (574, "Lucas")]:
        total, ganados = contar_partidos_reales(conn, uid)
        conn.execute(text("""
            UPDATE usuarios SET partidos_jugados = :total WHERE id_usuario = :uid
        """), {"total": total, "uid": uid})
        print(f"  {nombre} ({uid}): partidos_jugados = {total} (ganados: {ganados})")

    # ============ 4. BORRAR TEMPS YA MIGRADOS ============
    print("\n" + "=" * 60)
    print("4. BORRAR TEMPS MIGRADOS")
    print("=" * 60)
    
    # Temps a borrar: 502 (Benjamin), 511 (Juan Magi), 542 (Flavio Palacio), y temp_lucas si existe
    temps_borrar = [502, 511, 542]
    if temp_lucas:
        temps_borrar.append(temp_lucas)
    
    for tid in temps_borrar:
        # Verificar que no tenga parejas activas
        parejas = conn.execute(text("""
            SELECT COUNT(*) FROM torneos_parejas WHERE jugador1_id = :tid OR jugador2_id = :tid
        """), {"tid": tid}).scalar()
        
        if parejas > 0:
            print(f"  ⚠️ TEMP {tid}: todavía tiene {parejas} parejas, NO se borra")
            continue
        
        # Borrar perfil
        conn.execute(text("DELETE FROM perfil_usuarios WHERE id_usuario = :tid"), {"tid": tid})
        # Borrar historial rating
        conn.execute(text("DELETE FROM historial_rating WHERE id_usuario = :tid"), {"tid": tid})
        # Borrar usuario
        deleted = conn.execute(text("DELETE FROM usuarios WHERE id_usuario = :tid AND password_hash = 'temp_no_login'"), {"tid": tid}).rowcount
        if deleted:
            print(f"  ✅ TEMP {tid}: borrado (perfil + historial + usuario)")
        else:
            print(f"  ℹ️ TEMP {tid}: no encontrado o no es temp")
    
    conn.commit()
    
    # ============ VERIFICACIÓN FINAL ============
    print("\n" + "=" * 60)
    print("VERIFICACIÓN FINAL")
    print("=" * 60)
    
    for uid, nombre in [(568, "Benjamin Hrellac"), (562, "Juan Magi"), (564, "Flavio Palacio"), (574, "Lucas")]:
        u = conn.execute(text("""
            SELECT u.id_usuario, u.rating, u.id_categoria, u.partidos_jugados, p.nombre, p.apellido
            FROM usuarios u
            LEFT JOIN perfil_usuarios p ON p.id_usuario = u.id_usuario
            WHERE u.id_usuario = :uid
        """), {"uid": uid}).fetchone()
        parejas = conn.execute(text("""
            SELECT tp.id, tp.jugador1_id, tp.jugador2_id, tp.torneo_id
            FROM torneos_parejas tp WHERE tp.jugador1_id = :uid OR tp.jugador2_id = :uid
        """), {"uid": uid}).fetchall()
        print(f"  {nombre} ({uid}): {u[4]} {u[5]}, rating={u[1]}, cat={u[2]}, pj={u[3]}, parejas={len(parejas)}")
    
    # Verificar que temps ya no existen
    for tid in temps_borrar:
        exists = conn.execute(text("SELECT COUNT(*) FROM usuarios WHERE id_usuario = :tid"), {"tid": tid}).scalar()
        print(f"  Temp {tid}: {'EXISTE AÚN ⚠️' if exists else 'BORRADO ✅'}")
