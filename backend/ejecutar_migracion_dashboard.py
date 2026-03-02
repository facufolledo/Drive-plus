"""
Script para ejecutar la migración de índices del Dashboard en producción
"""
import os
import psycopg2

# Usar DATABASE_URL directamente desde el entorno o .env.production
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    # Intentar leer de .env.production
    try:
        with open('.env.production', 'r') as f:
            for line in f:
                if line.startswith('DATABASE_URL='):
                    DATABASE_URL = line.split('=', 1)[1].strip().strip('"').strip("'")
                    break
    except:
        pass

if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL no encontrada")
    print("Por favor, ejecuta: export DATABASE_URL='tu_url_de_postgres'")
    exit(1)

print(f"🔗 Conectando a la base de datos...")

try:
    # Conectar a la base de datos
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    cursor = conn.cursor()
    
    print("✅ Conexión exitosa")
    print("\n📊 Ejecutando migración de índices del Dashboard...\n")
    
    # Leer el archivo SQL
    with open('migrations_dashboard_indices.sql', 'r', encoding='utf-8') as f:
        sql = f.read()
    
    # Ejecutar la migración
    cursor.execute(sql)
    
    print("✅ Migración ejecutada exitosamente\n")
    
    # Verificar índices creados
    print("📋 Verificando índices creados:\n")
    cursor.execute("""
        SELECT 
            tablename,
            indexname
        FROM pg_indexes
        WHERE tablename IN ('partido_jugadores', 'historial_rating', 'usuarios', 'perfil_usuarios', 'partidos')
        AND indexname LIKE 'idx_%'
        ORDER BY tablename, indexname
    """)
    
    indices = cursor.fetchall()
    for tabla, indice in indices:
        print(f"  ✓ {tabla}.{indice}")
    
    # Verificar constraints creados
    print("\n🔒 Verificando constraints de unicidad:\n")
    cursor.execute("""
        SELECT 
            conrelid::regclass as table_name,
            conname as constraint_name
        FROM pg_constraint
        WHERE conname IN ('uq_partido_jugadores_partido_usuario', 'uq_historial_rating_partido_usuario')
    """)
    
    constraints = cursor.fetchall()
    for tabla, constraint in constraints:
        print(f"  ✓ {tabla}.{constraint}")
    
    if not constraints:
        print("  ⚠️  No se encontraron constraints (puede que ya existieran)")
    
    cursor.close()
    conn.close()
    
    print("\n✅ Migración completada exitosamente!")
    print("🚀 El Dashboard ahora debería cargar mucho más rápido")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
