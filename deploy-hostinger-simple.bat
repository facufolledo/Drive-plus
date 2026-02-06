@echo off
chcp 65001 >nul
echo ========================================
echo   Deploy Drive+ a Hostinger
echo ========================================
echo.

if not exist "frontend\dist" (
    echo ERROR: No se encuentra la carpeta frontend\dist
    echo Ejecuta primero: cd frontend ^&^& npm run build
    exit /b 1
)

echo OK: Carpeta dist encontrada
echo.

echo Archivos a subir:
dir /s /b frontend\dist | find /c ":" > temp.txt
set /p TOTAL=<temp.txt
del temp.txt
echo   Total: %TOTAL% archivos
echo.

echo Estructura del build:
echo   frontend\dist\
echo   - index.html
echo   - .htaccess
echo   - assets\ (archivos JS y CSS)
echo   - manifest.json
echo   - sw.js
echo.

echo ========================================
echo   INSTRUCCIONES DE DEPLOY
echo ========================================
echo.

echo Pasos a seguir:
echo.
echo 1. Accede a Hostinger Panel
echo    https://hpanel.hostinger.com
echo.
echo 2. Abre File Manager
echo    - Selecciona tu dominio: drive-plus.com.ar
echo    - Click en 'File Manager'
echo.
echo 3. Navega a public_html
echo    - Esta es la carpeta raiz de tu sitio
echo.
echo 4. Limpia archivos antiguos (IMPORTANTE)
echo    - Elimina TODOS los archivos antiguos
echo    - Excepto .htaccess si quieres conservarlo
echo.
echo 5. Sube los archivos nuevos
echo    - Click en 'Upload Files'
echo    - Selecciona TODO el contenido de:
echo      %CD%\frontend\dist\
echo    - Incluye la carpeta assets\ completa
echo.
echo 6. Verifica la estructura final
echo    public_html\
echo    - index.html
echo    - .htaccess
echo    - assets\ (con todos los archivos JS y CSS)
echo    - manifest.json
echo    - otros archivos
echo.
echo 7. Prueba el sitio
echo    https://drive-plus.com.ar
echo.

echo ========================================
echo   VERIFICACION POST-DEPLOY
echo ========================================
echo.

echo Checklist:
echo   [ ] La pagina principal carga correctamente
echo   [ ] Puedes navegar entre paginas (sin 404)
echo   [ ] El login funciona
echo   [ ] Las imagenes cargan
echo   [ ] No hay errores en la consola (F12)
echo   [ ] Las llamadas API van a Railway
echo   [ ] Puedes ver torneos y fixture
echo   [ ] El boton de cambiar horario funciona
echo   [ ] El boton de ver restricciones funciona
echo.

echo ========================================
echo   NUEVAS FUNCIONALIDADES
echo ========================================
echo.

echo Este build incluye:
echo   - Fix de zona horaria (horarios correctos)
echo   - Cambio manual de horarios con verificacion
echo   - Ver restricciones horarias de parejas
echo   - Fix de algoritmo de restricciones
echo   - Fix de intervalo de 3 horas entre partidos
echo   - UI mejorada y mas compacta
echo.

echo ========================================
echo   BACKEND
echo ========================================
echo.

echo Backend ya actualizado en Railway
echo   URL: https://drive-plus-production.up.railway.app
echo   No necesitas hacer nada en Railway
echo.

echo ========================================
echo.
echo Ruta del build: %CD%\frontend\dist\
echo.
echo Tip: Puedes comprimir la carpeta dist en un ZIP
echo   y subirla directamente en Hostinger File Manager
echo.

echo ========================================
echo   Listo para deploy!
echo ========================================
echo.

pause
