import streamlit as st
from streamlit_chat import message
import os
from advanced_rag import AdvancedRAG
import time
from streamlit_audio_recorder.st_audiorec import st_audiorec

# Page config
st.set_page_config(
    page_title="AI Document Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        background-color: #f5f5f5;
    }
    .stTextInput>div>div>input {
        background-color: #ffffff;
    }
    .css-1d391kg {
        padding: 1rem;
    }
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: row;
        align-items: flex-start;
        gap: 1rem;
    }
    .chat-message.user {
        background-color: #2b313e;
    }
    .chat-message.bot {
        background-color: #475063;
    }
    .chat-message .avatar {
        width: 20%;
    }
    .chat-message .message {
        width: 80%;
        padding: 0 1.5rem;
        color: #fff;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'rag' not in st.session_state:
    st.session_state.rag = AdvancedRAG()
    st.session_state.vector_store_created = False
    st.session_state.assistant_created = False
    st.session_state.thread_created = False
    st.session_state.messages = []

# Sidebar
with st.sidebar:
    st.title("📚 Document Setup")
    
    # File uploader
    uploaded_file = st.file_uploader("Upload your document", type=['pdf', 'txt', 'docx'])
    
    if uploaded_file and not st.session_state.vector_store_created:
        with st.spinner("Processing document..."):
            # Save the uploaded file temporarily
            with open(uploaded_file.name, "wb") as f:
                f.write(uploaded_file.getvalue())
            
            # Upload document (do NOT create new assistant/vector store/thread)
            file_id = st.session_state.rag.upload_document(uploaded_file)
            
            # Mark as ready
            st.session_state.vector_store_created = True
            st.session_state.assistant_created = True
            st.session_state.thread_created = True
            
            # Clean up temporary file
            os.remove(uploaded_file.name)
            
            st.success("Document processed successfully!")
    
    # Display status
    st.markdown("---")
    st.markdown("### Status")
    st.markdown(f"Vector Store: {'✅' if st.session_state.vector_store_created else '❌'}")
    st.markdown(f"Assistant: {'✅' if st.session_state.assistant_created else '❌'}")
    st.markdown(f"Thread: {'✅' if st.session_state.thread_created else '❌'}")

# Main content
st.title("🤖 AI Document Assistant")
st.markdown("Upload a document in the sidebar and start chatting!")

# Chat interface
if st.session_state.thread_created:
    # Display chat messages
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            message(msg["content"], is_user=True, key=f"user_{msg['id']}")
        else:
            message(msg["content"], is_user=False, key=f"bot_{msg['id']}")
    
    # Chat input
    user_input = st.text_input("Ask a question about your document:", key="user_input")
    
    if user_input:
        # Add user message to chat
        st.session_state.messages.append({
            "role": "user",
            "content": user_input,
            "id": len(st.session_state.messages)
        })
        
        # Get bot response
        with st.spinner("Thinking..."):
            try:
                # Search for similar documents
                similar_docs = st.session_state.rag.search_similar_documents(user_input)
                
                # Get assistant's response
                response = st.session_state.rag.ask_question(user_input)
                
                # Add bot response to chat
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response,
                    "id": len(st.session_state.messages)
                })
                
                # Rerun to update the chat
                st.experimental_rerun()
                
            except Exception as e:
                st.error(f"Error: {str(e)}")

    # --- VOICE NOTE FEATURES ---
    st.subheader("Voice Note (Record or Upload)")
    audio_bytes = st_audiorec()
    if audio_bytes:
        st.audio(audio_bytes, format="audio/wav")
        if st.button("Send Voice Note"):
            with st.spinner("Transcribing audio..."):
                try:
                    user_question = st.session_state.rag.transcribe_audio(audio_bytes)
                    st.success(f"Transcribed: {user_question}")
                    st.session_state.messages.append({
                        "role": "user",
                        "content": user_question,
                        "id": len(st.session_state.messages)
                    })
                    with st.spinner("Thinking..."):
                        response = st.session_state.rag.ask_question(user_question)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": response,
                            "id": len(st.session_state.messages)
                        })
                        with st.spinner("Synthesizing speech..."):
                            tts_audio = st.session_state.rag.synthesize_speech(response)
                            st.audio(tts_audio, format="audio/mp3")
                        st.experimental_rerun()
                except Exception as e:
                    st.error(f"Error processing voice note: {str(e)}")
    uploaded_audio = st.file_uploader("Or upload a voice note (WAV, MP3, M4A)", type=["wav", "mp3", "m4a"], key="audio_upload")
    if uploaded_audio is not None:
        st.audio(uploaded_audio)
        if st.button("Send Uploaded Voice Note"):
            audio_bytes = uploaded_audio.read()
            with st.spinner("Transcribing audio..."):
                try:
                    user_question = st.session_state.rag.transcribe_audio(audio_bytes)
                    st.success(f"Transcribed: {user_question}")
                    st.session_state.messages.append({
                        "role": "user",
                        "content": user_question,
                        "id": len(st.session_state.messages)
                    })
                    with st.spinner("Thinking..."):
                        response = st.session_state.rag.ask_question(user_question)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": response,
                            "id": len(st.session_state.messages)
                        })
                        with st.spinner("Synthesizing speech..."):
                            tts_audio = st.session_state.rag.synthesize_speech(response)
                            st.audio(tts_audio, format="audio/mp3")
                        st.experimental_rerun()
                except Exception as e:
                    st.error(f"Error processing uploaded audio: {str(e)}")
else:
    st.info("Please upload a document in the sidebar to start chatting!")

# Footer
st.markdown("---")
st.markdown("Built with ❤️ using OpenAI's Assistants API and Streamlit") 