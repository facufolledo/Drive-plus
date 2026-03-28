"""
Asignar manualmente los 5 partidos conflictivos a horarios razonables.
"""

import os
from datetime import datetime
from dotenv import load_dotenv
import psycopg2

load_dotenv('.env.production')

def conectar_db():
    db_url = os.getenv('DATABASE_URL')
    if db_url.startswith('postgresql+pg8000://'):
        db_url = db_url.replace('postgresql+pg8000://', 'postgresql://')
    return psycopg2.connect(db_url)

# Asignaciones manuales basadas en disponibilidades reales
asignaciones = [
    {
        'partido_id': 1044,
        'fecha': datetime(2026, 3, 29, 16, 0),  # Sabado 16:00
        'razon': 'Silva/Aguilar pueden despues de 14:00, Lucero/Folledo pueden viernes 16:00+'
    },
    {
        'partido_id': 1045,
        'fecha': datetime(2026, 3, 29, 17, 0),  # Sabado 17:00 (tarde)
        'razon': 'Silva/Aguilar pueden despues de 14:00, Mercado/Zaracho pueden sabado 00:00-01:00'
    },
    {
        'partido_id': 1046,
        'fecha': datetime(2026, 3, 28, 23, 59),  # Viernes 23:59
        'razon': 'Lucero/Folledo pueden viernes 16:00+, Mercado/Zaracho no pueden viernes (forzado)'
    },
    {
        'partido_id': 1052,
        'fecha': datetime(2026, 3, 28, 22, 30),  # Viernes 22:30
        'razon': 'Bedini/Johannesen pueden viernes despues de 14:00, Diaz/Jofre pueden viernes despues de 22:00'
    }
]

print("\n" + "="*80)
print("ASIGNACION MANUAL DE PARTIDOS CONFLICTIVOS")
print("="*80 + "\n")

for asig in asignaciones:
    dia_semana = asig['fecha'].strftime('%A')
    fecha_str = asig['fecha'].strftime('%d/%m/%Y %H:%M')
    print(f"Partido {asig['partido_id']}: {dia_semana.upper()} {fecha_str}")
    print(f"  Razon: {asig['razon']}\n")

print("="*80)
respuesta = input("\nEjecutar asignaciones? (si/no): ")

if respuesta.lower() == 'si':
    conn = conectar_db()
    cur = conn.cursor()
    
    for asig in asignaciones:
        query = """
        UPDATE partidos 
        SET fecha_hora = %s
        WHERE id_partido = %s
        """
        cur.execute(query, (asig['fecha'], asig['partido_id']))
    
    conn.commit()
    cur.close()
    conn.close()
    
    print(f"\nOK - {len(asignaciones)} partidos actualizados exitosamente")
else:
    print("\nOperacion cancelada")
