"""Buscar usuarios reales recién creados y ver si coinciden con algún temp para migrar."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

# Usuarios reales recién creados (por username/email)
usernames = [
    'rodriguezmfacundom',
    'thotycrespo7',
    'noelmagi26',
    'miguelsoria380380',
    'flaviopalacio66ar',
    'cocomolinox7',
    'miguelantunez844',
    'morenanieto46',
]

with engine.connect() as conn:
    # 1. Buscar los usuarios reales
    print("=" * 80)
    print("USUARIOS REALES RECIÉN CREADOS")
    print("=" * 80)
    
    reales = []
    for uname in usernames:
        r = conn.execute(text("""
            SELECT u.id_usuario, u.email, p.nombre, p.apellido
            FROM usuarios u
            LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
            WHERE u.email = :email
        """), {"email": uname + "@gmail.com"}).fetchone()
        
        if r:
            reales.append((r[0], uname, r[1], r[2], r[3]))
            print(f"  ID {r[0]} | {uname} | {r[1]} | {r[2]} {r[3]}")
        else:
            print(f"  ❌ NO ENCONTRADO: {uname}")
    
    # 2. Buscar todos los temps
    print("\n" + "=" * 80)
    print("BUSCANDO COINCIDENCIAS CON TEMPS...")
    print("=" * 80)
    
    temps = conn.execute(text("""
        SELECT u.id_usuario, u.email, p.nombre, p.apellido
        FROM usuarios u
        LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        WHERE u.email LIKE '%@driveplus.temp'
        OR u.password_hash = 'temp_no_login'
        ORDER BY u.id_usuario
    """)).fetchall()
    
    print(f"\nTotal temps en sistema: {len(temps)}")
    
    for real in reales:
        real_id, real_uname, real_email, real_nombre, real_apellido = real
        if not real_nombre or not real_apellido:
            print(f"\n⚠️  {real_uname} (ID {real_id}) - Sin perfil, no se puede comparar")
            continue
        
        nombre_lower = real_nombre.lower().strip() if real_nombre else ''
        apellido_lower = real_apellido.lower().strip() if real_apellido else ''
        
        matches = []
        for t in temps:
            t_id, t_email, t_nombre, t_apellido = t
            t_nombre_l = (t_nombre or '').lower().strip()
            t_apellido_l = (t_apellido or '').lower().strip()
            
            # Match por nombre+apellido exacto
            if nombre_lower and apellido_lower and t_nombre_l == nombre_lower and t_apellido_l == apellido_lower:
                matches.append(('EXACTO', t))
            # Match parcial: apellido igual y nombre parecido
            elif apellido_lower and t_apellido_l == apellido_lower and nombre_lower and (
                nombre_lower in t_nombre_l or t_nombre_l in nombre_lower
            ):
                matches.append(('PARCIAL', t))
            # Match por apellido solo
            elif apellido_lower and t_apellido_l == apellido_lower:
                matches.append(('APELLIDO', t))
        
        if matches:
            print(f"\n🔍 {real_nombre} {real_apellido} (ID {real_id}, {real_uname})")
            for tipo, t in matches:
                t_id, t_email, t_nombre, t_apellido = t
                # Ver si el temp tiene partidos
                partidos = conn.execute(text("""
                    SELECT COUNT(*) FROM torneos_parejas tp
                    JOIN partidos p ON (p.pareja1_id = tp.id OR p.pareja2_id = tp.id)
                    WHERE tp.jugador1_id = :tid OR tp.jugador2_id = :tid
                """), {"tid": t_id}).scalar()
                
                historial = conn.execute(text("""
                    SELECT COUNT(*) FROM historial_rating WHERE id_usuario = :tid
                """), {"tid": t_id}).scalar()
                
                print(f"  [{tipo}] Temp ID {t_id} | {t_email} | {t_nombre} {t_apellido} | partidos={partidos} historial={historial}")
        else:
            print(f"\n✅ {real_nombre} {real_apellido} (ID {real_id}) - Sin temp coincidente")
