"""Corregir restricciones horarias para parejas de 5ta T42
El campo disponibilidad_horaria guarda RESTRICCIONES = horarios en que NO pueden jugar.

Horarios del torneo: vie 15:00-23:30, sáb 09:00-23:30

Parejas y lo que me pasaron (+ = después de):
666: Calderón/Villegas - vie +22:30, sáb +12
     -> NO pueden: vie 15:00-22:30, sáb 09:00-12:00
667: Oliva/Peñaloza - vie antes de 19, sáb antes 15:30 y después 19:30
     -> NO pueden: vie 19:00-23:30, sáb 15:30-19:30
668: Romero/Romero - sáb después de 13
     -> NO pueden: vie todo, sáb 09:00-13:00
669: Castro/Aguilar - vie +21, sáb +13:30
     -> NO pueden: vie 15:00-21:00, sáb 09:00-13:30
670: Brizuela/Casas - vie +18
     -> NO pueden: vie 15:00-18:00 (solo mencionó viernes, sáb sin dato = no puede?)
     -> Asumo solo viernes disponible +18, sin sábado mencionado
     -> NO pueden: vie 15:00-18:00
671: Nieto/Tello - vie +17 antes de 20, sáb +18
     -> Pueden: vie 17:00-20:00, sáb 18:00-23:30
     -> NO pueden: vie 15:00-17:00, vie 20:00-23:30, sáb 09:00-18:00
672: Díaz/Sosa - vie +18, sáb antes de 20
     -> Pueden: vie 18:00-23:30, sáb 09:00-20:00
     -> NO pueden: vie 15:00-18:00, sáb 20:00-23:30
673: Nani/Abrego - vie +20:30
     -> NO pueden: vie 15:00-20:30 (solo mencionó viernes)
674: Loto/Navarro - sáb +12
     -> NO pueden: vie todo, sáb 09:00-12:00
     -> Asumo viernes no pueden (no mencionado)
675: Farran/Montiel - sin restricciones
     -> Sin restricciones (vacío)
676: Ruarte/Romero - vie no pueden, sáb libre
     -> NO pueden: vie todo
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
engine = create_engine(os.getenv("DATABASE_URL"))

restricciones = {
    666: [  # Calderón/Villegas: pueden vie +22:30, sáb +12
        # NO pueden: vie 15:00-22:30, sáb 09:00-12:00
        {"dias": ["viernes"], "horaInicio": "15:00", "horaFin": "22:30"},
        {"dias": ["sabado"], "horaInicio": "09:00", "horaFin": "12:00"},
    ],
    667: [  # Oliva/Peñaloza: pueden vie antes 19, sáb antes 15:30 y +19:30
        # NO pueden: vie 19:00-23:30, sáb 15:30-19:30
        {"dias": ["viernes"], "horaInicio": "19:00", "horaFin": "23:30"},
        {"dias": ["sabado"], "horaInicio": "15:30", "horaFin": "19:30"},
    ],
    668: [  # Romero/Romero: pueden sáb +13 (viernes no mencionado = no pueden)
        # NO pueden: vie todo, sáb 09:00-13:00
        {"dias": ["viernes"], "horaInicio": "15:00", "horaFin": "23:30"},
        {"dias": ["sabado"], "horaInicio": "09:00", "horaFin": "13:00"},
    ],
    669: [  # Castro/Aguilar: pueden vie +21, sáb +13:30
        # NO pueden: vie 15:00-21:00, sáb 09:00-13:30
        {"dias": ["viernes"], "horaInicio": "15:00", "horaFin": "21:00"},
        {"dias": ["sabado"], "horaInicio": "09:00", "horaFin": "13:30"},
    ],
    670: [  # Brizuela/Casas: pueden vie +18
        # NO pueden: vie 15:00-18:00
        {"dias": ["viernes"], "horaInicio": "15:00", "horaFin": "18:00"},
    ],
    671: [  # Nieto/Tello: pueden vie 17-20, sáb +18
        # NO pueden: vie 15:00-17:00, vie 20:00-23:30, sáb 09:00-18:00
        {"dias": ["viernes"], "horaInicio": "15:00", "horaFin": "17:00"},
        {"dias": ["viernes"], "horaInicio": "20:00", "horaFin": "23:30"},
        {"dias": ["sabado"], "horaInicio": "09:00", "horaFin": "18:00"},
    ],
    672: [  # Díaz/Sosa: pueden vie +18, sáb antes 20
        # NO pueden: vie 15:00-18:00, sáb 20:00-23:30
        {"dias": ["viernes"], "horaInicio": "15:00", "horaFin": "18:00"},
        {"dias": ["sabado"], "horaInicio": "20:00", "horaFin": "23:30"},
    ],
    673: [  # Nani/Abrego: pueden vie +20:30
        # NO pueden: vie 15:00-20:30
        {"dias": ["viernes"], "horaInicio": "15:00", "horaFin": "20:30"},
    ],
    674: [  # Loto/Navarro: pueden sáb +12 (viernes no mencionado)
        # NO pueden: vie todo, sáb 09:00-12:00
        {"dias": ["viernes"], "horaInicio": "15:00", "horaFin": "23:30"},
        {"dias": ["sabado"], "horaInicio": "09:00", "horaFin": "12:00"},
    ],
    675: [],  # Farran/Montiel: sin restricciones
    676: [  # Ruarte/Romero: vie no pueden, sáb libre
        # NO pueden: vie todo
        {"dias": ["viernes"], "horaInicio": "15:00", "horaFin": "23:30"},
    ],
}

with engine.connect() as conn:
    for pareja_id, restr in restricciones.items():
        restr_val = restr if restr else None
        if restr_val is not None:
            conn.execute(
                text("UPDATE torneos_parejas SET disponibilidad_horaria = CAST(:r AS jsonb) WHERE id = :pid"),
                {"r": json.dumps(restr_val), "pid": pareja_id}
            )
        else:
            conn.execute(
                text("UPDATE torneos_parejas SET disponibilidad_horaria = NULL WHERE id = :pid"),
                {"pid": pareja_id}
            )
        nombre = f"Pareja {pareja_id}"
        if restr_val:
            print(f"  {nombre}: {len(restr_val)} restricciones")
        else:
            print(f"  {nombre}: sin restricciones")
    
    conn.commit()
    
    # Verificar
    print("\n=== VERIFICACIÓN ===")
    rows = conn.execute(text("""
        SELECT tp.id, 
               p1.nombre || ' ' || p1.apellido,
               p2.nombre || ' ' || p2.apellido,
               tp.disponibilidad_horaria
        FROM torneos_parejas tp
        LEFT JOIN perfil_usuarios p1 ON p1.id_usuario = tp.jugador1_id
        LEFT JOIN perfil_usuarios p2 ON p2.id_usuario = tp.jugador2_id
        WHERE tp.torneo_id = 42 AND tp.categoria_id = 108
        ORDER BY tp.id
    """)).fetchall()
    for r in rows:
        restr = r[3]
        if restr:
            # Mostrar resumen legible
            partes = []
            for fr in restr:
                dias = ', '.join(fr['dias'])
                partes.append(f"{dias} {fr['horaInicio']}-{fr['horaFin']}")
            print(f"  {r[0]}: {r[1]} / {r[2]}")
            print(f"       NO pueden: {' | '.join(partes)}")
        else:
            print(f"  {r[0]}: {r[1]} / {r[2]} -> SIN RESTRICCIONES")
    
    print("\n✅ Restricciones corregidas!")
