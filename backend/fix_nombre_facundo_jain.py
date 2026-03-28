import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

def fix_nombre_facundo():
    db_url = os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://')
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    print("Corrigiendo nombre de Facundo Jain (ID 1006)...")
    
    cur.execute("""
        UPDATE perfil_usuarios
        SET nombre = 'Facundo', apellido = 'Jain'
        WHERE id_usuario = 1006
    """)
    
    conn.commit()
    
    cur.execute("""
        SELECT nombre, apellido
        FROM perfil_usuarios
        WHERE id_usuario = 1006
    """)
    result = cur.fetchone()
    
    print(f"✅ Nombre actualizado: {result[0]} {result[1]}")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    fix_nombre_facundo()
