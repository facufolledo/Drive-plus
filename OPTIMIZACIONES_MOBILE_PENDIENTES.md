# Optimizaciones Mobile Pendientes

## Problemas Identificados

### 1. ModalCargarResultado
- ✅ Ya tiene buen responsive (text-xs sm:text-sm, p-2 sm:p-4)
- Necesita: Mejorar espaciado entre elementos en mobile

### 2. ModalCrearSala  
- ❌ Inputs de fecha y hora se salen de los cuadros en mobile
- Necesita: Ajustar grid y tamaños de inputs

### 3. ModalInscribirTorneo
- ❌ Botón "Inscribir" queda muy abajo y no se mueve al scrollear
- ❌ Sección de restricciones/disponibilidad poco llamativa
- Necesita: 
  - Botón sticky en mobile
  - Destacar más la sección de disponibilidad horaria

### 4. TorneoZonas
- ❌ Nombres de parejas no se ven completos en mobile
- Necesita: Truncate con tooltip o layout vertical en mobile

## Prioridad de Implementación

1. **ALTA**: ModalInscribirTorneo (botón sticky + destacar restricciones)
2. **ALTA**: ModalCrearSala (inputs fecha/hora)
3. **MEDIA**: TorneoZonas (nombres parejas)
4. **BAJA**: ModalCargarResultado (ajustes menores)

## Soluciones Propuestas

### ModalInscribirTorneo
```tsx
// Botón sticky en mobile
<div className="sticky bottom-0 left-0 right-0 bg-cardBg border-t border-cardBorder p-3 sm:relative sm:border-t-0 sm:p-0">
  <Button type="submit" className="w-full">Inscribir Pareja</Button>
</div>

// Destacar disponibilidad
<div className="bg-accent/10 border-2 border-accent/30 rounded-xl p-4">
  <div className="flex items-center gap-2 mb-3">
    <Clock className="text-accent" />
    <h3 className="font-bold text-accent">⚠ Importante: Disponibilidad Horaria</h3>
  </div>
  <SelectorDisponibilidad ... />
</div>
```

### ModalCrearSala
```tsx
// Grid responsive mejorado
<div className="grid grid-cols-2 gap-2 sm:gap-4">
  <Input type="date" className="text-sm" />
  <Input type="time" className="text-sm" />
</div>
```

### TorneoZonas
```tsx
// Nombres con truncate y tooltip
<div className="truncate max-w-[150px] sm:max-w-none" title={pareja.nombre}>
  {pareja.nombre}
</div>
```
