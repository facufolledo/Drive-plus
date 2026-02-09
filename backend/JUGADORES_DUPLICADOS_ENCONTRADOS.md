# Jugadores Duplicados Encontrados

## Resumen
- **Total de grupos**: 8
- **Total de jugadores duplicados**: 16
- **Umbral de similitud**: 85%

---

## GRUPO 1: Fernanda Bustos (100% similar)

### Cuenta Temporal (ELIMINAR)
- **ID**: 225
- **Email**: fernanda.bustos@driveplus.temp ❌
- **Usuario**: fernandabustos
- **Rating**: 768 | Partidos: 1
- **Parejas**: 1 | Partidos jugados: 1

### Cuenta Real (MANTENER)
- **ID**: 57
- **Email**: fernanda.ferplast@gmail.com ✅
- **Usuario**: fernanda.ferplast
- **Rating**: 1099 | Partidos: 0
- **Parejas**: 1 | Partidos jugados: 0

**Acción**: Migrar datos de ID 225 → ID 57

---

## GRUPO 2: Gabriel Fernández (100% similar)

### Cuenta Temporal (ELIMINAR)
- **ID**: 206
- **Email**: gabriel.fernandez@driveplus.temp ❌
- **Usuario**: gabrielfernandez
- **Rating**: 1499 | Partidos: 0
- **Parejas**: 1 | Partidos jugados: 1

### Cuenta Real (MANTENER)
- **ID**: 38
- **Email**: grfernandez191@gmail.com ✅
- **Usuario**: grfernandez191
- **Rating**: 1499 | Partidos: 0
- **Parejas**: 1 | Partidos jugados: 0

**Acción**: Migrar datos de ID 206 → ID 38

---

## GRUPO 3: Facundo Guerrero (100% similar)

### Cuenta Temporal (ELIMINAR)
- **ID**: 129
- **Email**: facundo.guerrero@driveplus.temp ❌
- **Usuario**: facundoguerrero
- **Rating**: 1074 | Partidos: 2
- **Parejas**: 1 | Partidos jugados: 2

### Cuenta Real (MANTENER)
- **ID**: 210
- **Email**: facundo_g10@hotmail.com ✅
- **Usuario**: facundo_g10
- **Rating**: 1099 | Partidos: 0
- **Parejas**: 0 | Partidos jugados: 0

**Acción**: Migrar datos de ID 129 → ID 210

---

## GRUPO 4: Matias Moreno (100% similar)

### Cuenta Temporal (ELIMINAR)
- **ID**: 224
- **Email**: matias.moreno@driveplus.temp ❌
- **Usuario**: matiasmoreno
- **Rating**: 768 | Partidos: 1
- **Parejas**: 1 | Partidos jugados: 1

### Cuenta Real (MANTENER)
- **ID**: 30
- **Email**: matis61190@gmail.com ✅
- **Usuario**: matis61190
- **Rating**: 1099 | Partidos: 0
- **Parejas**: 1 | Partidos jugados: 0

**Acción**: Migrar datos de ID 224 → ID 30

---

## GRUPO 5: Esther Reyes (100% similar)

### Cuenta 1
- **ID**: 97
- **Email**: estuyreyes95@gmail.com ✅
- **Usuario**: estureyes
- **Rating**: 1499 | Partidos: 0
- **Parejas**: 0 | Partidos jugados: 0

### Cuenta 2
- **ID**: 98
- **Email**: estureyes95@gmail.com ✅
- **Usuario**: estherreyes
- **Rating**: 1499 | Partidos: 0
- **Parejas**: 1 | Partidos jugados: 0

**Acción**: ⚠️ Ambas tienen email real. Verificar con el usuario cuál es la correcta.
- Opción 1: Migrar ID 97 → ID 98 (tiene pareja)
- Opción 2: Migrar ID 98 → ID 97

---

## GRUPO 6: Juan Romero (100% similar)

### Cuenta Temporal (ELIMINAR)
- **ID**: 125
- **Email**: juan.romero@driveplus.temp ❌
- **Usuario**: juanromero
- **Rating**: 1100 | Partidos: 4
- **Parejas**: 1 | Partidos jugados: 3

### Cuenta Real (MANTENER)
- **ID**: 81
- **Email**: pablochami26@gmail.com ✅
- **Usuario**: pablochami26
- **Rating**: 749 | Partidos: 0
- **Parejas**: 1 | Partidos jugados: 0

**Acción**: Migrar datos de ID 125 → ID 81

---

## GRUPO 7: Juan Pablo Romero (91.9% similar)

### Cuenta Real 1
- **ID**: 80
- **Email**: romerojp.1609@gmail.com ✅
- **Usuario**: romerojp.1609
- **Nombre**: Juan Pablo Romero
- **Rating**: 1099 | Partidos: 0
- **Parejas**: 1 | Partidos jugados: 0

### Cuenta Temporal
- **ID**: 124
- **Email**: juanpablo.romerojr@driveplus.temp ❌
- **Usuario**: juanpabloromerojr
- **Nombre**: Juan Pablo Romero Jr
- **Rating**: 1100 | Partidos: 4
- **Parejas**: 1 | Partidos jugados: 3

**Acción**: ⚠️ Verificar si son la misma persona (uno dice "Jr")
- Si son la misma: Migrar ID 124 → ID 80
- Si son diferentes: Dejar ambas cuentas

---

## GRUPO 8: Martin Sanchez (100% similar)

### Cuenta Temporal (ELIMINAR)
- **ID**: 132
- **Email**: martin.sanchez@driveplus.temp ❌
- **Usuario**: martinsanchez
- **Nombre**: Martin Sanchez
- **Rating**: 1074 | Partidos: 3
- **Parejas**: 1 | Partidos jugados: 2

### Cuenta Real (MANTENER)
- **ID**: 209
- **Email**: martinalejandrosanchez27@gmail.com ✅
- **Usuario**: martinalejandrosanchez27
- **Nombre**: Martin Sánchez
- **Rating**: 1299 | Partidos: 0
- **Parejas**: 0 | Partidos jugados: 0

**Acción**: Migrar datos de ID 132 → ID 209

---

## Script de Migración

Para cada migración, usar:

```bash
python migrar_usuario_especifico.py
```

Y seguir las instrucciones para ingresar:
1. ID del usuario duplicado (origen)
2. ID del usuario real (destino)

---

## Migraciones Recomendadas (en orden)

1. ✅ Fernanda Bustos: 225 → 57
2. ✅ Gabriel Fernández: 206 → 38
3. ✅ Facundo Guerrero: 129 → 210
4. ✅ Matias Moreno: 224 → 30
5. ⚠️ Esther Reyes: Verificar con usuario
6. ✅ Juan Romero: 125 → 81
7. ⚠️ Juan Pablo Romero: Verificar si son la misma persona
8. ✅ Martin Sanchez: 132 → 209

---

## Notas

- Las cuentas con email `@driveplus.temp` son temporales y deben eliminarse
- Las cuentas con email real (gmail, hotmail, etc.) deben mantenerse
- Después de cada migración, verificar que los datos se transfirieron correctamente
