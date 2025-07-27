@echo off
echo Starting ResumePard Web Application...
echo.
echo Activating virtual environment...
call resume_parser_env\Scripts\activate.bat
echo.
echo Starting Streamlit server...
echo Open your browser and navigate to: http://localhost:8501
echo.
echo To stop the application, press Ctrl+C in this window
echo.
streamlit run app.py
pause
