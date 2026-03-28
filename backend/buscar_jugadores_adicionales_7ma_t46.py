"""
Buscar jugadores adicionales para 7ma del torneo 46
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from sqlalchemy import create_engine, text
from thefuzz import fuzz

env_file = os.path.join(os.path.dirname(__file__), '.env.production')
DATABASE_URL = None
if os.path.exists(env_file):
    with open(env_file) as f:
        for line in f:
            if line.startswith('DATABASE_URL='):
                DATABASE_URL = line.split('=', 1)[1].strip().strip('"').strip("'")
                break

engine = create_engine(DATABASE_URL)

# Nuevos jugadores a buscar
JUGADORES = [
    "Millicay Federico",
    "Carrizo Exequiel",
    "Saldaño Dante",
    "Vásquez Alejandro",
    "Gonzales Renzo",
    "Letterucci Erik",
    "Diaz Exequiel",
    "Jofre Yamil",
    "Diaz leo",
    "Barroca Valentín",
]

def buscar_jugador(conn, nombre_completo):
    partes = nombre_completo.strip().split()
    if len(partes) < 2:
        return []
    
    # Probar nombre apellido
    nombre1, apellido1 = partes[0], ' '.join(partes[1:])
    # Probar apellido nombre (invertido)
    nombre2, apellido2 = ' '.join(partes[1:]), partes[0]
    
    # Buscar en TODOS los usuarios (incluir temps para ver si ya fueron creados)
    usuarios = conn.execute(text("""
        SELECT u.id_usuario, u.nombre_usuario, p.nombre, p.apellido, c.nombre as categoria, u.email
        FROM usuarios u
        LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        LEFT JOIN categorias c ON u.id_categoria = c.id_categoria
        ORDER BY u.id_usuario
    """)).fetchall()
    
    matches = []
    for u in usuarios:
        nombre_db = (u.nombre or '').lower().strip()
        apellido_db = (u.apellido or '').lower().strip()
        username_db = (u.nombre_usuario or '').lower().strip()
        
        # Comparar: nombre apellido vs DB
        score1 = fuzz.ratio(f"{nombre1} {apellido1}".lower(), f"{nombre_db} {apellido_db}")
        # Comparar: apellido nombre vs DB (invertido)
        score2 = fuzz.ratio(f"{nombre2} {apellido2}".lower(), f"{nombre_db} {apellido_db}")
        # Comparar con username
        score3 = fuzz.ratio(nombre_completo.lower(), username_db)
        
        max_score = max(score1, score2, score3)
        
        if max_score >= 75:  # Bajé el umbral a 75%
            invertido = " ⚠️ INVERTIDO" if score2 > score1 else ""
            es_temp = " [TEMP]" if '@driveplus.temp' in (u.email or '') else ""
            matches.append((u.id_usuario, nombre_db, apellido_db, u.categoria, max_score, invertido, es_temp))
    
    return sorted(matches, key=lambda x: x[4], reverse=True)

def main():
    with engine.connect() as conn:
        torneo = conn.execute(text("SELECT nombre FROM torneos WHERE id = 46")).fetchone()
        print(f"Torneo encontrado: {torneo.nombre}")
        
        for jugador in JUGADORES:
            print("=" * 80)
            print(f"🔍 Buscando: {jugador}")
            
            matches = buscar_jugador(conn, jugador)
            
            if matches:
                print(f"✅ Encontrados {len(matches)} match(es):")
                for m in matches[:5]:  # Mostrar top 5
                    print(f"- ID {m[0]}: {m[1].title()} {m[2].title()} ({m[3]}){m[5]}{m[6]} - {m[4]}%")
            else:
                print("❌ NO encontrado")

if __name__ == "__main__":
    main()
