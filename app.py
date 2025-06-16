import streamlit as st
import openai
import os
from dotenv import load_dotenv
import speech_recognition as sr
from pydub import AudioSegment
import io

# Load API key
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="🎙️ ChatGPT Voice Bot")
st.title("🎙️ Talk to ChatGPT Using Your Voice")

st.markdown("**Click to record, ask your question, and ChatGPT will answer!**")

# Audio recorder using Streamlit's HTML + JavaScript trick
st.markdown("""
    <script>
    let mediaRecorder;
    let audioChunks = [];

    function startRecording() {
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                mediaRecorder = new MediaRecorder(stream);
                mediaRecorder.start();

                mediaRecorder.ondataavailable = function(e) {
                    audioChunks.push(e.data);
                };

                mediaRecorder.onstop = function() {
                    let blob = new Blob(audioChunks, { 'type': 'audio/wav; codecs=MS_PCM' });
                    let fileReader = new FileReader();
                    fileReader.onloadend = function () {
                        let arrayBuffer = fileReader.result;
                        window.parent.postMessage({ type: 'streamlit:audio', audio: arrayBuffer }, '*');
                    };
                    fileReader.readAsArrayBuffer(blob);
                };

                setTimeout(() => mediaRecorder.stop(), 5000);
            });
    }

    window.addEventListener("message", (event) => {
        if (event.data.type === "streamlit:startRecording") {
            audioChunks = [];
            startRecording();
        }
    });
    </script>

    <button onclick="window.parent.postMessage({ type: 'streamlit:startRecording' }, '*')">🎤 Record 5s</button>
""", unsafe_allow_html=True)

# Receive audio from frontend
audio_bytes = st.file_uploader("Upload audio if recorded already (WAV)", type=["wav"])

if audio_bytes is not None:
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_bytes) as source:
        audio = recognizer.record(source)
        st.info("Transcribing...")
        try:
            question = recognizer.recognize_google(audio)
            st.success(f"You said: {question}")

            # Ask ChatGPT
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are ChatGPT. Answer questions about yourself with insight and personality."},
                    {"role": "user", "content": question}
                ]
            )
            answer = response["choices"][0]["message"]["content"]
            st.markdown("### 🤖 ChatGPT replies:")
            st.write(answer)

        except Exception as e:
            st.error(f"Could not process your voice: {e}")
