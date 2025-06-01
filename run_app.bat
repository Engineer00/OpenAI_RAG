@echo off
echo Starting AI Document Assistant...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed! Please install Python 3.7 or higher.
    pause
    exit /b 1
)

REM Check if requirements are installed
echo Checking and installing requirements...
pip install -r requirements.txt

REM Check if .env file exists
if not exist .env (
    echo Creating .env file...
    echo OPENAI_API_KEY=your-api-key-here > .env
    echo Please edit the .env file and add your OpenAI API key!
    pause
)

REM Run the Streamlit app
echo Starting the application...
echo The app will open in your default web browser.
echo.
streamlit run chatbot_ui.py

pause 