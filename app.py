import os
import streamlit as st
from dotenv import load_dotenv
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase, ClientSettings
import speech_recognition as sr
from pydub import AudioSegment
import numpy as np
import openai
import tempfile

# Load API key
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="🎙️ ChatGPT Voice Bot")
st.title("🎙️ Chat with ChatGPT using Your Voice")

st.markdown("Click the record button, speak your question, and ChatGPT will respond.")

# Set up WebRTC
WEBRTC_CLIENT_SETTINGS = ClientSettings(
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
    media_stream_constraints={"audio": True, "video": False},
)

class AudioProcessor(AudioProcessorBase):
    def __init__(self) -> None:
        self.recorded_frames = []

    def recv(self, frame):
        audio = frame.to_ndarray()
        self.recorded_frames.append(audio)
        return frame

ctx = webrtc_streamer(
    key="chatgpt-voice",
    mode="SENDRECV",
    client_settings=WEBRTC_CLIENT_SETTINGS,
    audio_processor_factory=AudioProcessor,
    media_stream_constraints={"audio": True, "video": False},
)

if st.button("📝 Submit Voice to ChatGPT"):
    if ctx.audio_processor and ctx.audio_processor.recorded_frames:
        # Convert audio numpy array to WAV
        audio_data = np.concatenate(ctx.audio_processor.recorded_frames, axis=0).astype(np.int16)
        temp_wav_path = tempfile.mktemp(suffix=".wav")
        audio_segment = AudioSegment(
            audio_data.tobytes(), frame_rate=16000, sample_width=2, channels=1
        )
        audio_segment.export(temp_wav_path, format="wav")

        recognizer = sr.Recognizer()
        with sr.AudioFile(temp_wav_path) as source:
            audio = recognizer.record(source)
            st.info("Transcribing your voice...")
            try:
                question = recognizer.recognize_google(audio)
                st.success(f"You asked: {question}")

                response = openai.ChatCompletion.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are ChatGPT. Answer questions about yourself with personality, insight, and creativity."},
                        {"role": "user", "content": question}
                    ]
                )
                answer = response["choices"][0]["message"]["content"]
                st.markdown("### 🤖 ChatGPT says:")
                st.write(answer)

            except Exception as e:
                st.error(f"Error transcribing audio: {e}")
    else:
        st.warning("No audio recorded yet.")
