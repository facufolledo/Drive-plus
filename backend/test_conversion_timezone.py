"""
Test de conversión de timezone para entender cómo funciona
"""
from datetime import datetime, timedelta, timezone
import pytz

# Crear timezone de Argentina
argentina_tz = pytz.timezone('America/Argentina/Buenos_Aires')

# Ejemplo: 2026-03-27 15:00 UTC
hora_utc = datetime(2026, 3, 27, 15, 0, 0, tzinfo=pytz.UTC)

# Convertir a Argentina
hora_argentina = hora_utc.astimezone(argentina_tz)

print("=" * 80)
print("TEST DE CONVERSIÓN DE TIMEZONE")
print("=" * 80)

print(f"\n📅 HORA EN BD (UTC):")
print(f"   {hora_utc}")

print(f"\n🇦🇷 HORA EN ARGENTINA:")
print(f"   {hora_argentina}")
print(f"   Hora: {hora_argentina.hour}:{hora_argentina.minute:02d}")

print(f"\n🔄 CONVERSIÓN INVERSA:")
print(f"   Si quiero que en Argentina sea 15:00")
hora_arg_deseada = argentina_tz.localize(datetime(2026, 3, 27, 15, 0, 0))
hora_utc_necesaria = hora_arg_deseada.astimezone(pytz.UTC)
print(f"   En BD debe ser: {hora_utc_necesaria}")

print(f"\n📊 RESUMEN:")
print(f"   UTC → Argentina: restar 3 horas (o usar astimezone)")
print(f"   Argentina → UTC: sumar 3 horas (o usar astimezone)")
