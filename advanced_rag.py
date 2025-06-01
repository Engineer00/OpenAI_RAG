import os
from typing import List, Optional
import openai
# from dotenv import load_dotenv
import streamlit as st
from streamlit_chat import message
import tempfile
import sys
import hashlib
import numpy as np
from io import BytesIO

# Streamlit Cloud Ready: This code is optimized for deployment on Streamlit Cloud.
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
# Removed vector_store_id from secrets

if not api_key:
    st.error("OpenAI API key not found. Please add it to your Streamlit Cloud secrets.")
    st.stop()

# Initialize OpenAI client
client = openai.OpenAI(api_key=api_key)

class AdvancedRAG:
    def __init__(self):
        self.vector_store_id: Optional[str] = None  # No longer from secrets
        self.file_ids: List[str] = []
        self.thread_id: Optional[str] = None
        self.assistant_id: Optional[str] = assistant_id

    def create_thread(self) -> str:
        thread = client.beta.threads.create(
            tool_resources={
                "file_search": {
                    "vector_store_ids": [self.vector_store_id]
                }
            }
        )
        self.thread_id = thread.id
        return self.thread_id

    def create_vector_store(self, name: str = "My Vector Store") -> str:
        try:
            # Create vector store
            vector_store = client.vector_stores.create(name=name)
            self.vector_store_id = vector_store.id
            return self.vector_store_id
        except Exception as e:
            st.error(f"Error creating vector store: {str(e)}")
            raise

    def ensure_vector_store(self):
        # Try to use the current vector store, or create a new one if missing/invalid
        try:
            if not self.vector_store_id:
                vector_store = client.vector_stores.create(name="knowledge_base")
                self.vector_store_id = vector_store.id
            else:
                # Try to retrieve the vector store to check if it exists
                client.vector_stores.retrieve(self.vector_store_id)
        except Exception:
            # If retrieval fails, create a new vector store
            vector_store = client.vector_stores.create(name="knowledge_base")
            self.vector_store_id = vector_store.id

    def upload_document(self, uploaded_file) -> str:
        # Delete previous vector store if it exists
        if self.vector_store_id:
            try:
                client.vector_stores.delete(self.vector_store_id)
            except Exception as e:
                st.warning(f"Could not delete previous vector store {self.vector_store_id}: {e}")
        # Always create a new vector store for each upload
        vector_store = client.vector_stores.create(name="knowledge_base")
        self.vector_store_id = vector_store.id
        self.file_ids = []
        # Upload file to OpenAI
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp.flush()
            with open(tmp.name, "rb") as file:
                file_obj = client.files.create(
                    file=file,
                    purpose="assistants"
                )
                self.file_ids.append(file_obj.id)
                # Attach file to vector store
                client.vector_stores.files.create(
                    vector_store_id=self.vector_store_id,
                    file_id=file_obj.id
                )
        # Always create a new thread for each upload
        thread = client.beta.threads.create(
            tool_resources={
                "file_search": {
                    "vector_store_ids": [self.vector_store_id]
                }
            }
        )
        self.thread_id = thread.id
        return file_obj.id

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
            import time
            waited = 0
            while True:
                run_status = client.beta.threads.runs.retrieve(
                    thread_id=self.thread_id,
                    run_id=run.id
                )
                if run_status.status == 'completed':
                    break
                elif run_status.status == 'failed':
                    raise Exception("Run failed")
                time.sleep(0.2)
                waited += 0.2
                if waited > 60:
                    raise Exception("Run timed out after 60 seconds.")
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
            # Add user message to the thread
            client.beta.threads.messages.create(
                thread_id=self.thread_id,
                role="user",
                content=question
            )
            # Run the assistant on the thread
            run = client.beta.threads.runs.create(
                thread_id=self.thread_id,
                assistant_id=self.assistant_id
            )
            # Wait for the run to complete
            import time
            waited = 0
            while True:
                run_status = client.beta.threads.runs.retrieve(
                    thread_id=self.thread_id,
                    run_id=run.id
                )
                if run_status.status == 'completed':
                    break
                elif run_status.status == 'failed':
                    raise Exception("Run failed")
                time.sleep(0.2)
                waited += 0.2
                if waited > 60:
                    raise Exception("Run timed out after 60 seconds.")
            # Get the latest message
            messages = client.beta.threads.messages.list(
                thread_id=self.thread_id,
                order='desc',
                limit=1
            )
            if not messages.data:
                return "No response received from the assistant."
            return messages.data[0].content[0].text.value
        except Exception as e:
            st.error(f"Error processing question: {str(e)}")
            return "[Assistant failed to answer]"

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

    def transcribe_audio(self, audio_bytes):
        import traceback
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp.flush()
                tmp_path = tmp.name
            with open(tmp_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="en"
                )
            os.remove(tmp_path)
            return transcript.text
        except Exception as e:
            st.error(f"Error transcribing audio: {str(e)}")
            st.error(traceback.format_exc())
            return "[Transcription failed]"

    def synthesize_speech(self, text, voice="alloy", response_format="mp3"):
        import traceback
        try:
            response = client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text,
                response_format=response_format
            )
            return response.content
        except Exception as e:
            st.error(f"Error synthesizing speech: {str(e)}")
            st.error(traceback.format_exc())
            return None

def file_hash(uploaded_file):
    return hashlib.sha256(uploaded_file.getvalue()).hexdigest()

def main():
    st.title("Document Q&A Assistant (Voice Note & Text, Custom Component)")
    if 'rag' not in st.session_state:
        st.session_state.rag = AdvancedRAG()
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'assistant_created' not in st.session_state:
        st.session_state.assistant_created = False
    if 'last_uploaded_file_hash' not in st.session_state:
        st.session_state.last_uploaded_file_hash = None
    if 'disable_widgets' not in st.session_state:
        st.session_state.disable_widgets = False

    def reset_all():
        st.session_state.rag = AdvancedRAG()
        st.session_state.messages = []
        st.session_state.assistant_created = False
        st.session_state.last_uploaded_file_hash = None
        st.session_state.disable_widgets = False

    st.button("Reset", on_click=reset_all)

    uploaded_file = st.file_uploader("Upload a document", type=['pdf', 'txt', 'docx'], disabled=st.session_state.disable_widgets)
    if uploaded_file:
        current_hash = file_hash(uploaded_file)
        if current_hash != st.session_state.last_uploaded_file_hash:
            reset_all()
            st.session_state.disable_widgets = True
            with st.spinner("Uploading document..."):
                try:
                    file_id = st.session_state.rag.upload_document(uploaded_file)
                    st.success(f"Document uploaded successfully!")
                    st.session_state.assistant_created = True
                    st.session_state.last_uploaded_file_hash = current_hash
                except Exception as e:
                    st.error(f"Failed to upload document: {str(e)}")
                    st.session_state.assistant_created = False
                    st.session_state.last_uploaded_file_hash = None
                finally:
                    st.session_state.disable_widgets = False

    if st.session_state.assistant_created:
        st.subheader("Ask a question (type, record a voice note, or upload audio)")
        audio_bytes = st_audiorec() if not st.session_state.disable_widgets else None
        if audio_bytes:
            st.audio(audio_bytes, format="audio/wav")
            if st.button("Send Voice Note", disabled=st.session_state.disable_widgets):
                st.session_state.disable_widgets = True
                with st.spinner("Transcribing audio..."):
                    try:
                        user_question = st.session_state.rag.transcribe_audio(audio_bytes)
                        st.success(f"Transcribed: {user_question}")
                        st.session_state.messages.append((user_question, True))
                        with st.spinner("Thinking..."):
                            response = st.session_state.rag.ask_question(user_question)
                            st.session_state.messages.append((response, False))
                            st.write("Assistant:", response)
                            with st.spinner("Synthesizing speech..."):
                                tts_audio = st.session_state.rag.synthesize_speech(response)
                                st.audio(tts_audio, format="audio/mp3")
                    except Exception as e:
                        st.error(f"Error processing voice note: {str(e)}")
                    finally:
                        st.session_state.disable_widgets = False
        
        # --- AUDIO FILE UPLOAD FOR VOICE NOTE (fallback) ---
        uploaded_audio = st.file_uploader("Or upload a voice note (WAV, MP3, M4A)", type=["wav", "mp3", "m4a"], key="audio_upload", disabled=st.session_state.disable_widgets)
        if uploaded_audio is not None:
            st.audio(uploaded_audio)
            if st.button("Send Uploaded Voice Note", disabled=st.session_state.disable_widgets):
                st.session_state.disable_widgets = True
                audio_bytes = uploaded_audio.read()
                with st.spinner("Transcribing audio..."):
                    try:
                        user_question = st.session_state.rag.transcribe_audio(audio_bytes)
                        st.success(f"Transcribed: {user_question}")
                        st.session_state.messages.append((user_question, True))
                        
                        with st.spinner("Thinking..."):
                            response = st.session_state.rag.ask_question(user_question)
                            st.session_state.messages.append((response, False))
                            st.write("Assistant:", response)
                            
                            # --- TTS ---
                            with st.spinner("Synthesizing speech..."):
                                tts_audio = st.session_state.rag.synthesize_speech(response)
                                st.audio(tts_audio, format="audio/mp3")
                    except Exception as e:
                        st.error(f"Error processing uploaded audio: {str(e)}")
                    finally:
                        st.session_state.disable_widgets = False
        
        # --- TEXT INPUT ---
        prompt = st.chat_input("Ask a question about your document (or use voice note above)", disabled=st.session_state.disable_widgets)
        if prompt:
            st.session_state.disable_widgets = True
            user_question = prompt
            st.session_state.messages.append((user_question, True))
            try:
                with st.spinner("Thinking..."):
                    response = st.session_state.rag.ask_question(user_question)
                    st.session_state.messages.append((response, False))
                    st.write("Assistant:", response)
                    
                    # --- TTS ---
                    with st.spinner("Synthesizing speech..."):
                        tts_audio = st.session_state.rag.synthesize_speech(response)
                        st.audio(tts_audio, format="audio/mp3")
            except Exception as e:
                st.error(f"Error processing question: {str(e)}")
            finally:
                st.session_state.disable_widgets = False
        
        # Display chat messages
        for i, (msg, is_user) in enumerate(st.session_state.messages):
            message(msg, is_user=is_user, key=str(i))
    else:
        st.info("Please upload a document to start the conversation.")

if __name__ == "__main__":
    main() 