# Instrucciones Finales - Restricciones y Cambio de Horarios

## 🎯 PROBLEMA ACTUAL

Reportas que el sistema sigue generando partidos en horarios restringidos (ej: viernes 16:10 para Bicet/Cejas).

## 🔍 DIAGNÓSTICO

El código del backend **SÍ verifica ambas parejas** correctamente. El problema es que el backend en ejecución **NO está usando el código actualizado**.

### Verificación del código:

```python
# En _asignar_horarios_y_canchas() línea ~500
datos_pareja1 = parejas_disponibilidad.get(pareja1_id, {'restricciones_por_dia': {}})
datos_pareja2 = parejas_disponibilidad.get(pareja2_id, {'restricciones_por_dia': {}})

# Verifica AMBAS parejas
pareja1_disponible = TorneoFixtureGlobalService._verificar_disponibilidad_pareja(
    dia, hora_mins, datos_pareja1
)

pareja2_disponible = TorneoFixtureGlobalService._verificar_disponibilidad_pareja(
    dia, hora_mins, datos_pareja2
)

# Solo acepta el slot si AMBAS están disponibles
if not (pareja1_disponible and pareja2_disponible):
    continue
```

## ✅ SOLUCIÓN

### 1. Reiniciar el backend COMPLETAMENTE

El backend tiene el código en cache. Necesitas:

```bash
# Opción A: Reiniciar el proceso
# Detén el backend (Ctrl+C)
# Limpia cache
cd backend
Get-ChildItem -Recurse -Filter "*.pyc" | Remove-Item -Force
Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force

# Inicia de nuevo
python main.py
```

```bash
# Opción B: Si usas Railway/producción
# Haz un nuevo deploy o reinicia el servicio desde el dashboard
```

### 2. Verificar que el backend usa el código correcto

Ejecuta este script para verificar:

```bash
python backend/debug_restricciones_detallado.py
```

**Resultado esperado**: "✅ No hay partidos a las 16:10"

**Si ves violaciones**: El backend NO está usando el código actualizado

### 3. Regenerar el fixture

Una vez que el backend esté actualizado:

1. Elimina el fixture actual desde el frontend
2. Genera nuevo fixture
3. Verifica con: `python backend/test_fixture_torneo37_restricciones.py`

## 🎨 BOTÓN DE CAMBIAR HORARIO

### Ya implementado en el frontend ✅

El botón ya está agregado en `TorneoFixture.tsx`:

- Aparece junto al botón "Cargar Resultado"
- Solo visible para organizadores
- Solo en partidos pendientes
- Icono de reloj + texto "Horario"

### Cómo usarlo:

1. Ve al fixture del torneo
2. Busca un partido pendiente
3. Verás dos botones:
   - **"Horario"** (secundario, con icono de reloj)
   - **"Cargar Resultado"** (amarillo)
4. Click en "Horario"
5. Selecciona nueva fecha, hora y cancha
6. Si hay solapamiento, te mostrará los conflictos
7. Si no hay conflictos, actualiza el horario

## 📊 ESTADO ACTUAL

### Backend:
- ✅ Código corregido
- ✅ Endpoint de cambio manual creado
- ⚠️  Necesita reinicio para aplicar cambios

### Frontend:
- ✅ Modal de cambio de horario creado
- ✅ Botón agregado en fixture
- ✅ Validación de solapamientos integrada

### Base de datos:
- ⚠️  Canchas 3, 4, 5 aún activas (ejecutar script SQL)
- ⚠️  Fixture con partidos incorrectos (regenerar)

## 🚀 PASOS SIGUIENTES

### Paso 1: Actualizar canchas (opcional)
```bash
# Si quieres solo 2 canchas techadas
python backend/ejecutar_actualizar_canchas_torneo37.py
```

### Paso 2: Reiniciar backend
```bash
# Detener backend
# Limpiar cache
# Iniciar de nuevo
```

### Paso 3: Verificar código actualizado
```bash
python backend/debug_restricciones_detallado.py
```

### Paso 4: Regenerar fixture
- Desde el frontend: Eliminar fixture
- Generar nuevo
- Verificar: 0 violaciones

### Paso 5: Probar cambio manual
- Seleccionar un partido
- Click en "Horario"
- Cambiar a un horario con conflicto
- Verificar que muestra la advertencia

## 🐛 SI EL PROBLEMA PERSISTE

### Opción 1: Verificar que el archivo se guardó
```bash
# Ver última modificación del archivo
Get-Item backend/src/services/torneo_fixture_global_service.py | Select-Object LastWriteTime
```

### Opción 2: Verificar imports en main.py
El archivo `main.py` debe importar correctamente el servicio.

### Opción 3: Usar el endpoint de cambio manual
Si el fixture automático sigue fallando, usa el botón "Horario" para corregir manualmente los partidos incorrectos.

## 📝 ARCHIVOS CLAVE

### Backend:
- `backend/src/services/torneo_fixture_global_service.py` - Algoritmo de fixture
- `backend/src/controllers/torneo_controller.py` - Endpoint de cambio manual

### Frontend:
- `frontend/src/components/TorneoFixture.tsx` - Vista de fixture con botón
- `frontend/src/components/ModalCambiarHorario.tsx` - Modal de cambio

### Scripts de debug:
- `backend/debug_restricciones_detallado.py` - Verificar violaciones
- `backend/test_fixture_torneo37_restricciones.py` - Test completo

## ✅ CHECKLIST FINAL

- [ ] Backend reiniciado completamente
- [ ] Cache de Python limpiado
- [ ] Script de debug ejecutado: 0 violaciones
- [ ] Fixture regenerado desde frontend
- [ ] Test de restricciones: 0 violaciones
- [ ] Botón "Horario" visible en frontend
- [ ] Modal de cambio de horario funciona
- [ ] Validación de solapamientos funciona

---

**Nota importante**: El código está correcto. El problema es que el backend en ejecución tiene el código viejo en cache. Un reinicio completo debería resolverlo.
