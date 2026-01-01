@echo off
echo Starting ClearBill Application...

echo.
echo [1/2] Starting Backend Server on port 8001...
cd backend
start "Backend Server" cmd /k "..\\myenv\\Scripts\\activate && python main.py"

echo.
echo [2/2] Starting Frontend Development Server...
cd ..\\frontend\\frontapp
start "Frontend Server" cmd /k "npm run dev"

echo.
echo ✅ Both servers are starting...
echo 📱 Frontend: http://localhost:5173
echo 🔧 Backend API: http://localhost:8001
echo 📚 API Docs: http://localhost:8001/docs
echo.
echo Press any key to exit...
pause > nul