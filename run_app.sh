#!/bin/bash

echo "Starting AI Document Assistant..."
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python is not installed! Please install Python 3.7 or higher."
    exit 1
fi

# Check if requirements are installed
echo "Checking and installing requirements..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Creating .env file..."
    echo "OPENAI_API_KEY=your-api-key-here" > .env
    echo "Please edit the .env file and add your OpenAI API key!"
    read -p "Press Enter to continue..."
fi

# Run the Streamlit app
echo "Starting the application..."
echo "The app will open in your default web browser."
echo
streamlit run chatbot_ui.py 