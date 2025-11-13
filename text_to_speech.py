import os
from groq import Groq
from dotenv import load_dotenv
import uuid

# Load API key from .env
load_dotenv()

def text_to_speech(text):
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

    # 🗂️ Create a dedicated folder for audios if not exists
    audio_dir = "audio_responses"
    os.makedirs(audio_dir, exist_ok=True) #exist_ok=True means “Create the folder only if it doesn’t exist"

    # 🎧 Generate unique filename
    unique_id = uuid.uuid4().hex
    speech_file_path = os.path.join(audio_dir, f"speech_{unique_id}.wav")

    model = "playai-tts"
    voice = "Fritz-PlayAI"
    response_format = "wav"

    try:
        response = client.audio.speech.create(
            model=model,
            voice=voice,
            input=text,
            response_format=response_format
        )
        response.write_to_file(speech_file_path)
        return speech_file_path

    except Exception as e:
        # Check if error is rate limit exceeded
        if hasattr(e, "response") and "rate_limit_exceeded" in str(e.response):
            print("⚠️ Groq TTS rate limit reached. Skipping audio generation.")
        else:
            print(f"⚠️ TTS generation failed: {e}")
        # Return None so app can still show text response
        return None
