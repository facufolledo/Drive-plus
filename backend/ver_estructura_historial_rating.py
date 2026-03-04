"""
Script para ver la estructura de historial_rating
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv('.env.production')

DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

try:
    # Ver columnas de historial_rating
    query = text("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'historial_rating'
        ORDER BY ordinal_position
    """)
    columnas = session.execute(query).fetchall()
    
    print("\n📋 Columnas de historial_rating:")
    print("="*50)
    for col, tipo in columnas:
        print(f"  {col:<30} {tipo}")
    
    # Ver un registro de ejemplo
    query2 = text("""
        SELECT * FROM historial_rating LIMIT 1
    """)
    ejemplo = session.execute(query2).fetchone()
    
    if ejemplo:
        print("\n📄 Ejemplo de registro:")
        print("="*50)
        for i, col in enumerate(columnas):
            print(f"  {col[0]:<30} {ejemplo[i]}")
    
except Exception as e:
    print(f"❌ Error: {e}")
finally:
    session.close()
