
from groq import Groq
import base64
import os

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
def analyze_image(image_paths, user_prompt=None):
    """
    image_paths: str (single) or list of str (multiple image paths)
    user_prompt: optional text prompt
    """
    try:
        # Har image ko base64 karo
        image_contents = []
        for path in image_paths:
            with open(path, "rb") as f:
                img_bytes = f.read()
            b64_img = base64.b64encode(img_bytes).decode("utf-8")
            image_contents.append(
                {"type": "image_url","image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}}
                )

        prompt_text = user_prompt or "Describe these images in detail."

        # Groq ko multiple images bhejo
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_text},
                        *image_contents  # yahan saari images daal do # * mtlb list ke saare items ko alag-alag nikaal do yahan
                    ]
                }
            ],
            temperature=0.7,
            max_completion_tokens=1024,
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"❌ Vision model error: {str(e)}"
    
    
    