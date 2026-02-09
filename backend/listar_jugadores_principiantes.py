"""
Script para listar jugadores principiantes y ver cuánto cambiaría su rating
"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ Error: DATABASE_URL no está configurada")
    sys.exit(1)

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def main():
    session = Session()
    
    try:
        # Obtener jugadores principiantes con sus estadísticas
        query = text("""
            SELECT 
                u.id_usuario,
                u.nombre_usuario as username,
                pu.nombre,
                pu.apellido,
                u.rating as rating_actual,
                u.sexo,
                c.nombre as categoria,
                u.partidos_jugados
            FROM usuarios u
            INNER JOIN perfil_usuarios pu ON u.id_usuario = pu.id_usuario
            INNER JOIN categorias c ON u.id_categoria = c.id_categoria
            WHERE c.nombre = 'Principiante'
            ORDER BY u.partidos_jugados DESC, u.rating DESC
        """)
        
        result = session.execute(query)
        jugadores = result.fetchall()
        
        if not jugadores:
            print("\n❌ No se encontraron jugadores principiantes")
            return
        
        print("\n" + "="*110)
        print("JUGADORES PRINCIPIANTES - Análisis de K-Factor")
        print("="*110 + "\n")
        
        # K-factors anteriores y nuevos
        def get_k_anterior(partidos: int) -> int:
            if partidos <= 5:
                return 200
            elif partidos <= 15:
                return 180
            elif partidos <= 40:
                return 20
            else:
                return 15
        
        def get_k_nuevo(partidos: int) -> int:
            if partidos <= 10:
                return 250
            elif partidos <= 25:
                return 200
            elif partidos <= 50:
                return 150
            else:
                return 100
        
        # Tabla de resultados
        print(f"{'ID':>4} | {'Username':>15} | {'Nombre':>25} | {'Rating':>6} | {'Partidos':>8} | {'K Ant':>6} | {'K Nuevo':>8} | {'Dif':>5} | {'Impacto':>10}")
        print("-" * 110)
        
        total_jugadores = 0
        jugadores_beneficiados = 0
        
        for jugador in jugadores:
            nombre_completo = f"{jugador.nombre} {jugador.apellido}"
            partidos = jugador.partidos_jugados or 0
            
            k_anterior = get_k_anterior(partidos)
            k_nuevo = get_k_nuevo(partidos)
            diferencia = k_nuevo - k_anterior
            
            # Calcular impacto aproximado (% de aumento)
            if k_anterior > 0:
                impacto = ((k_nuevo - k_anterior) / k_anterior) * 100
            else:
                impacto = 0
            
            # Determinar si se beneficia significativamente
            beneficiado = diferencia > 50
            if beneficiado:
                jugadores_beneficiados += 1
            
            # Formatear impacto
            if impacto > 0:
                impacto_str = f"+{impacto:.0f}%"
            else:
                impacto_str = f"{impacto:.0f}%"
            
            # Marcar jugadores muy beneficiados
            marca = "⭐" if diferencia > 100 else ""
            
            print(f"{jugador.id_usuario:>4} | {jugador.username:>15} | {nombre_completo:>25} | "
                  f"{jugador.rating_actual:>6} | {partidos:>8} | "
                  f"{k_anterior:>6} | {k_nuevo:>8} | {diferencia:>+5} | {impacto_str:>10} {marca}")
            
            total_jugadores += 1
        
        print("-" * 110)
        print(f"\nTotal de jugadores: {total_jugadores}")
        print(f"Jugadores beneficiados significativamente (Δ > 50): {jugadores_beneficiados} ({jugadores_beneficiados/total_jugadores*100:.1f}%)")
        
        # Estadísticas por rango de partidos
        print("\n" + "="*110)
        print("DISTRIBUCIÓN POR RANGO DE PARTIDOS")
        print("="*110 + "\n")
        
        rangos = [
            (0, 10, "0-10 partidos"),
            (11, 25, "11-25 partidos"),
            (26, 50, "26-50 partidos"),
            (51, 999, "51+ partidos")
        ]
        
        print(f"{'Rango':>20} | {'Jugadores':>10} | {'K Anterior':>12} | {'K Nuevo':>10} | {'Diferencia':>12}")
        print("-" * 70)
        
        for min_p, max_p, label in rangos:
            jugadores_rango = [j for j in jugadores if min_p <= (j.partidos_jugados or 0) <= max_p]
            count = len(jugadores_rango)
            
            if count > 0:
                k_ant = get_k_anterior(min_p)
                k_nue = get_k_nuevo(min_p)
                dif = k_nue - k_ant
                
                print(f"{label:>20} | {count:>10} | {k_ant:>12} | {k_nue:>10} | {dif:>+12}")
        
        print("\n" + "="*110)
        print("RECOMENDACIONES")
        print("="*110 + "\n")
        
        if jugadores_beneficiados > 0:
            print(f"✅ {jugadores_beneficiados} jugadores se beneficiarán significativamente del aumento de K-factor")
            print(f"\nPara aplicar los cambios:")
            print(f"  1. Probar con un jugador: python recalcular_elo_principiantes.py --usuario-id <ID> --dry-run")
            print(f"  2. Aplicar a un jugador: python recalcular_elo_principiantes.py --usuario-id <ID>")
            print(f"  3. Aplicar a todos: python recalcular_elo_principiantes.py")
        else:
            print("ℹ️  No hay jugadores que se beneficien significativamente en este momento")
        
        print("\n" + "="*110 + "\n")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        session.close()

if __name__ == "__main__":
    main()
