import os

from dotenv import load_dotenv
from google import genai

from app.core.config import settings

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def generate_response(prompt: str) -> str:
    """
    Generate a response using Gemini.
    """

    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=prompt,
    )

    return response.text