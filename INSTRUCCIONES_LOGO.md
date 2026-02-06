# Instrucciones para Cambiar el Logo

## Paso 1: Preparar el Logo

Tu logo actual tiene fondo negro. Necesitas:

1. **Abrir la imagen en un editor** (Photoshop, GIMP, Photopea, etc.)
2. **Eliminar el fondo negro** y dejarlo transparente
3. **Guardar como PNG** con transparencia
4. **Nombre del archivo**: `logo-drive.png`

### Opción rápida con Photopea (online gratis):

1. Ve a https://www.photopea.com
2. Abre tu imagen del logo
3. Selecciona la herramienta "Varita mágica" (Magic Wand)
4. Click en el fondo negro
5. Presiona Delete
6. File > Export As > PNG
7. Guarda como `logo-drive.png`

## Paso 2: Reemplazar el Logo

Una vez tengas el PNG transparente:

1. **Copia el archivo** `logo-drive.png` a:
   - `frontend/public/logo-drive.png`

2. **Ejecuta el build nuevamente**:
   ```bash
   cd frontend
   npm run build
   ```

3. El logo se copiará automáticamente a `frontend/dist/`

## Paso 3: Verificar

El logo se usa en:
- Navbar (esquina superior izquierda)
- Página de Login
- Página de Register
- Landing page

Todos estos componentes ya están configurados para mantener las proporciones con `object-contain`.

## Alternativa: Usar el Logo Actual

Si quieres usar el logo con fondo negro tal como está:

1. Simplemente copia tu imagen a `frontend/public/logo-drive.png`
2. Ejecuta `npm run build` en frontend
3. El fondo negro se verá bien en fondos claros

## Tamaños Actuales

- **Navbar**: 32x32px (w-8 h-8)
- **Landing**: 32x32px en mobile, 40x40px en desktop
- **Login/Register**: 80x80px en mobile, 112x112px en desktop

Todos usan `object-contain` para mantener proporciones sin distorsión.
