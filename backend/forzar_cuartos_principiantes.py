"""
Fuerza el cuadro de cuartos de Principiantes con los cruces indicados.
(Se bajaron varias parejas, el cuadro queda con estos 8 parejas en este orden.)

Cuartos (orden de arriba a abajo):
  1. Jere vera / Malcos Calderon    vs  Victoria Cavallieri / Gula Saracho
  2. Exe Damian / Santi Mazza       vs  Fabian Alejandro / Franco Direnzo
  3. Dario Barrionuevo / Vega       vs  Sergio Panza / Seba Corzo
  4. Maxi Yelamo / Jorge Paz        vs  Carlos Fernandez / Leo Mena

Uso:
  python forzar_cuartos_principiantes.py [torneo_id] [categoria_id]
  python forzar_cuartos_principiantes.py 37 86 --list     # listar parejas y salir
  python forzar_cuartos_principiantes.py 37 86 --dry-run  # mostrar qué se asignaría
  python forzar_cuartos_principiantes.py 37 86 -y          # aplicar
Si no pasás categoria_id, se busca por nombre "Principiante".
"""
import argparse
import sys
import os
from typing import Optional

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from src.database.config import SessionLocal
from src.models.driveplus_models import Partido, PerfilUsuario
from src.models.torneo_models import TorneoPareja, TorneoCategoria

# Orden exacto del cuadro: 8 "identificadores" (apellido o nombre único) para encontrar cada pareja
# Partido 1: pareja1, pareja2; Partido 2: pareja1, pareja2; Partido 3: pareja1, pareja2; Partido 4: pareja1, pareja2
BUSCAR_PAREJAS = [
    "vera",       # 1.1 Jere vera - Marcos Calderon
    "saracho",    # 1.2 Victoria Cavallieri, Gula Saracho
    "damian",     # 2.1 Exe Damian - Santi Mazza
    "villafane",  # 2.2 Fabian Alejandro Villafañe - Franco Direnzo
    "barrionuevo", # 3.1 Dario Barrionuevo - Matias Vega
    "pansa",      # 3.2 Sergio Pansa - Seba Corzo
    "yelamo",     # 4.1 Maxi Yelamo - Jorge Paz
    "fernandez",  # 4.2 Carlos Fernandez - Leo Mena
]


def nombre_pareja(db, pareja: TorneoPareja) -> str:
    p1 = db.query(PerfilUsuario).filter(PerfilUsuario.id_usuario == pareja.jugador1_id).first()
    p2 = db.query(PerfilUsuario).filter(PerfilUsuario.id_usuario == pareja.jugador2_id).first()
    n1 = f"{p1.nombre} {p1.apellido}" if p1 else f"J{pareja.jugador1_id}"
    n2 = f"{p2.nombre} {p2.apellido}" if p2 else f"J{pareja.jugador2_id}"
    return f"{n1} / {n2}"


def normalizar(texto: str) -> str:
    """Normaliza texto removiendo acentos y convirtiendo a minúsculas"""
    import unicodedata
    texto = texto.lower()
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    return texto


def pareja_contiene(pareja: TorneoPareja, db, term: str) -> bool:
    p1 = db.query(PerfilUsuario).filter(PerfilUsuario.id_usuario == pareja.jugador1_id).first()
    p2 = db.query(PerfilUsuario).filter(PerfilUsuario.id_usuario == pareja.jugador2_id).first()
    t = normalizar(term)
    if p1 and (t in normalizar(p1.nombre or "") or t in normalizar(p1.apellido or "")):
        return True
    if p2 and (t in normalizar(p2.nombre or "") or t in normalizar(p2.apellido or "")):
        return True
    return False


def run(torneo_id: int, categoria_id: Optional[int], list_only: bool, dry_run: bool, confirmar: bool) -> bool:
    db = SessionLocal()
    try:
        if categoria_id is None:
            cat = db.query(TorneoCategoria).filter(
                TorneoCategoria.torneo_id == torneo_id,
                TorneoCategoria.nombre.ilike("%principiante%"),
            ).first()
            if not cat:
                print("❌ No se encontró categoría Principiante para ese torneo.")
                return False
            categoria_id = cat.id
            print(f"   Categoría Principiante: id={categoria_id}")

        parejas = db.query(TorneoPareja).filter(
            TorneoPareja.torneo_id == torneo_id,
            TorneoPareja.categoria_id == categoria_id,
            TorneoPareja.estado.in_(["inscripta", "confirmada"]),
        ).order_by(TorneoPareja.id).all()

        if list_only:
            print(f"\n=== Parejas en torneo {torneo_id} categoría {categoria_id} ({len(parejas)} total) ===\n")
            for p in parejas:
                print(f"  {p.id}: {nombre_pareja(db, p)}")
            return True

        # Resolver los 8 IDs por búsqueda
        ids = []
        for term in BUSCAR_PAREJAS:
            candidatos = [p for p in parejas if pareja_contiene(p, db, term)]
            if len(candidatos) != 1:
                print(f"❌ Búsqueda '{term}' devolvió {len(candidatos)} parejas (esperado 1). Ajustá BUSCAR_PAREJAS o pasá IDs a mano.")
                for c in candidatos:
                    print(f"     -> {c.id}: {nombre_pareja(db, c)}")
                return False
            ids.append(candidatos[0].id)

        partidos = db.query(Partido).filter(
            Partido.id_torneo == torneo_id,
            Partido.categoria_id == categoria_id,
            Partido.fase.in_(["cuartos", "4tos"]),
        ).order_by(Partido.numero_partido).all()

        if len(partidos) != 4:
            print(f"❌ Se esperaban 4 partidos de cuartos, hay {len(partidos)}.")
            return False

        print("\n=== Cuartos que se van a asignar ===\n")
        for i, p in enumerate(partidos):
            id1, id2 = ids[i * 2], ids[i * 2 + 1]
            n1 = next((nombre_pareja(db, x) for x in parejas if x.id == id1), f"Pareja {id1}")
            n2 = next((nombre_pareja(db, x) for x in parejas if x.id == id2), f"Pareja {id2}")
            print(f"  Partido {i + 1} (id_partido={p.id_partido}): {n1}  vs  {n2}")

        if dry_run:
            print("\n[DRY-RUN] No se modificó nada.")
            return True

        if confirmar:
            r = input("\n¿Aplicar estos cruces? (s/n): ").strip().lower()
            if r != "s":
                print("Cancelado.")
                return False

        for i, p in enumerate(partidos):
            p.pareja1_id = ids[i * 2]
            p.pareja2_id = ids[i * 2 + 1]
        db.commit()
        print("\n✅ Cuartos de principiantes actualizados. Recargá el bracket.")
        return True
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def main():
    ap = argparse.ArgumentParser(description="Forzar cuadro de cuartos Principiantes")
    ap.add_argument("torneo_id", nargs="?", type=int, default=37)
    ap.add_argument("categoria_id", nargs="?", type=int, default=None, help="Si no se pasa, se busca Principiante por nombre")
    ap.add_argument("--list", action="store_true", help="Solo listar parejas de la categoría")
    ap.add_argument("--dry-run", action="store_true", help="Mostrar asignación sin guardar")
    ap.add_argument("-y", "--yes", action="store_true", help="No pedir confirmación")
    args = ap.parse_args()

    print(f"Torneo={args.torneo_id}, Categoría={args.categoria_id or 'Principiante (por nombre)'}")
    ok = run(args.torneo_id, args.categoria_id, args.list, args.dry_run, confirmar=not args.yes)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
