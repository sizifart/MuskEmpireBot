@Echo Off
SETLOCAL EnableDelayedExpansion
for /F "tokens=1,2 delims=#" %%a in ('"prompt #$H#$E# & echo on & for %%b in (1) do rem"') do (
set "DEL=%%a"
)
echo Installing NodeJS...
winget install Schniz.fnm
fnm use --install-if-missing 20
node -v
npm -v
echo Installing Pnpm...
iwr https://get.pnpm.io/install.ps1 -useb | iex
echo.
pause
exit
:colorEcho
echo off
<nul set /p ".=%DEL%" > "%~2"
findstr /v /a:%1 /R "^$" "%~2" nul
del "%~2" > nul 2>&1i