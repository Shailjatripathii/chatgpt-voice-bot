import os
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from gtts import gTTS
import io
import hashlib
from tempfile import NamedTemporaryFile
from audio_recorder_streamlit import audio_recorder

# Initialize
st.set_page_config(page_title="Voice Assistant", page_icon="🎙️")
load_dotenv()

# Check API key
if not os.getenv("OPENAI_API_KEY"):
    st.error("OPENAI_API_KEY not found in environment variables")
    st.stop()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Session state
if 'conversation' not in st.session_state:
    st.session_state.conversation = []
if 'last_audio_hash' not in st.session_state:
    st.session_state.last_audio_hash = ""
if 'processing' not in st.session_state:
    st.session_state.processing = False

# UI
st.title("🎙️ Voice Assistant")
st.write("Press the microphone to speak (hold for 2-3 seconds)")

# Display chat history
for msg in st.session_state.conversation:
    if msg['role'] == 'user':
        st.chat_message("user").write(msg['content'])
    else:
        st.chat_message("assistant").write(msg['content'])
        if 'audio' in msg:
            st.audio(msg['audio'], format='audio/mp3')

def get_audio_hash(audio_bytes):
    return hashlib.md5(audio_bytes).hexdigest() if audio_bytes else ""

# Audio processing functions
def process_audio(audio_bytes):
    try:
        with NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        
        with open(tmp_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-1"
            )
        os.unlink(tmp_path)
        return transcript.text
    except Exception as e:
        st.error(f"Audio processing error: {str(e)}")
        return None

def text_to_speech(text):
    try:
        audio = io.BytesIO()
        gTTS(text=text, lang='en').write_to_fp(audio)
        return audio.getvalue()
    except Exception as e:
        st.error(f"TTS error: {str(e)}")
        return None

def get_chat_response(prompt):
    try:
        messages = [{"role": "system", "content": "You are a helpful assistant."}]
        
        # Add conversation history (last 3 exchanges)
        for msg in st.session_state.conversation[-6:]:
            messages.append({"role": msg['role'], "content": msg['content']})
        
        messages.append({"role": "user", "content": prompt})
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Chat error: {str(e)}")
        return None

# Audio recorder
audio_bytes = audio_recorder(
    pause_threshold=2.0,
    sample_rate=16000,
    text="Hold to speak",
    neutral_color="#6aa84f",
    recording_color="#e69138"
)

# Handle audio input
if audio_bytes and len(audio_bytes) > 0:
    current_hash = get_audio_hash(audio_bytes)
    
    if current_hash != st.session_state.last_audio_hash and not st.session_state.processing:
        st.session_state.processing = True
        st.session_state.last_audio_hash = current_hash
        
        with st.spinner("Processing your voice..."):
            user_text = process_audio(audio_bytes)
            if user_text:
                st.session_state.conversation.append({'role': 'user', 'content': user_text})
                
                assistant_text = get_chat_response(user_text)
                if assistant_text:
                    assistant_audio = text_to_speech(assistant_text)
                    st.session_state.conversation.append({
                        'role': 'assistant',
                        'content': assistant_text,
                        'audio': assistant_audio
                    })
        
        st.session_state.processing = False
        st.rerun()

# Handle text input
if prompt := st.chat_input("Or type your message here..."):
    if prompt.strip() and not st.session_state.processing:
        st.session_state.processing = True
        
        with st.spinner("Generating response..."):
            st.session_state.conversation.append({'role': 'user', 'content': prompt})
            
            assistant_text = get_chat_response(prompt)
            if assistant_text:
                assistant_audio = text_to_speech(assistant_text)
                st.session_state.conversation.append({
                    'role': 'assistant',
                    'content': assistant_text,
                    'audio': assistant_audio
                })
        
        st.session_state.processing = False
        st.rerun()
