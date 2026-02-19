import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
load_dotenv()
e = create_engine(os.getenv("DATABASE_URL"))
s = sessionmaker(bind=e)()

for tid in [39, 40]:
    print(f"Limpiando torneo {tid}...")
    s.execute(text("DELETE FROM torneos_parejas WHERE torneo_id = :t"), {"t": tid})
    s.execute(text("DELETE FROM torneo_canchas WHERE torneo_id = :t"), {"t": tid})
    s.execute(text("DELETE FROM torneo_categorias WHERE torneo_id = :t"), {"t": tid})
    s.execute(text("DELETE FROM torneos WHERE id = :t"), {"t": tid})
    s.commit()
    print(f"  ✅ Torneo {tid} eliminado")

# Eliminar usuarios demo en batch
print("Eliminando usuarios demo...")
s.execute(text("DELETE FROM perfil_usuarios WHERE id_usuario IN (SELECT id_usuario FROM usuarios WHERE email LIKE 'demo%@demo.com')"))
r = s.execute(text("DELETE FROM usuarios WHERE email LIKE 'demo%@demo.com'"))
s.commit()
print(f"  ✅ {r.rowcount} usuarios eliminados")
s.close()
print("✅ Listo")
