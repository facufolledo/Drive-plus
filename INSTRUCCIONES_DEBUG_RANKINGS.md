# Instrucciones para Debug de Rankings

## Problema
El frontend muestra 0 victorias para todos los jugadores, pero el endpoint de backend está devolviendo los datos correctamente.

## Verificación del Backend
✅ El endpoint `https://drive-plus-production.up.railway.app/ranking/` está devolviendo:
```json
{
  "nombre_usuario": "coppedejoaco",
  "partidos_jugados": 3,
  "partidos_ganados": 2,
  "tendencia": "up"
}
```

## Pasos para Debug

### 1. Build del Frontend
```bash
cd frontend
npm run build
```

### 2. Deploy a Hostinger
```bash
# Desde la raíz del proyecto
.\deploy-hostinger.ps1
```

### 3. Verificar en el Navegador
1. Abre `https://drive-plus.com.ar/rankings`
2. Abre DevTools (F12)
3. Ve a la pestaña "Console"
4. Busca el log: `DEBUG Rankings - Primer jugador con partidos:`
5. Verifica qué datos está recibiendo el frontend

### 4. Limpiar Caché
Si los datos son correctos pero no se muestran:
1. DevTools → Application → Storage
2. Limpia:
   - Local Storage
   - Session Storage
   - Cache Storage
3. Hard refresh: `Ctrl + Shift + R`

### 5. Verificar Network
1. DevTools → Network
2. Filtra por "ranking"
3. Verifica la respuesta del endpoint
4. Asegúrate de que `partidos_ganados` esté en la respuesta

## Posibles Causas

### A. Caché del Frontend (Hostinger)
El build viejo está en caché. Solución:
- Hacer nuevo build
- Subir a Hostinger
- Limpiar caché del navegador

### B. Caché del Navegador
El navegador tiene datos viejos. Solución:
- Hard refresh
- Limpiar storage
- Modo incógnito

### C. Caché del Backend
El endpoint está sirviendo datos viejos. Solución:
- Esperar 60 segundos (TTL del caché)
- O llamar al endpoint `/ranking/clear-cache` (requiere admin)

## Verificación Final
Una vez hecho el deploy, verifica que:
1. El console.log aparezca en la consola
2. Los datos incluyan `partidos_ganados > 0` para jugadores con victorias
3. La tabla muestre las victorias correctamente

## Remover Debug
Una vez verificado, remover los console.logs:
1. Editar `frontend/src/pages/Rankings.tsx`
2. Eliminar los bloques de `console.log('DEBUG Rankings...')`
3. Commit y push
4. Rebuild y redeploy
