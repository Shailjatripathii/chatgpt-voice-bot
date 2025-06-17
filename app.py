import os
import openai
import streamlit as st
from dotenv import load_dotenv
from gtts import gTTS
import io
import hashlib
from tempfile import NamedTemporaryFile
from audio_recorder_streamlit import audio_recorder

# Must be first command
st.set_page_config(page_title="Voice Assistant", page_icon="🎙️")
client = openai.OpenAI()
# === Setup ===
load_dotenv()
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
response = openai.ChatCompletion.create(
    model="gpt-4o"
)
# === Simple UI ===
st.title("🎙️ Voice Assistant")
st.write("Press to record your question (hold for 5 seconds)")

# Initialize session state
if 'conversation' not in st.session_state:
    st.session_state.conversation = []
if 'last_audio_hash' not in st.session_state:
    st.session_state.last_audio_hash = None
if 'processing' not in st.session_state:
    st.session_state.processing = False

# Display chat history
for msg in st.session_state.conversation:
    if msg['role'] == 'user':
        st.chat_message("user").write(msg['content'])
    else:
        st.chat_message("assistant").write(msg['content'])
        if 'audio' in msg:
            st.audio(msg['audio'], format='audio/mp3')

def get_audio_hash(audio_bytes):
    return hashlib.md5(audio_bytes).hexdigest()

# Audio recorder
audio_bytes = audio_recorder(
    pause_threshold=5.0,
    sample_rate=16000,
    text="Hold to speak",
    neutral_color="#1e88e5",
    recording_color="#e53935"
)

# Audio processing
def process_audio(audio_data):
    with NamedTemporaryFile(suffix=".wav") as tmp:
        tmp.write(audio_data)
        audio_file = genai.upload_file(tmp.name, mime_type="audio/wav")
        response = model.generate_content(["Transcribe:", audio_file])
        genai.delete_file(audio_file.name)
        return response.text

def text_to_speech(text):
    audio = io.BytesIO()
    gTTS(text, lang='en').write_to_fp(audio)
    return audio.getvalue()

# Handle new audio
if audio_bytes and len(audio_bytes) > 0:
    current_hash = get_audio_hash(audio_bytes)
    
    # Only process if this is new audio and not currently processing
    if current_hash != st.session_state.last_audio_hash and not st.session_state.processing:
        st.session_state.processing = True
        st.session_state.last_audio_hash = current_hash
        
        with st.spinner("Processing..."):
            try:
                # Transcribe
                text = process_audio(audio_bytes)
                st.session_state.conversation.append({'role': 'user', 'content': text})
                
                # Get response
                response = model.generate_content(text)
                response_text = response.text
                response_audio = text_to_speech(response_text)
                
                st.session_state.conversation.append({
                    'role': 'assistant', 
                    'content': response_text,
                    'audio': response_audio
                })
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
            finally:
                st.session_state.processing = False
                st.rerun()

# Text input fallback
if prompt := st.chat_input("Or type your question..."):
    if not st.session_state.processing:
        st.session_state.processing = True
        with st.spinner("Thinking..."):
            try:
                response = model.generate_content(prompt)
                response_text = response.text
                response_audio = text_to_speech(response_text)
                
                st.session_state.conversation.extend([
                    {'role': 'user', 'content': prompt},
                    {'role': 'assistant', 'content': response_text, 'audio': response_audio}
                ])
            except Exception as e:
                st.error(f"Error: {str(e)}")
            finally:
                st.session_state.processing = False
                st.rerun()
