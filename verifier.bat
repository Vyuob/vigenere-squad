@echo off
setlocal
cd /d "%~dp0"
call "%~dp0scripts\_uv.bat"
if errorlevel 1 goto erreur
uv sync --frozen --extra dev
if errorlevel 1 goto erreur
echo.
echo [1/3] Tests...
uv run --frozen pytest -q
if errorlevel 1 goto erreur
echo.
echo [2/3] Empreintes SHA-256 (SHA256SUMS)...
uv run --frozen python scripts/hashes.py --check
if errorlevel 1 goto erreur
echo.
echo [3/3] Signature minisign...
where minisign >nul 2>&1
if errorlevel 1 (
  echo minisign non installe : etape ignoree. Installation : winget install jedisct1.minisign
) else (
  minisign -Vm SHA256SUMS -p minisign.pub
  if errorlevel 1 goto erreur
)
echo.
echo OK : tout est conforme.
pause
exit /b 0
:erreur
echo.
echo ECHEC de la verification.
pause
exit /b 1
