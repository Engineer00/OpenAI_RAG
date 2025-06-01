# Trivial change to force redeploy
import os
from typing import List, Optional
import openai
# from dotenv import load_dotenv
import streamlit as st
from streamlit_chat import message
import tempfile
import sys
import numpy as np
from io import BytesIO

# Try to import from installed package, fallback to local path for dev
try:
    from streamlit_audio_recorder.st_audiorec import st_audiorec  # type: ignore[import]
except ImportError:
    sys.path.append(os.path.join(os.path.dirname(__file__), 'streamlit_audio_recorder', 'st_audiorec'))
    from streamlit_audio_recorder.st_audiorec import st_audiorec  # type: ignore[import]

# Load environment variables from .env file
# load_dotenv()

# Get the API key and resource IDs from environment variables
# api_key = os.getenv("OPENAI_API_KEY")
# assistant_id = os.getenv("ASSISTANT_ID")
# thread_id = os.getenv("THREAD_ID")
# vector_store_id = os.getenv("VECTOR_STORE_ID")

api_key = st.secrets["OPENAI_API_KEY"]
assistant_id = st.secrets["ASSISTANT_ID"]
thread_id = st.secrets["THREAD_ID"]
vector_store_id = st.secrets["VECTOR_STORE_ID"]

if not api_key:
    st.error("OpenAI API key not found. Please check your .env file.")
    st.stop()

# Initialize OpenAI client
client = openai.OpenAI(api_key=api_key)

def transcribe_audio(audio_bytes):
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp.flush()
        with open(tmp.name, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="en"
            )
    return transcript.text

def synthesize_speech(text, voice="alloy", response_format="mp3"):
    response = client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=text,
        response_format=response_format
    )
    return response.content

class AdvancedRAG:
    def __init__(self):
        self.vector_store_id: Optional[str] = vector_store_id
        self.file_ids: List[str] = []
        self.thread_id: Optional[str] = thread_id
        self.assistant_id: Optional[str] = assistant_id

    def create_vector_store(self, name: str = "My Vector Store") -> str:
        try:
            # Create assistant with file search tool
            assistant = client.beta.assistants.create(
                instructions="Use the file provided as your knowledge base to best respond to customer queries.",
                model="gpt-4-1106-preview",
                tools=[{"type": "file_search"}]
            )
            self.vector_store_id = assistant.id
            return self.vector_store_id
        except Exception as e:
            st.error(f"Error creating vector store: {str(e)}")
            raise

    def upload_document(self, uploaded_file) -> str:
        try:
            # Save the uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp.flush()
                # Create file object
                with open(tmp.name, "rb") as file:
                    file_obj = client.files.create(
                        file=file,
                        purpose="assistants"
                    )
                    self.file_ids.append(file_obj.id)
                # Attach the file to the vector store if needed (optional, depending on your workflow)
                # If you want to attach to the assistant, you may need to update the assistant with the file (if API supports)
                # Add the file to the thread
                client.beta.threads.messages.create(
                    thread_id=self.thread_id,
                    role="user",
                    content="Please analyze this document.",
                    attachments=[{
                        "file_id": file_obj.id,
                        "tools": [{"type": "file_search"}]
                    }]
                )
            return file_obj.id
        except Exception as e:
            st.error(f"Error uploading document: {str(e)}")
            raise

    def search_similar_chunks(self, query: str, top_k: int = 3) -> list:
        try:
            # Add the message to the thread
            client.beta.threads.messages.create(
                thread_id=self.thread_id,
                role="user",
                content=query
            )
            # Create a run
            run = client.beta.threads.runs.create(
                thread_id=self.thread_id,
                assistant_id=self.assistant_id
            )
            # Wait for the run to complete
            while True:
                run_status = client.beta.threads.runs.retrieve(
                    thread_id=self.thread_id,
                    run_id=run.id
                )
                if run_status.status == 'completed':
                    break
                elif run_status.status == 'failed':
                    raise Exception("Run failed")
            # Get the messages
            messages = client.beta.threads.messages.list(
                thread_id=self.thread_id
            )
            return messages.data
        except Exception as e:
            st.error(f"Error searching documents: {str(e)}")
            raise

    def search_similar_documents(self, query: str, top_k: int = 3) -> list:
        return self.search_similar_chunks(query, top_k=top_k)

    def synthesize_answer(self, query: str, results) -> str:
        try:
            if not results:
                return "I couldn't find any relevant information in the documents to answer your question."
            
            # Get the latest assistant message
            assistant_messages = [msg for msg in results if msg.role == "assistant"]
            if not assistant_messages:
                return "I couldn't generate a response based on the documents."
            
            return assistant_messages[0].content[0].text.value
        except Exception as e:
            st.error(f"Error generating answer: {str(e)}")
            raise

    def ask_question(self, question: str) -> str:
        try:
            results = self.search_similar_chunks(question, top_k=3)
            return self.synthesize_answer(question, results)
        except Exception as e:
            st.error(f"Error processing question: {str(e)}")
            raise

    def create_assistant(self, name: str = "Document Assistant") -> str:
        try:
            assistant = client.beta.assistants.create(
                instructions="Use the file provided as your knowledge base to best respond to customer queries.",
                model="gpt-4-1106-preview",
                tools=[{"type": "file_search"}],
                name=name
            )
            self.assistant_id = assistant.id
            return self.assistant_id
        except Exception as e:
            st.error(f"Error creating assistant: {str(e)}")
            raise

def main():
    st.title("Document Q&A Assistant (Voice Note & Text, Custom Component)")
    if 'rag' not in st.session_state:
        st.session_state.rag = AdvancedRAG()
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'assistant_created' not in st.session_state:
        st.session_state.assistant_created = False

    uploaded_file = st.file_uploader("Upload a document", type=['pdf', 'txt', 'docx'])
    if uploaded_file and not st.session_state.assistant_created:
        with st.spinner("Uploading document..."):
            try:
                file_id = st.session_state.rag.upload_document(uploaded_file)
                st.success(f"Document uploaded successfully!")
                st.session_state.assistant_created = True
            except Exception as e:
                st.error(f"Failed to upload document: {str(e)}")
                st.session_state.assistant_created = False

    if st.session_state.assistant_created:
        st.subheader("Ask a question (type, record a voice note, or upload audio)")
        # --- CUSTOM AUDIO RECORDER ---
        audio_bytes = st_audiorec()
        if audio_bytes:
            st.audio(audio_bytes, format="audio/wav")
            if st.button("Send Voice Note"):
                with st.spinner("Transcribing audio..."):
                    try:
                        user_question = transcribe_audio(audio_bytes)
                        st.success(f"Transcribed: {user_question}")
                        st.session_state.messages.append((user_question, True))
                        
                        with st.spinner("Thinking..."):
                            response = st.session_state.rag.ask_question(user_question)
                            st.session_state.messages.append((response, False))
                            st.write("Assistant:", response)
                            
                            # --- TTS ---
                            with st.spinner("Synthesizing speech..."):
                                tts_audio = synthesize_speech(response)
                                st.audio(tts_audio, format="audio/mp3")
                    except Exception as e:
                        st.error(f"Error processing voice note: {str(e)}")
        
        # --- AUDIO FILE UPLOAD FOR VOICE NOTE (fallback) ---
        uploaded_audio = st.file_uploader("Or upload a voice note (WAV, MP3, M4A)", type=["wav", "mp3", "m4a"], key="audio_upload")
        if uploaded_audio is not None:
            st.audio(uploaded_audio)
            if st.button("Send Uploaded Voice Note"):
                audio_bytes = uploaded_audio.read()
                with st.spinner("Transcribing audio..."):
                    try:
                        user_question = transcribe_audio(audio_bytes)
                        st.success(f"Transcribed: {user_question}")
                        st.session_state.messages.append((user_question, True))
                        
                        with st.spinner("Thinking..."):
                            response = st.session_state.rag.ask_question(user_question)
                            st.session_state.messages.append((response, False))
                            st.write("Assistant:", response)
                            
                            # --- TTS ---
                            with st.spinner("Synthesizing speech..."):
                                tts_audio = synthesize_speech(response)
                                st.audio(tts_audio, format="audio/mp3")
                    except Exception as e:
                        st.error(f"Error processing uploaded audio: {str(e)}")
        
        # --- TEXT INPUT ---
        prompt = st.chat_input("Ask a question about your document (or use voice note above)")
        if prompt:
            user_question = prompt
            st.session_state.messages.append((user_question, True))
            try:
                with st.spinner("Thinking..."):
                    response = st.session_state.rag.ask_question(user_question)
                    st.session_state.messages.append((response, False))
                    st.write("Assistant:", response)
                    
                    # --- TTS ---
                    with st.spinner("Synthesizing speech..."):
                        tts_audio = synthesize_speech(response)
                        st.audio(tts_audio, format="audio/mp3")
            except Exception as e:
                st.error(f"Error processing question: {str(e)}")
        
        # Display chat messages
        for i, (msg, is_user) in enumerate(st.session_state.messages):
            message(msg, is_user=is_user, key=str(i))
    else:
        st.info("Please upload a document to start the conversation.")

if __name__ == "__main__":
    main() 