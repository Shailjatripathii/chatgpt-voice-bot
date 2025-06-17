import os
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from gtts import gTTS
import io
import base64
import hashlib
from tempfile import NamedTemporaryFile
from audio_recorder_streamlit import audio_recorder

# Initialize app
st.set_page_config(page_title="AI Voice Assistant", page_icon="🤖")

# Load environment variables
load_dotenv()

# Verify OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    st.error("❌ OPENAI_API_KEY not found in environment variables")
    st.stop()

# Initialize OpenAI client
try:
    client = OpenAI(api_key=OPENAI_API_KEY)
except Exception as e:
    st.error(f"❌ Failed to initialize OpenAI client: {str(e)}")
    st.stop()

# Session state management
if 'conversation' not in st.session_state:
    st.session_state.conversation = []
if 'processing' not in st.session_state:
    st.session_state.processing = False

# UI Components
st.title("🤖 AI Voice Assistant")
st.caption("Speak or type your message")

# Display conversation history
for msg in st.session_state.conversation:
    if msg['role'] == 'user':
        st.chat_message("user").write(msg['content'])
    else:
        with st.chat_message("assistant"):
            st.write(msg['content'])
            if 'audio' in msg:
                st.audio(msg['audio'], format='audio/mp3')

# Audio processing functions
def audio_to_text(audio_bytes):
    try:
        with NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        
        with open(tmp_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        os.unlink(tmp_path)
        return transcript.text
    except Exception as e:
        st.error(f"🔇 Audio processing failed: {str(e)}")
        return None

def text_to_audio(text):
    try:
        audio = io.BytesIO()
        tts = gTTS(text=text, lang='en')
        tts.write_to_fp(audio)
        return audio.getvalue()
    except Exception as e:
        st.error(f"🔈 Text-to-speech failed: {str(e)}")
        return None

def get_ai_response(prompt):
    try:
        # Prepare conversation history
        messages = [{"role": "system", "content": "You are a helpful assistant."}]
        
        # Add previous conversation context
        for msg in st.session_state.conversation[-6:]:  # Keep last 3 exchanges
            messages.append({"role": msg['role'], "content": msg['content']})
        
        # Add current prompt
        messages.append({"role": "user", "content": prompt})
        
        # Get response from OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"🤖 AI response failed: {str(e)}")
        return None

# Voice input handling
audio_bytes = audio_recorder(
    pause_threshold=2.0,
    sample_rate=44100,
    text="Hold to record",
    neutral_color="#6AA84F",
    recording_color="#CC0000"
)

if audio_bytes and not st.session_state.processing:
    st.session_state.processing = True
    
    with st.spinner("🔄 Processing your voice..."):
        # Convert audio to text
        user_text = audio_to_text(audio_bytes)
        
        if user_text:
            # Store user message
            st.session_state.conversation.append({
                'role': 'user',
                'content': user_text
            })
            
            # Get AI response
            ai_text = get_ai_response(user_text)
            
            if ai_text:
                # Convert response to audio
                ai_audio = text_to_audio(ai_text)
                
                # Store AI response
                st.session_state.conversation.append({
                    'role': 'assistant',
                    'content': ai_text,
                    'audio': ai_audio
                })
    
    st.session_state.processing = False
    st.rerun()

# Text input handling
if prompt := st.chat_input("Type your message here..."):
    if prompt.strip() and not st.session_state.processing:
        st.session_state.processing = True
        
        with st.spinner("🔄 Processing your message..."):
            # Store user message
            st.session_state.conversation.append({
                'role': 'user',
                'content': prompt
            })
            
            # Get AI response
            ai_text = get_ai_response(prompt)
            
            if ai_text:
                # Convert response to audio
                ai_audio = text_to_audio(ai_text)
                
                # Store AI response
                st.session_state.conversation.append({
                    'role': 'assistant',
                    'content': ai_text,
                    'audio': ai_audio
                })
        
        st.session_state.processing = False
        st.rerun()
