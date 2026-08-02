@echo off
cd /d "%~dp0"
if not exist "node_modules\electron\dist\electron.exe" (
  echo Installing shell dependencies...
  call npm install
)
start "" /B cmd /c "npm start"
