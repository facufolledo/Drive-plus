# Cómo Cambiar el Logo

## Problema Actual
El logo actual tiene fondo negro y se ve como un cuadrado. Necesitas reemplazarlo con tu nuevo logo sin fondo.

## Solución Rápida

### Paso 1: Preparar tu logo sin fondo

**Opción A - Usar Remove.bg (Más fácil)**
1. Ve a https://www.remove.bg
2. Sube tu imagen del logo
3. Automáticamente quitará el fondo
4. Descarga el PNG transparente

**Opción B - Usar Photopea (Más control)**
1. Ve a https://www.photopea.com
2. File > Open > Selecciona tu logo
3. Herramienta "Varita mágica" (W)
4. Click en el fondo negro
5. Presiona Delete
6. File > Export As > PNG
7. Descarga

### Paso 2: Reemplazar el archivo

1. **Guarda tu nuevo logo** con el nombre exacto: `logo-drive.png`

2. **Cópialo a esta ubicación** (reemplazando el actual):
   ```
   D:\Users\Facundo\Desktop\Proyecto\frontend\public\logo-drive.png
   ```

3. **Recarga el navegador** (Ctrl + Shift + R para limpiar caché)

### Paso 3: Verificar

Abre http://localhost:5173 y deberías ver tu nuevo logo sin fondo.

---

## Si quieres usar el logo que me mostraste

El logo que me mostraste tiene:
- Fondo negro
- Texto "Drive+" en azul
- Tres puntos a la izquierda

Para usarlo sin el fondo negro:

1. **Abre la imagen en un editor**
2. **Selecciona y elimina el fondo negro**
3. **Guarda como PNG transparente**
4. **Copia a `frontend/public/logo-drive.png`**

---

## Tamaños del Logo

El logo se mostrará en estos tamaños:
- **Navbar**: 32x32 píxeles
- **Login/Register**: 80x80 píxeles (mobile), 112x112 píxeles (desktop)
- **Landing**: 32x32 píxeles (mobile), 40x40 píxeles (desktop)

Recomendación: Usa una imagen de al menos 256x256 píxeles para que se vea nítida.

---

## Alternativa: Usar solo el ícono

Si solo quieres usar el ícono (el símbolo +D sin el texto "Drive+"):

1. Recorta solo esa parte
2. Elimina el fondo
3. Guarda como `logo-drive.png`
4. El texto "Drive+" ya está en el código, así que se verá bien

---

## Después de cambiar el logo

Una vez que hayas reemplazado el archivo:

1. **En desarrollo**: Solo recarga el navegador (Ctrl + Shift + R)
2. **Para producción**: Ejecuta `npm run build` en la carpeta frontend
3. **Sube a Hostinger**: Sigue las instrucciones de `INSTRUCCIONES_DEPLOY_HOSTINGER.md`

---

## Troubleshooting

**Si no ves el cambio:**
- Limpia la caché del navegador (Ctrl + Shift + R)
- Verifica que el archivo se llame exactamente `logo-drive.png`
- Verifica que esté en `frontend/public/`
- Reinicia el servidor de desarrollo (Ctrl + C y luego `npm run dev`)

**Si se ve distorsionado:**
- Asegúrate de que sea PNG transparente
- Verifica que tenga buena resolución (mínimo 256x256px)
- Los componentes ya tienen `object-contain` para mantener proporciones
