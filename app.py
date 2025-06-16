import streamlit as st
import os
import openai
import speech_recognition as sr
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Streamlit page setup
st.set_page_config(page_title="🎙️ ChatGPT Voice Bot")
st.title("🎙️ Talk to ChatGPT - Voice Bot")

# Instruction
st.markdown("""
Ask ChatGPT personal-style questions like:
- What’s your life story in a few sentences?
- What’s your #1 superpower?
- How do you push your boundaries?

Just upload your voice (WAV format) and let ChatGPT answer!
""")

# Upload audio file
audio_file = st.file_uploader("🎤 Upload your question (WAV format)", type=["wav"])

if audio_file is not None:
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(audio_file) as source:
            st.info("Transcribing your voice...")
            audio = recognizer.record(source)
            question = recognizer.recognize_google(audio)
            st.success(f"🗣️ You asked: {question}")

            # Ask ChatGPT
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are ChatGPT. Answer questions about yourself with creativity, depth, and personality."},
                    {"role": "user", "content": question}
                ]
            )
            answer = response["choices"][0]["message"]["content"]
            st.markdown("### 🤖 ChatGPT says:")
            st.write(answer)

    except Exception as e:
        st.error(f"Error: {e}")
