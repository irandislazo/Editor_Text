@echo off
setlocal
cd /d "%~dp0"
echo === 1/3 Monaco (se empaqueta para funcionar sin internet) ===
if not exist monaco\vs\loader.js (
  if exist "%USERPROFILE%\.bloc_monaco\monaco\vs\loader.js" (
    xcopy /e /i /y "%USERPROFILE%\.bloc_monaco\monaco" monaco >nul
  ) else (
    where npm >nul 2>nul && (npm pack monaco-editor@0.52.2 && mkdir monaco && tar -xzf monaco-editor-0.52.2.tgz -C monaco --strip-components=2 package/min/vs)
  )
)
if not exist monaco\vs\loader.js (
  echo Falta Monaco. Abre un .py en la app una vez con internet y vuelve a ejecutar este archivo.
  exit /b 1
)
echo === 2/3 Generando la app ===
set ICON=
if exist icon.ico set ICON=--icon icon.ico
flet pack main.py --name BlocDeNotas -y --onedir %ICON% --add-data "monaco;monaco"
if errorlevel 1 exit /b 1
echo === 3/3 Creando instalador ===
set ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe
if not exist "%ISCC%" set ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe
if not exist "%ISCC%" set ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe
if not exist "%ISCC%" (
  echo Instala Inno Setup 6 ^(gratis: https://jrsoftware.org/isdl.php^) y vuelve a ejecutar.
  exit /b 1
)
"%ISCC%" installer.iss
echo Listo: installer\BlocDeNotas-Setup.exe
