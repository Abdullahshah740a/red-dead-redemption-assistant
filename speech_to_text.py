import os
from groq import Groq
from dotenv import load_dotenv

# Load API key from .env
load_dotenv()

def transcribe_audio(file_path):
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    with open(file_path, "rb") as file:
        transcription = client.audio.transcriptions.create(
            file=(file_path, file.read()),
            model="whisper-large-v3-turbo",
            response_format="verbose_json",
        )
        return transcription.text


# Example usage
file_path = r"C:\Users\pc planet\Desktop\ai_with_langchain\wav_voice_note.wav"
print(transcribe_audio(file_path))

