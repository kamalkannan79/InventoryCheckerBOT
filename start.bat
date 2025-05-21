@echo off
echo Starting FastAPI backend...
cd "C:\Users\Kamalesh.K\Desktop\SPI Projects\InventoryCheckerBot"
start cmd /k "call .venv\Scripts\activate && python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000"


echo Starting React frontend...
cd "C:\Users\Kamalesh.K\Desktop\SPI Projects\InventoryCheckerBot\chatbot"
start cmd /k "npm start"

echo Both backend and frontend are starting...
