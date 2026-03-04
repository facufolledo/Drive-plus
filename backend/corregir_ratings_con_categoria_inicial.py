"""
Corregir ratings usando la categoría INICIAL del usuario
Si tiene cambios de categoría, usa la primera. Si no, usa la actual.
"""
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv('.env.production')

DATABASE_URL = os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://')

RANGOS_CATEGORIAS = {
    'Principiante': 249,
    '8va': 749,
    '7ma': 1099,
    '6ta': 1299,
    '5ta': 1499,
    '4ta': 1699,
    '3ra': 1899
}

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Obtener usuarios con historial (excluyendo temps)
cur.execute("""
    SELECT DISTINCT u.id_usuario, p.nombre, p.apellido, u.rating
    FROM usuarios u
    JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
    WHERE EXISTS (
        SELECT 1 FROM historial_rating h WHERE h.id_usuario = u.id_usuario
    )
    AND p.nombre NOT LIKE '%temp%'
    AND p.apellido NOT LIKE '%temp%'
    ORDER BY p.apellido, p.nombre
""")

usuarios = cur.fetchall()

print(f"\n🔍 Verificando {len(usuarios)} usuarios...\n")

usuarios_corregidos = []
usuarios_correctos = []

for user_id, nombre, apellido, rating_actual in usuarios:
    # Obtener categoría inicial de perfil_usuarios
    cur.execute("""
        SELECT c.nombre
        FROM perfil_usuarios pu
        JOIN categorias c ON pu.id_categoria_inicial = c.id_categoria
        WHERE pu.id_usuario = %s
    """, (user_id,))
    
    cat_inicial_row = cur.fetchone()
    
    if cat_inicial_row:
        # Tiene categoría inicial guardada, usarla
        categoria_inicial = cat_inicial_row[0]
    else:
        # No tiene categoría inicial, usar la actual
        cur.execute("""
            SELECT c.nombre
            FROM usuarios u
            JOIN categorias c ON u.id_categoria = c.id_categoria
            WHERE u.id_usuario = %s
        """, (user_id,))
        
        cat_row = cur.fetchone()
        categoria_inicial = cat_row[0] if cat_row else None
    
    if not categoria_inicial or categoria_inicial not in RANGOS_CATEGORIAS:
        continue
    
    rating_inicial = RANGOS_CATEGORIAS[categoria_inicial]
    
    # Suma de deltas (DISTINCT para evitar duplicados)
    cur.execute("""
        SELECT COALESCE(SUM(delta), 0)
        FROM (
            SELECT DISTINCT ON (id_usuario, id_partido) delta
            FROM historial_rating
            WHERE id_usuario = %s
            ORDER BY id_usuario, id_partido, id_historial
        ) t
    """, (user_id,))
    
    suma_deltas = int(cur.fetchone()[0])
    rating_esperado = rating_inicial + suma_deltas
    diferencia = rating_actual - rating_esperado
    
    if diferencia != 0:
        # Excluir usuarios con diferencia > 80 (probablemente cambio de categoría)
        if abs(diferencia) <= 80:
            usuarios_corregidos.append({
                'user_id': user_id,
                'nombre': f"{nombre} {apellido}",
                'categoria_inicial': categoria_inicial,
                'rating_inicial': rating_inicial,
                'suma_deltas': suma_deltas,
                'rating_esperado': rating_esperado,
                'rating_actual': rating_actual,
                'diferencia': diferencia
            })
    else:
        usuarios_correctos.append(f"{nombre} {apellido}")

print(f"{'='*110}")
print(f"\n📊 RESUMEN:")
print(f"   Total usuarios: {len(usuarios)}")
print(f"   ⚠️  Con discrepancias: {len(usuarios_corregidos)}")
print(f"   ✓  Correctos: {len(usuarios_correctos)}\n")

if usuarios_corregidos:
    print(f"{'='*110}")
    print(f"USUARIOS CON DISCREPANCIAS ({len(usuarios_corregidos)}):")
    print(f"{'='*110}")
    print(f"{'Nombre':<30} {'Cat Inicial':<16} {'Inicial':>8} {'Deltas':>7} {'Esperado':>9} {'Actual':>8} {'Dif':>6}")
    print(f"{'-'*110}")
    for u in usuarios_corregidos:
        print(f"{u['nombre']:<30} {u['categoria_inicial']:<16} {u['rating_inicial']:>8} {u['suma_deltas']:>+7} {u['rating_esperado']:>9} {u['rating_actual']:>8} {u['diferencia']:>+6}")
    
    print(f"\n{'='*110}")
    respuesta = input(f"¿Corregir los {len(usuarios_corregidos)} usuarios? (s/n): ")
    
    if respuesta.lower() == 's':
        for u in usuarios_corregidos:
            cur.execute("""
                UPDATE usuarios
                SET rating = %s
                WHERE id_usuario = %s
            """, (u['rating_esperado'], u['user_id']))
            print(f"✅ {u['nombre']}: {u['rating_actual']} → {u['rating_esperado']}")
        
        conn.commit()
        print(f"\n✅ {len(usuarios_corregidos)} usuarios corregidos")
    else:
        print("\n❌ Cancelado")
else:
    print("✅ Todos los usuarios tienen ratings correctos")

cur.close()
conn.close()
