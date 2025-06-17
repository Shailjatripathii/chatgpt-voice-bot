import os
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from gtts import gTTS
import io
import hashlib
from tempfile import NamedTemporaryFile
from audio_recorder_streamlit import audio_recorder

# Must be first command
st.set_page_config(page_title="Voice Assistant", page_icon="🎙️")

# === Setup ===
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
        tmp.seek(0)
        transcript = client.audio.transcriptions.create(
            file=tmp,
            model="whisper-1"
        )
        return transcript.text

def text_to_speech(text):
    audio = io.BytesIO()
    gTTS(text, lang='en').write_to_fp(audio)
    return audio.getvalue()

def get_chat_response(prompt):
    # Prepare conversation history for context
    messages = [{"role": "system", "content": "You are a helpful assistant."}]
    
    # Add previous conversation (last 4 exchanges to manage token count)
    for msg in st.session_state.conversation[-8:]:
        messages.append({"role": msg['role'], "content": msg['content']})
    
    # Add current prompt
    messages.append({"role": "user", "content": prompt})
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.7
    )
    return response.choices[0].message.content

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
                response_text = get_chat_response(text)
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
                response_text = get_chat_response(prompt)
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
