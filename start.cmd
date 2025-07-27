@echo off
echo Starting ResumePard Web Application...
echo.
echo Make sure you're in the ResumePard directory with virtual environment activated
echo.
streamlit run app.py --server.port 8501 --server.address localhost
pause
