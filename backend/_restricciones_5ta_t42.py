"""Cargar restricciones horarias para parejas de 5ta T42
Formato: disponibilidad_horaria = [{dias: [], horaInicio, horaFin}]
Representa los horarios en que PUEDEN jugar.

Parejas y horarios:
666: Calderón/Villegas - viernes después de 22:30, sábado después de 12
667: Oliva/Peñaloza - viernes antes de 19, sábado antes de 15:30 y después de 19:30
668: Romero Isaías/Romero Martín - sábado después de 13
669: Castro/Aguilar - viernes después de 21, sábado después de 13:30
670: Brizuela/Casas - viernes después de 18
671: Nieto/Tello - viernes después de 17 antes de 20, sábado después de 18
672: Díaz/Sosa - viernes después de 18, sábado antes de 20
673: Nani/Abrego - viernes después de 20:30
674: Loto/Navarro - sábado después de 12
675: Farran/Montiel - sin restricciones
676: Ruarte/Romero Gastón - viernes no pueden, sábado libre
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
engine = create_engine(os.getenv("DATABASE_URL"))

# Restricciones por pareja_id
# Cada entrada es la disponibilidad (cuándo PUEDEN jugar)
restricciones = {
    666: [  # Calderón/Villegas: vie +22:30, sáb +12
        {"dias": ["viernes"], "horaInicio": "22:30", "horaFin": "23:30"},
        {"dias": ["sabado"], "horaInicio": "12:00", "horaFin": "23:30"},
    ],
    667: [  # Oliva/Peñaloza: vie antes 19, sáb antes 15:30 y después 19:30
        {"dias": ["viernes"], "horaInicio": "15:00", "horaFin": "19:00"},
        {"dias": ["sabado"], "horaInicio": "09:00", "horaFin": "15:30"},
        {"dias": ["sabado"], "horaInicio": "19:30", "horaFin": "23:30"},
    ],
    668: [  # Romero/Romero: sáb +13
        {"dias": ["sabado"], "horaInicio": "13:00", "horaFin": "23:30"},
    ],
    669: [  # Castro/Aguilar: vie +21, sáb +13:30
        {"dias": ["viernes"], "horaInicio": "21:00", "horaFin": "23:30"},
        {"dias": ["sabado"], "horaInicio": "13:30", "horaFin": "23:30"},
    ],
    670: [  # Brizuela/Casas: vie +18
        {"dias": ["viernes"], "horaInicio": "18:00", "horaFin": "23:30"},
    ],
    671: [  # Nieto/Tello: vie +17 antes 20, sáb +18
        {"dias": ["viernes"], "horaInicio": "17:00", "horaFin": "20:00"},
        {"dias": ["sabado"], "horaInicio": "18:00", "horaFin": "23:30"},
    ],
    672: [  # Díaz/Sosa: vie +18, sáb antes 20
        {"dias": ["viernes"], "horaInicio": "18:00", "horaFin": "23:30"},
        {"dias": ["sabado"], "horaInicio": "09:00", "horaFin": "20:00"},
    ],
    673: [  # Nani/Abrego: vie +20:30
        {"dias": ["viernes"], "horaInicio": "20:30", "horaFin": "23:30"},
    ],
    674: [  # Loto/Navarro: sáb +12
        {"dias": ["sabado"], "horaInicio": "12:00", "horaFin": "23:30"},
    ],
    675: None,  # Farran/Montiel: sin restricciones (pueden siempre)
    676: [  # Ruarte/Romero: viernes no pueden, sábado libre
        {"dias": ["sabado"], "horaInicio": "09:00", "horaFin": "23:30"},
    ],
}

with engine.connect() as conn:
    for pareja_id, restr in restricciones.items():
        if restr is None:
            # Sin restricciones = disponible siempre
            restr_val = [
                {"dias": ["viernes"], "horaInicio": "15:00", "horaFin": "23:30"},
                {"dias": ["sabado"], "horaInicio": "09:00", "horaFin": "23:30"},
                {"dias": ["domingo"], "horaInicio": "09:00", "horaFin": "23:30"},
            ]
        else:
            restr_val = restr
        
        conn.execute(
            text("UPDATE torneos_parejas SET disponibilidad_horaria = CAST(:r AS jsonb) WHERE id = :pid"),
            {"r": json.dumps(restr_val), "pid": pareja_id}
        )
        print(f"  Pareja {pareja_id}: {json.dumps(restr_val, ensure_ascii=False)}")
    
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
        disp = "✅" if r[3] else "❌ SIN RESTRICCIONES"
        print(f"  {r[0]}: {r[1]} / {r[2]} -> {disp}")
    
    print("\n✅ Restricciones cargadas!")
