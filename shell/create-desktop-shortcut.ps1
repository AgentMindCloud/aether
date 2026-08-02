# Aether — create Windows 11 Desktop shortcut (run once)
# Right-click → Run with PowerShell, or:
#   powershell -ExecutionPolicy Bypass -File .\create-desktop-shortcut.ps1

$ErrorActionPreference = "Stop"
$shellDir = $PSScriptRoot
$repoRoot = Split-Path $shellDir -Parent
$desktop = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktop "Aether.lnk"
$vbsPath = Join-Path $shellDir "Start-Aether.vbs"
$batPath = Join-Path $shellDir "Start-Aether.bat"

# Launcher bat (visible fallback)
$bat = @"
@echo off
cd /d "$shellDir"
if not exist "node_modules\electron\dist\electron.exe" (
  echo Installing shell dependencies...
  call npm install
)
start "" /B cmd /c "npm start"
"@
Set-Content -Path $batPath -Value $bat -Encoding ASCII

# VBS = no console window
$vbs = @"
Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "$shellDir"
WshShell.Run "cmd /c npm start", 0, False
"@
Set-Content -Path $vbsPath -Value $vbs -Encoding ASCII

$wsh = New-Object -ComObject WScript.Shell
$sc = $wsh.CreateShortcut($shortcutPath)
$sc.TargetPath = "wscript.exe"
$sc.Arguments = """$vbsPath"""
$sc.WorkingDirectory = $shellDir
$sc.WindowStyle = 7
$sc.Description = "Aether Presence — tray + panel (Ctrl+Alt+A)"
$sc.IconLocation = "shell32.dll,13"
$sc.Save()

Write-Host ""
Write-Host "Desktop shortcut created: $shortcutPath"
Write-Host "Double-click 'Aether' on your Desktop to start."
Write-Host "First run may install npm deps and spawn the Python runtime."
Write-Host ""
