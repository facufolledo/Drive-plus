# Implementación: Cambio Manual de Horarios con Validación

## 🎯 FUNCIONALIDADES AGREGADAS

### 1. Endpoint para cambiar horarios manualmente

**Endpoint**: `PUT /torneos/{torneo_id}/partidos/{partido_id}/cambiar-horario`

**Autenticación**: Requiere ser organizador del torneo

**Request Body**:
```json
{
  "fecha": "2026-02-06",
  "hora": "19:10",
  "cancha_id": 1
}
```

**Respuesta exitosa** (sin solapamiento):
```json
{
  "success": true,
  "message": "Horario actualizado correctamente",
  "partido": {
    "id": 73,
    "pareja1": "juanromero/juanpabloromerojr",
    "pareja2": "diegobicet/juancejas",
    "fecha": "2026-02-06",
    "hora": "19:10",
    "cancha": "Cancha 1",
    "cancha_id": 1
  }
}
```

**Respuesta con solapamiento detectado**:
```json
{
  "success": false,
  "error": "SOLAPAMIENTO_DETECTADO",
  "message": "El horario solicitado se solapa con 1 partido(s) en Cancha 1",
  "conflictos": [
    {
      "partido_id": 74,
      "pareja1": "millicay503/fmontivero257",
      "pareja2": "ericleterrucci/facundoguerrero",
      "fecha_hora": "2026-02-06 19:10",
      "cancha": "Cancha 1"
    }
  ],
  "horario_solicitado": {
    "fecha": "2026-02-06",
    "hora": "19:10",
    "cancha": "Cancha 1",
    "inicio": "2026-02-06 19:10",
    "fin": "2026-02-06 20:00"
  }
}
```

### 2. Validación de solapamiento

El endpoint valida automáticamente:

- ✅ **Solapamiento de horarios**: Detecta si otro partido ya está programado en la misma cancha en un horario que se solapa
- ✅ **Duración del partido**: Considera que cada partido dura 50 minutos
- ✅ **Cancha activa**: Verifica que la cancha esté activa en el torneo
- ✅ **Permisos**: Solo el organizador puede cambiar horarios

**Lógica de solapamiento**:
```python
# Partido nuevo: [nuevo_inicio, nuevo_inicio + 50 mins]
# Partido existente: [otro_inicio, otro_inicio + 50 mins]
# Hay solapamiento si:
if nuevo_inicio < otro_fin AND nuevo_fin > otro_inicio:
    # CONFLICTO DETECTADO
```

### 3. Actualización de canchas del torneo 37

**Cambio**: Solo 2 canchas techadas disponibles (Cancha 1 y Cancha 2)

**Script SQL**: `backend/actualizar_canchas_torneo37.sql`
```sql
UPDATE torneo_canchas
SET activa = false
WHERE torneo_id = 37
AND nombre IN ('Cancha 3', 'Cancha 4', 'Cancha 5');
```

**Script Python**: `backend/ejecutar_actualizar_canchas_torneo37.py`

## 📋 CASOS DE USO

### Caso 1: Cambio exitoso sin conflictos

```bash
curl -X PUT "http://localhost:8000/torneos/37/partidos/73/cambiar-horario" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "fecha": "2026-02-07",
    "hora": "15:00",
    "cancha_id": 2
  }'
```

**Resultado**: Partido movido a sábado 15:00 en Cancha 2

### Caso 2: Intento de cambio con solapamiento

```bash
curl -X PUT "http://localhost:8000/torneos/37/partidos/73/cambiar-horario" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "fecha": "2026-02-06",
    "hora": "19:10",
    "cancha_id": 1
  }'
```

**Resultado**: Error con lista de conflictos detectados

### Caso 3: Cancha inactiva

```bash
curl -X PUT "http://localhost:8000/torneos/37/partidos/73/cambiar-horario" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "fecha": "2026-02-06",
    "hora": "19:10",
    "cancha_id": 3
  }'
```

**Resultado**: Error 404 - "Cancha no encontrada o no está activa"

## 🔧 IMPLEMENTACIÓN TÉCNICA

### Archivo modificado:
- `backend/src/controllers/torneo_controller.py`

### Nuevas clases:
```python
class CambiarHorarioRequest(BaseModel):
    fecha: str  # "2026-02-06"
    hora: str   # "19:10"
    cancha_id: int
```

### Validaciones implementadas:

1. **Permisos**: Solo organizador puede cambiar horarios
2. **Partido existe**: Verifica que el partido pertenezca al torneo
3. **Cancha válida**: Verifica que la cancha exista y esté activa
4. **Formato de fecha/hora**: Valida formato correcto
5. **Solapamiento**: Detecta conflictos con otros partidos en la misma cancha
6. **Duración**: Considera 50 minutos por partido

## 🎨 INTEGRACIÓN CON FRONTEND

### Componente sugerido: ModalCambiarHorario.tsx

```typescript
interface CambiarHorarioProps {
  torneoId: number;
  partidoId: number;
  onClose: () => void;
  onSuccess: () => void;
}

const ModalCambiarHorario: React.FC<CambiarHorarioProps> = ({
  torneoId,
  partidoId,
  onClose,
  onSuccess
}) => {
  const [fecha, setFecha] = useState('');
  const [hora, setHora] = useState('');
  const [canchaId, setCanchaId] = useState<number>(1);
  const [conflictos, setConflictos] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const handleCambiarHorario = async () => {
    setLoading(true);
    setConflictos([]);
    
    try {
      const response = await fetch(
        `${API_URL}/torneos/${torneoId}/partidos/${partidoId}/cambiar-horario`,
        {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ fecha, hora, cancha_id: canchaId })
        }
      );
      
      const data = await response.json();
      
      if (data.success) {
        toast.success('Horario actualizado correctamente');
        onSuccess();
        onClose();
      } else if (data.error === 'SOLAPAMIENTO_DETECTADO') {
        setConflictos(data.conflictos);
        toast.warning(data.message);
      }
    } catch (error) {
      toast.error('Error al cambiar horario');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal">
      <h2>Cambiar Horario del Partido</h2>
      
      <input
        type="date"
        value={fecha}
        onChange={(e) => setFecha(e.target.value)}
      />
      
      <input
        type="time"
        value={hora}
        onChange={(e) => setHora(e.target.value)}
      />
      
      <select
        value={canchaId}
        onChange={(e) => setCanchaId(Number(e.target.value))}
      >
        <option value={1}>Cancha 1</option>
        <option value={2}>Cancha 2</option>
      </select>
      
      {conflictos.length > 0 && (
        <div className="alert alert-warning">
          <h3>⚠️ Conflictos detectados:</h3>
          {conflictos.map((conflicto, idx) => (
            <div key={idx}>
              {conflicto.pareja1} vs {conflicto.pareja2}
              <br />
              {conflicto.fecha_hora} - {conflicto.cancha}
            </div>
          ))}
        </div>
      )}
      
      <button onClick={handleCambiarHorario} disabled={loading}>
        {loading ? 'Cambiando...' : 'Cambiar Horario'}
      </button>
      
      <button onClick={onClose}>Cancelar</button>
    </div>
  );
};
```

### Integración en TorneoFixture.tsx

Agregar botón de editar horario en cada partido:

```typescript
<button
  onClick={() => setPartidoEditando(partido.id)}
  className="btn-icon"
  title="Cambiar horario"
>
  <Clock size={16} />
</button>

{partidoEditando === partido.id && (
  <ModalCambiarHorario
    torneoId={torneoId}
    partidoId={partido.id}
    onClose={() => setPartidoEditando(null)}
    onSuccess={() => {
      refetchPartidos();
      setPartidoEditando(null);
    }}
  />
)}
```

## 🧪 TESTING

### Test manual del endpoint:

```python
# backend/test_cambiar_horario_manual.py
import requests

API_URL = "http://localhost:8000"
TOKEN = "tu_token_aqui"

def test_cambiar_horario_exitoso():
    response = requests.put(
        f"{API_URL}/torneos/37/partidos/73/cambiar-horario",
        headers={"Authorization": f"Bearer {TOKEN}"},
        json={
            "fecha": "2026-02-07",
            "hora": "15:00",
            "cancha_id": 2
        }
    )
    print(response.json())
    assert response.json()["success"] == True

def test_cambiar_horario_con_solapamiento():
    response = requests.put(
        f"{API_URL}/torneos/37/partidos/73/cambiar-horario",
        headers={"Authorization": f"Bearer {TOKEN}"},
        json={
            "fecha": "2026-02-06",
            "hora": "19:10",
            "cancha_id": 1
        }
    )
    data = response.json()
    print(data)
    assert data["success"] == False
    assert data["error"] == "SOLAPAMIENTO_DETECTADO"
    assert len(data["conflictos"]) > 0

if __name__ == "__main__":
    test_cambiar_horario_exitoso()
    test_cambiar_horario_con_solapamiento()
```

## 📊 IMPACTO EN EL TORNEO 37

### Antes:
- 5 canchas disponibles
- Más slots simultáneos
- Fixture más compacto

### Después:
- 2 canchas techadas (Cancha 1 y Cancha 2)
- Menos slots simultáneos
- Fixture más extendido en el tiempo
- Necesidad de reprogramar manualmente algunos partidos

### Recomendación:
1. Regenerar el fixture con solo 2 canchas
2. Usar el endpoint de cambio manual para ajustes finos
3. Validar que no haya solapamientos antes de confirmar

## ✅ CHECKLIST DE IMPLEMENTACIÓN

- [x] Endpoint PUT creado
- [x] Validación de permisos
- [x] Validación de solapamiento
- [x] Validación de cancha activa
- [x] Respuesta con conflictos detallados
- [x] Script para actualizar canchas
- [x] Documentación completa
- [ ] Componente frontend (pendiente)
- [ ] Tests automatizados (pendiente)
- [ ] Deploy a producción (pendiente)

## 🚀 PRÓXIMOS PASOS

1. **Actualizar canchas del torneo 37**:
   ```bash
   # Opción 1: SQL directo
   psql -d driveplus -f backend/actualizar_canchas_torneo37.sql
   
   # Opción 2: Script Python
   python backend/ejecutar_actualizar_canchas_torneo37.py
   ```

2. **Regenerar fixture con 2 canchas**:
   - Eliminar fixture actual
   - Generar nuevo desde frontend
   - Verificar restricciones

3. **Implementar componente frontend**:
   - Crear ModalCambiarHorario.tsx
   - Agregar botón de editar en cada partido
   - Mostrar conflictos si los hay

4. **Testing**:
   - Probar cambios exitosos
   - Probar detección de solapamientos
   - Probar con canchas inactivas

---

**Fecha**: 2026-02-06
**Estado**: ✅ Backend completado, Frontend pendiente
**Versión**: 1.0
