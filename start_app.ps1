# ResumePard Startup Script (PowerShell)
Write-Host "🚀 Starting ResumePard Web Application..." -ForegroundColor Green
Write-Host ""

# Check if virtual environment exists
if (Test-Path "resume_parser_env\Scripts\activate.bat") {
    Write-Host "✅ Found virtual environment" -ForegroundColor Green
    
    # Activate virtual environment and start Streamlit
    Write-Host "🔄 Activating virtual environment..." -ForegroundColor Yellow
    & "resume_parser_env\Scripts\activate.bat"
    
    Write-Host "🌐 Starting Streamlit server..." -ForegroundColor Yellow
    Write-Host "📱 Open your browser and navigate to: http://localhost:8501" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "🛑 To stop the application, press Ctrl+C in this window" -ForegroundColor Red
    Write-Host ""
    
    # Start Streamlit
    & "resume_parser_env\Scripts\python.exe" -m streamlit run app.py
    
} else {
    Write-Host "❌ Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please make sure the virtual environment is set up correctly." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To set up the environment, run:" -ForegroundColor Yellow
    Write-Host "python -m venv resume_parser_env" -ForegroundColor Cyan
    Write-Host "resume_parser_env\Scripts\activate" -ForegroundColor Cyan
    Write-Host "pip install -r requirements.txt" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
