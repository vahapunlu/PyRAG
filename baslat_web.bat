@echo off
echo ===================================================
echo PyRAG - Web Uygulamasi Baslatiliyor...
echo ===================================================

echo.
echo 1. Backend (API) Baslatiliyor...
start "PyRAG API (Backend)" cmd /k "python main.py serve"

echo.
echo 2. Frontend (Web Arayuzu) Hazirlaniyor...
cd web

if not exist node_modules (
    echo    Ilk kurulum yapiliyor (npm install)...
    call npm install
)

echo.
echo 3. Web Arayuzu Baslatiliyor...
echo    Lutfen tarayicinizda http://localhost:3000 adresini acin.
echo.
npm run dev
pause
