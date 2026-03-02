param (
    [int]$Port = 8005
)

Write-Host "Buscando procesos en el puerto $Port..." -ForegroundColor Cyan

$process = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | Select-Object -First 1

if ($process) {
    $found_pid = $process.OwningProcess
    $processInfo = Get-Process -Id $found_pid
    Write-Host "Encontrado proceso: $($processInfo.Name) (PID: $found_pid)" -ForegroundColor Yellow
    
    try {
        Stop-Process -Id $found_pid -Force
        Write-Host "Proceso terminado con éxito. El puerto $Port ahora debería estar libre." -ForegroundColor Green
    } catch {
        Write-Host "Error al intentar cerrar el proceso: $_" -ForegroundColor Red
    }
} else {
    Write-Host "No se encontró ningún proceso escuchando en el puerto $Port." -ForegroundColor Gray
}
