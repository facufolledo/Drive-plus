# Instrucciones para Deploy en Hostinger

## ✅ Build Completado

El build de producción se ha generado exitosamente en la carpeta `frontend/dist/`

**Fecha del build**: 2026-02-06
**Tamaño total**: ~1.5 MB (comprimido)
**Archivos generados**: 35 archivos

---

## 📦 Archivos a Subir

Debes subir **TODO el contenido** de la carpeta `frontend/dist/` a Hostinger.

**Ruta local**: `D:\Users\Facundo\Desktop\Proyecto\frontend\dist\`

---

## 🚀 Pasos para Subir a Hostinger

### Opción 1: Via File Manager (Recomendado)

1. **Accede al Panel de Hostinger**
   - Ve a https://hpanel.hostinger.com
   - Inicia sesión con tu cuenta

2. **Abre el File Manager**
   - En tu dominio `drive-plus.com.ar`
   - Click en "File Manager"

3. **Navega a la carpeta public_html**
   - Esta es la carpeta raíz de tu sitio web
   - Si hay archivos antiguos, **elimínalos primero** (excepto `.htaccess` si existe)

4. **Sube los archivos**
   - Click en "Upload Files"
   - Selecciona **TODOS** los archivos de `frontend/dist/`
   - Incluye la carpeta `assets/` completa
   - Incluye `index.html`
   - Incluye cualquier archivo `.htaccess` si existe en dist

5. **Verifica la estructura**
   ```
   public_html/
   ├── index.html
   ├── assets/
   │   ├── index-dkyo1tzS.css
   │   ├── index-WVwqVTXg.js
   │   ├── react-vendor-CW7GCVTA.js
   │   ├── firebase-CKHgsykf.js
   │   ├── TorneoDetalle-vGIVNTXy.js
   │   ├── charts-BRSS6Muj.js
   │   └── ... (todos los demás archivos)
   └── .htaccess (si existe)
   ```

### Opción 2: Via FTP

1. **Conecta via FTP**
   - Host: `ftp.drive-plus.com.ar` (o el que te proporcione Hostinger)
   - Usuario: Tu usuario FTP
   - Contraseña: Tu contraseña FTP
   - Puerto: 21

2. **Navega a public_html**

3. **Elimina archivos antiguos** (si existen)

4. **Sube todo el contenido de `frontend/dist/`**

---

## 🔧 Configuración Adicional

### Archivo .htaccess (Importante para React Router)

Si no existe un `.htaccess` en `frontend/dist/`, créalo en `public_html/` con este contenido:

```apache
<IfModule mod_rewrite.c>
  RewriteEngine On
  RewriteBase /
  RewriteRule ^index\.html$ - [L]
  RewriteCond %{REQUEST_FILENAME} !-f
  RewriteCond %{REQUEST_FILENAME} !-d
  RewriteCond %{REQUEST_FILENAME} !-l
  RewriteRule . /index.html [L]
</IfModule>

# Habilitar compresión GZIP
<IfModule mod_deflate.c>
  AddOutputFilterByType DEFLATE text/html text/plain text/xml text/css text/javascript application/javascript application/json
</IfModule>

# Cache para assets estáticos
<IfModule mod_expires.c>
  ExpiresActive On
  ExpiresByType image/jpg "access plus 1 year"
  ExpiresByType image/jpeg "access plus 1 year"
  ExpiresByType image/gif "access plus 1 year"
  ExpiresByType image/png "access plus 1 year"
  ExpiresByType image/svg+xml "access plus 1 year"
  ExpiresByType text/css "access plus 1 month"
  ExpiresByType application/javascript "access plus 1 month"
  ExpiresByType application/pdf "access plus 1 month"
  ExpiresByType text/x-javascript "access plus 1 month"
</IfModule>
```

---

## ✅ Verificación Post-Deploy

1. **Abre el sitio**: https://drive-plus.com.ar

2. **Verifica que cargue correctamente**:
   - ✅ La página principal se ve bien
   - ✅ Puedes navegar entre páginas
   - ✅ El login funciona
   - ✅ Las imágenes cargan

3. **Prueba funcionalidades críticas**:
   - Login/Registro
   - Ver torneos
   - Ver fixture
   - Cambiar horarios (nueva funcionalidad)
   - Ver restricciones horarias (nueva funcionalidad)

4. **Verifica la consola del navegador** (F12):
   - No debe haber errores de CORS
   - Las llamadas a la API deben ir a: `https://drive-plus-production.up.railway.app`

---

## 🔍 Troubleshooting

### Si el sitio no carga:
- Verifica que `index.html` esté en la raíz de `public_html/`
- Verifica que la carpeta `assets/` esté completa
- Limpia la caché del navegador (Ctrl + Shift + R)

### Si las rutas no funcionan (404 en /torneos, etc.):
- Verifica que el archivo `.htaccess` esté presente
- Verifica que mod_rewrite esté habilitado en Hostinger

### Si hay errores de API:
- Verifica que el backend en Railway esté funcionando
- Verifica que las variables de entorno en `.env.production` sean correctas
- Verifica CORS en el backend (debe incluir drive-plus.com.ar)

---

## 📝 Cambios Incluidos en Este Build

✅ **Fix de zona horaria**: Los horarios ahora se muestran correctamente (sin -3 horas)
✅ **Cambio manual de horarios**: Botón compacto junto a cada partido con verificación en tiempo real
✅ **Ver restricciones horarias**: Botón con ícono de reloj en zonas, fixture y parejas
✅ **Fix de restricciones**: El algoritmo ahora respeta correctamente las restricciones horarias
✅ **Fix de intervalo 3 horas**: Los partidos se generan respetando 180 minutos entre partidos del mismo jugador
✅ **UI mejorada**: Botones más compactos y mejor diseño

---

## 🎯 Backend en Railway

El backend ya está actualizado en Railway con todos los cambios:
- URL: https://drive-plus-production.up.railway.app
- Último deploy: 2026-02-06
- Incluye todos los fixes de restricciones y zona horaria

**No necesitas hacer nada en Railway**, el backend ya está listo.

---

## 📞 Soporte

Si tienes problemas:
1. Verifica los logs en la consola del navegador (F12)
2. Verifica que el backend responda: https://drive-plus-production.up.railway.app/health
3. Limpia caché del navegador
4. Prueba en modo incógnito

---

**¡Listo para producción! 🚀**
