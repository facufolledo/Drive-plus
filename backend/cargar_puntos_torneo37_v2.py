"""
Cargar puntos del torneo 37 al sistema de circuitos por fase alcanzada.
Lógica:
- Ganador de final = campeon (1000 pts)
- Perdedor de final = subcampeon (800 pts)
- Perdedor de semis = semis (600 pts)
- Perdedor de cuartos = cuartos (400 pts)
- Parejas que solo jugaron zona = zona (100 pts)
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()
from src.database.config import SessionLocal
from sqlalchemy import text

db = SessionLocal()

CIRCUITO_ID = 1  # zf
TORNEO_ID = 37

# Obtener config de puntos
puntos_config = {}
rows = db.execute(text("SELECT fase, puntos FROM circuito_puntos_fase WHERE circuito_id = :cid"), {"cid": CIRCUITO_ID}).fetchall()
for r in rows:
    puntos_config[r[0]] = r[1]
print(f"Config puntos: {puntos_config}")

# Obtener categorías del torneo
categorias = db.execute(text("SELECT id, nombre FROM torneo_categorias WHERE torneo_id = :tid"), {"tid": TORNEO_ID}).fetchall()

for cat_id, cat_nombre in categorias:
    print(f"\n{'='*60}")
    print(f"CATEGORÍA: {cat_nombre} (ID: {cat_id})")
    print(f"{'='*60}")
    
    # Obtener partidos de playoffs con ganador
    playoffs = db.execute(text("""
        SELECT id_partido, fase, pareja1_id, pareja2_id, ganador_pareja_id, estado
        FROM partidos
        WHERE id_torneo = :tid AND categoria_id = :cid AND fase IS NOT NULL AND fase != 'zona'
        ORDER BY CASE fase WHEN 'final' THEN 1 WHEN 'semis' THEN 2 WHEN '4tos' THEN 3 WHEN '8vos' THEN 4 END
    """), {"tid": TORNEO_ID, "cid": cat_id}).fetchall()
    
    # Si no hay playoffs confirmados, skip
    confirmados = [p for p in playoffs if p[5] == 'confirmado' and p[4] is not None]
    if not confirmados:
        print(f"  ⚠️ No hay playoffs confirmados, saltando...")
        continue
    
    # Determinar fase alcanzada por cada pareja
    fase_pareja = {}  # pareja_id -> fase_alcanzada
    
    for partido in confirmados:
        _, fase, p1, p2, ganador, _ = partido
        perdedor = p1 if ganador == p2 else p2
        
        if fase == 'final':
            fase_pareja[ganador] = 'campeon'
            fase_pareja[perdedor] = 'subcampeon'
        elif fase == 'semis':
            # El perdedor de semis tiene fase "semis"
            # El ganador sigue a final, se asigna ahí
            if perdedor not in fase_pareja:
                fase_pareja[perdedor] = 'semis'
        elif fase == '4tos':
            if perdedor not in fase_pareja:
                fase_pareja[perdedor] = 'cuartos'
        elif fase == '8vos':
            if perdedor not in fase_pareja:
                fase_pareja[perdedor] = '8vos'
        elif fase == '16avos':
            if perdedor not in fase_pareja:
                fase_pareja[perdedor] = '16avos'
    
    # Todas las parejas de esta categoría
    todas_parejas = db.execute(text("""
        SELECT id, jugador1_id, jugador2_id FROM torneos_parejas
        WHERE torneo_id = :tid AND categoria_id = :cid AND estado != 'baja'
    """), {"tid": TORNEO_ID, "cid": cat_id}).fetchall()
    
    # Parejas que no están en playoffs = zona
    for pareja_id, j1, j2 in todas_parejas:
        if pareja_id not in fase_pareja:
            fase_pareja[pareja_id] = 'zona'
    
    # Insertar puntos para cada jugador
    for pareja_id, j1, j2 in todas_parejas:
        fase = fase_pareja.get(pareja_id, 'zona')
        pts = puntos_config.get(fase, 0)
        
        for jugador_id in [j1, j2]:
            # Upsert
            db.execute(text("""
                INSERT INTO circuito_puntos_jugador (circuito_id, torneo_id, categoria_id, usuario_id, fase_alcanzada, puntos)
                VALUES (:cir, :tor, :cat, :usr, :fase, :pts)
                ON CONFLICT (circuito_id, torneo_id, categoria_id, usuario_id) 
                DO UPDATE SET fase_alcanzada = EXCLUDED.fase_alcanzada, puntos = EXCLUDED.puntos
            """), {"cir": CIRCUITO_ID, "tor": TORNEO_ID, "cat": cat_id, "usr": jugador_id, "fase": fase, "pts": pts})
        
        # Obtener nombres
        nombres = db.execute(text("""
            SELECT COALESCE(p.nombre || ' ' || p.apellido, u.nombre_usuario)
            FROM usuarios u LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
            WHERE u.id_usuario IN (:j1, :j2)
        """), {"j1": j1, "j2": j2}).fetchall()
        n1 = nombres[0][0] if nombres else '?'
        n2 = nombres[1][0] if len(nombres) > 1 else '?'
        print(f"  Pareja {pareja_id} ({n1} / {n2}): {fase} = {pts} pts")

db.commit()
print(f"\n✅ Puntos cargados exitosamente para torneo {TORNEO_ID}")

# Verificación
total = db.execute(text("""
    SELECT COUNT(*) FROM circuito_puntos_jugador WHERE circuito_id = :cid AND torneo_id = :tid
"""), {"cid": CIRCUITO_ID, "tid": TORNEO_ID}).scalar()
print(f"Total registros insertados: {total}")

db.close()
