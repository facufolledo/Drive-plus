"""Verificar estructura de tabla torneo_categorias"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from sqlalchemy import create_engine, text

env_file = os.path.join(os.path.dirname(__file__), '.env.production')
DATABASE_URL = None
if os.path.exists(env_file):
    with open(env_file) as f:
        for line in f:
            if line.startswith('DATABASE_URL='):
                DATABASE_URL = line.split('=', 1)[1].strip().strip('"').strip("'")
                break

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'torneo_categorias' 
        ORDER BY ordinal_position
    """))
    
    print("Columnas de torneo_categorias:")
    for row in result:
        print(f"  - {row[0]}: {row[1]}")
    
    print("\nCategorías del torneo 46:")
    cats = conn.execute(text("""
        SELECT * FROM torneo_categorias WHERE torneo_id = 46
    """)).fetchall()
    
    for cat in cats:
        print(f"  {cat}")
