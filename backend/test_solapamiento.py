"""
Test de lógica de solapamiento
"""
from datetime import datetime, timedelta

# Partido 1: 19:10 - 20:00
partido1_inicio = datetime(2026, 2, 6, 19, 10)
partido1_fin = partido1_inicio + timedelta(minutes=50)

# Partido 2: 19:30 - 20:20
partido2_inicio = datetime(2026, 2, 6, 19, 30)
partido2_fin = partido2_inicio + timedelta(minutes=50)

print("Partido 1:")
print(f"  Inicio: {partido1_inicio.strftime('%H:%M')}")
print(f"  Fin: {partido1_fin.strftime('%H:%M')}")

print("\nPartido 2:")
print(f"  Inicio: {partido2_inicio.strftime('%H:%M')}")
print(f"  Fin: {partido2_fin.strftime('%H:%M')}")

# Lógica actual del backend
# Hay solapamiento si: nuevo_inicio < otro_fin AND nuevo_fin > otro_inicio
solapamiento = partido2_inicio < partido1_fin and partido2_fin > partido1_inicio

print(f"\nCondición: {partido2_inicio.strftime('%H:%M')} < {partido1_fin.strftime('%H:%M')} AND {partido2_fin.strftime('%H:%M')} > {partido1_inicio.strftime('%H:%M')}")
print(f"Resultado: {partido2_inicio < partido1_fin} AND {partido2_fin > partido1_inicio} = {solapamiento}")

if solapamiento:
    print("\n✅ SOLAPAMIENTO DETECTADO (correcto)")
else:
    print("\n❌ NO SE DETECTÓ SOLAPAMIENTO (incorrecto)")
