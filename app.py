import streamlit as st
import os
import openai
import speech_recognition as sr
import pyttsx3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Set page title and layout
st.set_page_config(page_title="🗣️ ChatGPT - Meet the AI Voice Bot")
st.title("🧠 Meet ChatGPT - Your Voice Assistant")

# Intro
st.markdown("""
Welcome! Ask me personal questions like:
- What should we know about your life story in a few sentences?
- What’s your #1 superpower?
- What are the top 3 areas you’d like to grow in?
- What misconception do your coworkers have about you?
- How do you push your boundaries and limits?

Press the record button and speak your question aloud.
""")

# Initialize TTS engine
engine = pyttsx3.init()

# Audio input
st.subheader("🎤 Speak Your Question")
audio_input = st.audio_input("Click the button and speak")

if audio_input:
    st.info("Transcribing your voice...")
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(audio_input) as source:
            audio = recognizer.record(source)
            question = recognizer.recognize_google(audio)
            st.success(f"You asked: {question}")

            # Send question to ChatGPT with system prompt
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are ChatGPT. You are confident, witty, introspective, and answer questions about yourself with creativity and depth."},
                    {"role": "user", "content": question}
                ]
            )
            answer = response["choices"][0]["message"]["content"]

            st.markdown("**ChatGPT says:**")
            st.write(answer)

            # Speak response aloud (locally only)
            engine.say(answer)
            engine.runAndWait()

    except sr.UnknownValueError:
        st.error("Could not understand audio.")
    except sr.RequestError as e:
        st.error(f"Speech Recognition error: {e}")
    except Exception as e:
        st.error(f"Something went wrong: {e}")
