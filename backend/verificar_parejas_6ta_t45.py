#!/usr/bin/env python3
"""
Verificar qué parejas de 6ta faltan en el torneo 45.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)

TORNEO_ID = 45
CATEGORIA_NOMBRE = "6ta"

# Parejas esperadas según la imagen
PAREJAS_ESPERADAS = [
    "Tejada - Corzo",
    "Ortiz - Suarez",
    "Nieto - Nieto",
    "Molina - Molina",
    "Bazan - Rodriguez",
    "Stepanios - Fuentes",
    "Biset - Ocampo",  # FILA 8
    "Gurgone - Palacio",
    "Oliva - Leyes",
    "Romero - Romero",
    "Ontivero - Ontivero",
    "Cordero - Perez",
    "Sanchez - Arrebola",
    "Ceballo - Pamelin",
    "Cejas - Redes",
    "Llabante - Cordoba",
    "Santillan - Paredes",
    "Lobos - Santander",
    "Ferreyra - Bustos",
    "Vega - Martin",
    "Nis - Fuentes",
    "Carrizo - Juarez",
    "Salazar - Charazo",
    "Rosa - Estrada",
]

def verificar():
    s = Session()
    try:
        # Obtener categoría
        cat = s.execute(text("""
            SELECT id FROM torneo_categorias 
            WHERE torneo_id = :t AND nombre = :n
        """), {"t": TORNEO_ID, "n": CATEGORIA_NOMBRE}).fetchone()
        
        if not cat:
            print(f"❌ Categoría {CATEGORIA_NOMBRE} no encontrada")
            return
        
        cat_id = cat[0]
        
        # Obtener parejas inscritas
        parejas = s.execute(text("""
            SELECT 
                tp.id,
                u1.nombre_usuario as j1_username,
                pf1.nombre as j1_nombre,
                pf1.apellido as j1_apellido,
                u2.nombre_usuario as j2_username,
                pf2.nombre as j2_nombre,
                pf2.apellido as j2_apellido
            FROM torneos_parejas tp
            JOIN usuarios u1 ON tp.jugador1_id = u1.id_usuario
            JOIN usuarios u2 ON tp.jugador2_id = u2.id_usuario
            LEFT JOIN perfil_usuarios pf1 ON u1.id_usuario = pf1.id_usuario
            LEFT JOIN perfil_usuarios pf2 ON u2.id_usuario = pf2.id_usuario
            WHERE tp.torneo_id = :t AND tp.categoria_id = :c
            ORDER BY tp.id
        """), {"t": TORNEO_ID, "c": cat_id}).fetchall()
        
        print(f"\n{'='*70}")
        print(f"PAREJAS INSCRITAS EN 6TA - TORNEO {TORNEO_ID}")
        print(f"{'='*70}")
        print(f"Total: {len(parejas)} parejas\n")
        
        for p in parejas:
            nombre1 = f"{p.j1_nombre or ''} {p.j1_apellido or ''}".strip() or p.j1_username
            nombre2 = f"{p.j2_nombre or ''} {p.j2_apellido or ''}".strip() or p.j2_username
            print(f"  {p.id:3d}. {nombre1} - {nombre2}")
        
        print(f"\n{'='*70}")
        print(f"ESPERADAS: {len(PAREJAS_ESPERADAS)} parejas")
        print(f"INSCRITAS: {len(parejas)} parejas")
        print(f"FALTAN: {len(PAREJAS_ESPERADAS) - len(parejas)} parejas")
        print(f"{'='*70}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    verificar()
