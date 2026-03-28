import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

TORNEO_ID = 45

# Configuración esperada según las imágenes
ZONAS_ESPERADAS = {
    '6ta': {
        'A': 3, 'B': 3, 'C': 3, 'D': 3, 'E': 3, 'F': 3, 'G': 3, 'H': 3, 'I': 3
    },
    '4ta': {
        'A': 3, 'B': 3, 'C': 3, 'D': 3, 'E': 3, 'F': 3, 'G': 2, 'H': 2, 'I': 2
    },
    '8va': {
        'A': 3, 'B': 3, 'C': 3, 'D': 3, 'E': 3, 'F': 2, 'G': 2
    }
}

def main():
    s = Session()
    try:
        print("=" * 80)
        print("VERIFICAR PAREJAS EN TODAS LAS ZONAS - T45")
        print("=" * 80)
        
        total_esperado = 0
        total_real = 0
        zonas_incompletas = []
        
        for cat_nombre, zonas in ZONAS_ESPERADAS.items():
            print(f"\n📂 {cat_nombre}")
            print("─" * 80)
            
            for zona_nombre, parejas_esperadas in zonas.items():
                # Buscar zona
                zona = s.execute(text("""
                    SELECT tz.id
                    FROM torneo_zonas tz
                    JOIN torneo_categorias tc ON tz.categoria_id = tc.id
                    WHERE tc.torneo_id = :tid
                    AND tc.nombre = :cat
                    AND tz.nombre = :zona
                """), {
                    "tid": TORNEO_ID,
                    "cat": cat_nombre,
                    "zona": f"Zona {zona_nombre}"
                }).fetchone()
                
                if not zona:
                    print(f"  Zona {zona_nombre}: ❌ NO EXISTE")
                    zonas_incompletas.append(f"{cat_nombre} Zona {zona_nombre}")
                    continue
                
                # Contar parejas
                parejas_reales = s.execute(text("""
                    SELECT COUNT(*)
                    FROM torneo_zona_parejas
                    WHERE zona_id = :zid
                """), {"zid": zona.id}).scalar()
                
                total_esperado += parejas_esperadas
                total_real += parejas_reales
                
                if parejas_reales < parejas_esperadas:
                    faltantes = parejas_esperadas - parejas_reales
                    print(f"  Zona {zona_nombre}: {parejas_reales}/{parejas_esperadas} ⚠️  FALTAN {faltantes}")
                    zonas_incompletas.append(f"{cat_nombre} Zona {zona_nombre} (faltan {faltantes})")
                else:
                    print(f"  Zona {zona_nombre}: {parejas_reales}/{parejas_esperadas} ✅")
        
        print(f"\n{'=' * 80}")
        print("RESUMEN")
        print("=" * 80)
        print(f"Parejas esperadas: {total_esperado}")
        print(f"Parejas reales: {total_real}")
        print(f"Diferencia: {total_esperado - total_real}")
        
        if zonas_incompletas:
            print(f"\n⚠️  {len(zonas_incompletas)} ZONAS INCOMPLETAS:")
            for zona in zonas_incompletas:
                print(f"  • {zona}")
        
        # Calcular partidos esperados vs reales
        partidos_esperados = 0
        for cat, zonas in ZONAS_ESPERADAS.items():
            for zona, parejas in zonas.items():
                if parejas == 3:
                    partidos_esperados += 3
                elif parejas == 2:
                    partidos_esperados += 1
        
        partidos_reales = s.execute(text("""
            SELECT COUNT(*)
            FROM partidos p
            JOIN torneos_parejas tp ON p.pareja1_id = tp.id
            WHERE tp.torneo_id = :tid
        """), {"tid": TORNEO_ID}).scalar()
        
        print(f"\n{'=' * 80}")
        print("PARTIDOS")
        print("=" * 80)
        print(f"Partidos esperados: {partidos_esperados}")
        print(f"Partidos reales: {partidos_reales}")
        print(f"Diferencia: {partidos_esperados - partidos_reales}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    main()
