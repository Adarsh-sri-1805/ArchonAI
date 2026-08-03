import os

from dotenv import load_dotenv
from google import genai
import time

from app.core.logger import logger
from app.core.config import settings

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def generate_response(prompt: str) -> str:
    start = time.perf_counter()

    logger.info("Sending request to Gemini")

    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=prompt,
    )

    logger.info(
        "Gemini responded in %.2fs",
        time.perf_counter() - start,
    )

    return response.text