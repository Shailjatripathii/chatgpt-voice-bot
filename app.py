import os
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from gtts import gTTS
import io
import hashlib
from tempfile import NamedTemporaryFile
from audio_recorder_streamlit import audio_recorder

# Initialize app
st.set_page_config(page_title="AI Voice Assistant", page_icon="🤖", layout="wide")

# Load environment variables
load_dotenv()

# Verify OpenAI API key
if not os.getenv("OPENAI_API_KEY"):
    st.error("OPENAI_API_KEY not found in environment variables")
    st.stop()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Session state management
if 'conversation' not in st.session_state:
    st.session_state.conversation = []
if 'last_audio_hash' not in st.session_state:
    st.session_state.last_audio_hash = ""
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'audio_recorded' not in st.session_state:
    st.session_state.audio_recorded = False

# UI Components
st.title("🤖 AI Voice Assistant")
col1, col2 = st.columns([3, 1])

with col1:
    st.caption("Speak or type your message below")

    # Display conversation history
    for msg in st.session_state.conversation:
        if msg['role'] == 'user':
            st.chat_message("user").write(msg['content'])
        else:
            with st.chat_message("assistant"):
                st.write(msg['content'])
                if 'audio' in msg:
                    st.audio(msg['audio'], format='audio/mp3')

with col2:
    st.caption("Voice Control")
    audio_bytes = audio_recorder(
        pause_threshold=2.0,
        sample_rate=44100,
        text="Hold to record",
        neutral_color="#6AA84F",
        recording_color="#CC0000",
        key="audio_recorder"
    )

# Audio processing functions
def process_audio(audio_bytes):
    try:
        with NamedTemporaryFile(suffix=".wav") as tmp:
            tmp.write(audio_bytes)
            tmp.seek(0)
            transcript = client.audio.transcriptions.create(
                file=tmp,
                model="whisper-1"
            )
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
        st.error(f"Text-to-speech error: {str(e)}")
        return None

def get_ai_response(prompt):
    try:
        messages = [{"role": "system", "content": "You are a helpful assistant."}]
        
        # Add conversation history
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
        st.error(f"AI response error: {str(e)}")
        return None

# Handle audio input
if audio_bytes and len(audio_bytes) > 0:
    current_hash = hashlib.md5(audio_bytes).hexdigest()
    
    # Only process if this is new audio and not currently processing
    if (current_hash != st.session_state.last_audio_hash and 
        not st.session_state.processing and
        not st.session_state.audio_recorded):
        
        st.session_state.processing = True
        st.session_state.last_audio_hash = current_hash
        st.session_state.audio_recorded = True
        
        with st.spinner("Processing your voice..."):
            # Transcribe audio
            user_text = process_audio(audio_bytes)
            
            if user_text:
                # Store user message
                st.session_state.conversation.append({
                    'role': 'user',
                    'content': user_text
                })
                
                # Get AI response
                ai_text = get_ai_response(user_text)
                
                if ai_text:
                    # Convert to speech
                    ai_audio = text_to_speech(ai_text)
                    
                    # Store AI response
                    st.session_state.conversation.append({
                        'role': 'assistant',
                        'content': ai_text,
                        'audio': ai_audio
                    })
        
        st.session_state.processing = False
        st.rerun()

# Reset audio recorded state when recorder is idle
if not audio_bytes:
    st.session_state.audio_recorded = False

# Handle text input
if prompt := st.chat_input("Type your message here..."):
    if prompt.strip() and not st.session_state.processing:
        st.session_state.processing = True
        
        with st.spinner("Generating response..."):
            # Store user message
            st.session_state.conversation.append({
                'role': 'user',
                'content': prompt
            })
            
            # Get AI response
            ai_text = get_ai_response(prompt)
            
            if ai_text:
                # Convert to speech
                ai_audio = text_to_speech(ai_text)
                
                # Store AI response
                st.session_state.conversation.append({
                    'role': 'assistant',
                    'content': ai_text,
                    'audio': ai_audio
                })
        
        st.session_state.processing = False
        st.rerun()
