# Script de Deploy para Hostinger - Drive+
# Fecha: 2026-02-06

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Deploy Drive+ a Hostinger" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar que existe la carpeta dist
if (-Not (Test-Path "frontend/dist")) {
    Write-Host "❌ Error: No se encuentra la carpeta frontend/dist" -ForegroundColor Red
    Write-Host "   Ejecuta primero: cd frontend && npm run build" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Carpeta dist encontrada" -ForegroundColor Green
Write-Host ""

# Contar archivos
$archivos = Get-ChildItem -Path "frontend/dist" -Recurse -File
$totalArchivos = $archivos.Count
$totalSize = ($archivos | Measure-Object -Property Length -Sum).Sum / 1MB

Write-Host "📦 Archivos a subir:" -ForegroundColor Cyan
Write-Host "   Total: $totalArchivos archivos" -ForegroundColor White
Write-Host "   Tamaño: $([math]::Round($totalSize, 2)) MB" -ForegroundColor White
Write-Host ""

# Mostrar estructura
Write-Host "Estructura del build:" -ForegroundColor Cyan
Write-Host "   frontend/dist/" -ForegroundColor White
Write-Host "   - index.html" -ForegroundColor White
Write-Host "   - .htaccess" -ForegroundColor White
$assetsCount = (Get-ChildItem -Path 'frontend/dist/assets' -File).Count
Write-Host "   - assets/ ($assetsCount archivos)" -ForegroundColor White
Write-Host "   - manifest.json" -ForegroundColor White
Write-Host "   - sw.js" -ForegroundColor White
Write-Host "   - otros archivos PWA" -ForegroundColor White
Write-Host ""

# Verificar archivos críticos
$archivosCriticos = @(
    "frontend/dist/index.html",
    "frontend/dist/.htaccess",
    "frontend/dist/manifest.json"
)

$todoOk = $true
foreach ($archivo in $archivosCriticos) {
    if (Test-Path $archivo) {
        Write-Host "   ✅ $($archivo.Split('/')[-1])" -ForegroundColor Green
    } else {
        Write-Host "   ❌ $($archivo.Split('/')[-1]) - FALTA" -ForegroundColor Red
        $todoOk = $false
    }
}

Write-Host ""

if (-Not $todoOk) {
    Write-Host "❌ Faltan archivos críticos. Regenera el build." -ForegroundColor Red
    exit 1
}

# Instrucciones
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  INSTRUCCIONES DE DEPLOY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "📋 Pasos a seguir:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Accede a Hostinger Panel" -ForegroundColor White
Write-Host "    https://hpanel.hostinger.com" -ForegroundColor Gray
Write-Host ""

Write-Host "2. Abre File Manager" -ForegroundColor White
Write-Host "    - Selecciona tu dominio: drive-plus.com.ar" -ForegroundColor Gray
Write-Host "    - Click en 'File Manager'" -ForegroundColor Gray
Write-Host ""

Write-Host "3. Navega a public_html" -ForegroundColor White
Write-Host "    - Esta es la carpeta raiz de tu sitio" -ForegroundColor Gray
Write-Host ""

Write-Host "4. Limpia archivos antiguos (IMPORTANTE)" -ForegroundColor White
Write-Host "    - Elimina TODOS los archivos antiguos" -ForegroundColor Gray
Write-Host "    - Excepto .htaccess si quieres conservarlo" -ForegroundColor Gray
Write-Host ""

Write-Host "5. Sube los archivos nuevos" -ForegroundColor White
Write-Host "    - Click en 'Upload Files'" -ForegroundColor Gray
Write-Host "    - Selecciona TODO el contenido de:" -ForegroundColor Gray
Write-Host "      $((Get-Location).Path)\frontend\dist\" -ForegroundColor Cyan
Write-Host "    - Incluye la carpeta assets/ completa" -ForegroundColor Gray
Write-Host ""

Write-Host "6. Verifica la estructura final" -ForegroundColor White
Write-Host "    public_html/" -ForegroundColor Gray
Write-Host "    - index.html" -ForegroundColor Gray
Write-Host "    - .htaccess" -ForegroundColor Gray
Write-Host "    - assets/ (con todos los archivos JS y CSS)" -ForegroundColor Gray
Write-Host "    - manifest.json" -ForegroundColor Gray
Write-Host "    - otros archivos" -ForegroundColor Gray
Write-Host ""

Write-Host "7. Prueba el sitio" -ForegroundColor White
Write-Host "    https://drive-plus.com.ar" -ForegroundColor Cyan
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  VERIFICACIÓN POST-DEPLOY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Checklist:" -ForegroundColor Yellow
Write-Host "   [ ] La página principal carga correctamente" -ForegroundColor White
Write-Host "   [ ] Puedes navegar entre páginas (sin 404)" -ForegroundColor White
Write-Host "   [ ] El login funciona" -ForegroundColor White
Write-Host "   [ ] Las imágenes cargan" -ForegroundColor White
Write-Host "   [ ] No hay errores en la consola (F12)" -ForegroundColor White
Write-Host "   [ ] Las llamadas API van a Railway" -ForegroundColor White
Write-Host "   [ ] Puedes ver torneos y fixture" -ForegroundColor White
Write-Host "   [ ] El botón de cambiar horario funciona" -ForegroundColor White
Write-Host "   [ ] El botón de ver restricciones funciona" -ForegroundColor White
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  NUEVAS FUNCIONALIDADES" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Este build incluye:" -ForegroundColor Green
Write-Host "   ✅ Fix de zona horaria (horarios correctos)" -ForegroundColor White
Write-Host "   ✅ Cambio manual de horarios con verificación" -ForegroundColor White
Write-Host "   ✅ Ver restricciones horarias de parejas" -ForegroundColor White
Write-Host "   ✅ Fix de algoritmo de restricciones" -ForegroundColor White
Write-Host "   ✅ Fix de intervalo de 3 horas entre partidos" -ForegroundColor White
Write-Host "   ✅ UI mejorada y más compacta" -ForegroundColor White
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  BACKEND" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Backend ya actualizado en Railway" -ForegroundColor Green
Write-Host "   URL: https://drive-plus-production.up.railway.app" -ForegroundColor Cyan
Write-Host "   No necesitas hacer nada en Railway" -ForegroundColor Gray
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Ruta del build: $((Get-Location).Path)\frontend\dist\" -ForegroundColor Yellow
Write-Host ""
Write-Host "Tip: Puedes comprimir la carpeta dist en un ZIP" -ForegroundColor Cyan
Write-Host "   y subirla directamente en Hostinger File Manager" -ForegroundColor Cyan
Write-Host ""

# Preguntar si quiere crear un ZIP
Write-Host "¿Quieres crear un archivo ZIP para facilitar la subida? (S/N): " -ForegroundColor Yellow -NoNewline
$respuesta = Read-Host

if ($respuesta -eq "S" -or $respuesta -eq "s") {
    $zipPath = "frontend/drive-plus-build-$(Get-Date -Format 'yyyy-MM-dd-HHmm').zip"
    
    Write-Host ""
    Write-Host "Creando archivo ZIP..." -ForegroundColor Cyan
    
    try {
        Compress-Archive -Path "frontend/dist/*" -DestinationPath $zipPath -Force
        Write-Host "✅ ZIP creado exitosamente: $zipPath" -ForegroundColor Green
        Write-Host ""
        Write-Host "   Sube este archivo a Hostinger y descomprímelo en public_html/" -ForegroundColor White
    } catch {
        Write-Host "Error al crear ZIP: $_" -ForegroundColor Red
    }
} else {
    Write-Host ""
    Write-Host "Ok, sube los archivos manualmente desde frontend/dist/" -ForegroundColor White
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ¡Listo para deploy! 🚀" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
