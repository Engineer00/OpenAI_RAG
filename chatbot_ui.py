import streamlit as st
from streamlit_chat import message
import os
from advanced_rag import AdvancedRAG
import time
from streamlit_audio_recorder.st_audiorec import st_audiorec
import traceback

# Page config
st.set_page_config(
    page_title="AI Document Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state with better error handling
try:
    if 'rag' not in st.session_state:
        st.session_state.rag = AdvancedRAG()
    if 'vector_store_created' not in st.session_state:
        st.session_state.vector_store_created = False
    if 'assistant_created' not in st.session_state:
        st.session_state.assistant_created = False
    if 'thread_created' not in st.session_state:
        st.session_state.thread_created = False
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'user_input' not in st.session_state:
        st.session_state.user_input = ""
    if 'last_error' not in st.session_state:
        st.session_state.last_error = ""
    if 'last_response' not in st.session_state:
        st.session_state.last_response = ""
    if 'debug_info' not in st.session_state:
        st.session_state.debug_info = []
except Exception as e:
    st.error(f"Error initializing session state: {str(e)}")
    st.error(traceback.format_exc())

# --- Check for required secrets ---
missing_secrets = []
try:
    for key in ["OPENAI_API_KEY", "ASSISTANT_ID", "THREAD_ID", "VECTOR_STORE_ID"]:
        if key not in st.secrets or not st.secrets[key]:
            missing_secrets.append(key)
            st.session_state.debug_info.append(f"Missing secret: {key}")
except Exception as e:
    st.error(f"Error checking secrets: {str(e)}")
    st.error(traceback.format_exc())

# --- DEBUG: Show debug info in sidebar ---
with st.sidebar:
    st.markdown("---")
    st.subheader("Debug Info")
    if st.session_state.last_error:
        st.error(f"Last error: {st.session_state.last_error}")
    if st.session_state.last_response:
        st.info(f"Last response: {st.session_state.last_response}")
    if st.session_state.debug_info:
        st.subheader("Debug Log")
        for info in st.session_state.debug_info:
            st.text(info)

# Sidebar
with st.sidebar:
    st.title("📚 Document Setup")
    
    # File uploader
    uploaded_file = st.file_uploader("Upload your document", type=['pdf', 'txt', 'docx'])
    
    if uploaded_file and not st.session_state.vector_store_created:
        with st.spinner("Processing document..."):
            try:
                # Save the uploaded file temporarily
                with open(uploaded_file.name, "wb") as f:
                    f.write(uploaded_file.getvalue())
                
                # Upload document
                file_id = st.session_state.rag.upload_document(uploaded_file)
                st.session_state.debug_info.append(f"Document uploaded with ID: {file_id}")
                
                # Mark as ready
                st.session_state.vector_store_created = True
                st.session_state.assistant_created = True
                st.session_state.thread_created = True
                
                # Clean up temporary file
                os.remove(uploaded_file.name)
                
                st.success("Document processed successfully!")
            except Exception as e:
                st.session_state.last_error = str(e)
                st.session_state.debug_info.append(f"Error processing document: {str(e)}")
                st.error(f"Error processing document: {str(e)}")
                st.error(traceback.format_exc())
    
    # Display status
    st.markdown("---")
    st.markdown("### Status")
    st.markdown(f"Vector Store: {'✅' if st.session_state.vector_store_created else '❌'}")
    st.markdown(f"Assistant: {'✅' if st.session_state.assistant_created else '❌'}")
    st.markdown(f"Thread: {'✅' if st.session_state.thread_created else '❌'}")

    # --- SIDEBAR: Chat Management ---
    st.markdown("---")
    st.subheader("Chat Management")
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.success("Chat history cleared.")
    if st.session_state.messages:
        import json
        chat_json = json.dumps(st.session_state.messages, indent=2)
        st.download_button("Download Chat History (JSON)", chat_json, file_name="chat_history.json", mime="application/json")

# --- Dedicated Chatbot Screen ---
st.title("🤖 AI Document Assistant")
st.markdown("Upload a document in the sidebar and start chatting!")

# --- Modern Chat Area ---
st.subheader("Chat")
chat_container = st.container()
with chat_container:
    if st.session_state.messages:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                message(msg["content"], is_user=True, key=f"user_{msg['id']}")
            else:
                message(msg["content"], is_user=False, key=f"bot_{msg['id']}")
    else:
        st.info("No messages yet. Start the conversation below!")
    # If there are missing secrets, show a clear error in the chat area
    if missing_secrets:
        st.error(f"Missing required secrets: {', '.join(missing_secrets)}. Please set them in Streamlit Cloud.")

# --- Input Widgets (always visible) ---
if not missing_secrets and st.session_state.thread_created:
    try:
        # --- VOICE NOTE FEATURES ---
        st.subheader("Voice Note (Record or Upload)")
        audio_bytes = st_audiorec()
        if audio_bytes:
            st.audio(audio_bytes, format="audio/wav")
        send_voice = st.button("Send Voice Note", key="send_voice")
        if send_voice:
            if audio_bytes:
                with st.spinner("Transcribing audio..."):
                    try:
                        user_question = st.session_state.rag.transcribe_audio(audio_bytes)
                        st.success(f"Transcribed: {user_question}")
                        st.session_state.user_input = user_question
                        st.session_state.messages.append({
                            "role": "user",
                            "content": user_question,
                            "id": len(st.session_state.messages)
                        })
                        st.info("Voice note sent to assistant.")
                        with st.spinner("Thinking..."):
                            try:
                                response = st.session_state.rag.ask_question(user_question)
                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "content": response,
                                    "id": len(st.session_state.messages)
                                })
                                st.success("Assistant replied.")
                                with st.spinner("Synthesizing speech..."):
                                    tts_audio = st.session_state.rag.synthesize_speech(response)
                                    st.audio(tts_audio, format="audio/mp3")
                                st.session_state.user_input = ""
                                st.session_state.last_error = ""
                                st.session_state.last_response = response
                                st.experimental_rerun()
                            except Exception as e:
                                st.session_state.last_error = str(e)
                                st.session_state.debug_info.append(f"Error getting assistant reply: {str(e)}")
                                st.error(f"Error getting assistant reply: {str(e)}")
                                st.error(traceback.format_exc())
                    except Exception as e:
                        st.session_state.last_error = str(e)
                        st.session_state.debug_info.append(f"Error processing voice note: {str(e)}")
                        st.error(f"Error processing voice note: {str(e)}")
                        st.error(traceback.format_exc())
            else:
                st.warning("Please record audio before sending.")
        
        # --- TEXT CHATBOT ---
        user_input = st.text_input("Ask a question about your document:", key="user_input", value=st.session_state.user_input)
        send_text = st.button("Send Message", key="send_text")
        if send_text and user_input:
            st.session_state.messages.append({
                "role": "user",
                "content": user_input,
                "id": len(st.session_state.messages)
            })
            with st.spinner("Thinking..."):
                try:
                    response = st.session_state.rag.ask_question(user_input)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response,
                        "id": len(st.session_state.messages)
                    })
                    st.session_state.user_input = ""
                    st.session_state.last_error = ""
                    st.session_state.last_response = response
                    st.experimental_rerun()
                except Exception as e:
                    st.session_state.last_error = str(e)
                    st.session_state.debug_info.append(f"Error in text chat: {str(e)}")
                    st.error(f"Error: {str(e)}")
                    st.error(traceback.format_exc())
    except Exception as e:
        st.session_state.last_error = str(e)
        st.session_state.debug_info.append(f"Error in main UI: {str(e)}")
        st.error(f"Error in main UI: {str(e)}")
        st.error(traceback.format_exc())
else:
    if not missing_secrets:
        st.warning("The backend is not running or the thread is not created. Please upload a document in the sidebar to start chatting!")

# Footer
st.markdown("---")
st.markdown("Built with ❤️ using OpenAI's Assistants API and Streamlit") 