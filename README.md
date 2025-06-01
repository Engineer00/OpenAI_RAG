# Advanced OpenAI RAG System with Beautiful UI

A comprehensive RAG (Retrieval Augmented Generation) system with a beautiful web interface, built using OpenAI's latest features and Streamlit.

## Features

- Beautiful and responsive web interface
- Document upload and processing
- Vector store creation and management
- Document embedding and similarity search
- Advanced document retrieval using OpenAI's Assistants API
- Interactive chat interface with context-aware responses
- Support for multiple documents
- Code interpreter capabilities
- Automatic document chunking and processing

## Prerequisites

- Python 3.7+
- OpenAI API key with access to:
  - GPT-4-1106-preview model
  - text-embedding-3-small model
  - Assistants API
  - Vector Store API
- Document(s) to chat with (PDF, TXT, DOCX)

## Quick Start

### Windows
1. Double-click `run_app.bat`
2. The script will:
   - Check Python installation
   - Install requirements
   - Create .env file if needed
   - Start the application

### Unix-based Systems (Linux/Mac)
1. Open terminal in the project directory
2. Make the script executable:
```bash
chmod +x run_app.sh
```
3. Run the script:
```bash
./run_app.sh
```

## Manual Setup

1. Install the required packages:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file in the project root with your OpenAI API key:
```
OPENAI_API_KEY=your-api-key-here
```

3. Run the Streamlit UI:
```bash
streamlit run chatbot_ui.py
```

## UI Features

### Document Upload
- Drag and drop or click to upload documents
- Supports PDF, TXT, and DOCX formats
- Automatic document processing
- Status indicators for processing steps

### Chat Interface
- Clean and modern chat design
- Real-time message updates
- Loading indicators
- Error handling and user feedback

### Status Panel
- Vector store status
- Assistant status
- Thread status
- Processing indicators

## Advanced Features

### Vector Store
- Creates and manages a vector store for efficient document retrieval
- Uses OpenAI's text-embedding-3-small model for embeddings
- Supports similarity search across multiple documents

### Document Processing
- Automatic document chunking and processing
- Support for multiple document formats
- Efficient document retrieval using embeddings

### Assistant Capabilities
- Retrieval-based question answering
- Code interpreter for complex queries
- Context-aware responses
- Multiple document support

## Troubleshooting

1. If the app doesn't start:
   - Make sure Python 3.7+ is installed
   - Check if all requirements are installed
   - Verify your OpenAI API key in the .env file

2. If document upload fails:
   - Check file format (PDF, TXT, or DOCX)
   - Ensure file size is within limits
   - Verify OpenAI API access

3. If chat doesn't work:
   - Check OpenAI API key permissions
   - Verify document processing status
   - Check internet connection

## Notes

- The OpenAI Assistants API with retrieval capabilities incurs additional costs
- Vector store operations may take longer for large documents
- The system uses GPT-4-1106-preview model by default
- Make sure your OpenAI API key has access to all required features 