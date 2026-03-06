$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [Environment]::GetFolderPath("Desktop")
# On OneDrive setups, it might be OneDrive\Desktop
$ShortcutPath = Join-Path $DesktopPath "Voice-txtSTT.lnk"

# Crear el acceso directo
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "uv.exe"  # Asumiendo que uv está en el PATH global
$Shortcut.Arguments = "run main.py"
$Shortcut.WorkingDirectory = "C:\Users\agude\Documents\Whisper\Voice-txt"
$Shortcut.Description = "Launch Voice-txt STT App"
$Shortcut.IconLocation = "C:\Users\agude\Documents\Whisper\Voice-txt\app\icon.ico"

$Shortcut.Save()

Write-Host "Acceso directo creado con éxito en tu Escritorio: $ShortcutPath"
