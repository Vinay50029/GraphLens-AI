import base64
import os
import requests
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

def process_image_with_groq_vision(base64_image: str) -> str:
    """
    Sends a base64 encoded image to Groq's Vision model and returns the transcription/description.
    """
    if not GROQ_API_KEY:
        return "ERROR: GROQ_API_KEY not set."

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = (
        "Transcribe all text from this image exactly. "
        "If there are charts, diagrams, or tables, describe them in detail. "
        "Provide only the extracted text and descriptions without any introductory conversational text."
    )

    payload = {
        "model": "llama-3.2-11b-vision-preview",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "temperature": 0.1,
        "max_tokens": 2048
    }

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        print(f"Groq Vision API error: {e}")
        return f"ERROR: Failed to process page image. {str(e)}"
