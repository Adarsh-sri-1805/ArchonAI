import os
import time

from dotenv import load_dotenv
from google import genai

from app.core.config import settings
from app.core.logger import logger

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def generate_response(prompt: str) -> str:
    """
    Generate a response using Gemini with retry logic.
    """

    max_retries = 3
    delay = 1

    for attempt in range(1, max_retries + 1):

        try:

            logger.info(
                "Sending request to Gemini (Attempt %d/%d)",
                attempt,
                max_retries,
            )

            start = time.perf_counter()

            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
            )

            logger.info(
                "Gemini responded in %.2fs",
                time.perf_counter() - start,
            )

            return response.text

        except Exception as e:

            logger.warning(
                "Gemini request failed (Attempt %d/%d): %s",
                attempt,
                max_retries,
                str(e),
            )

            if attempt == max_retries:
                logger.exception("Gemini failed after all retries.")
                raise

            logger.info(
                "Retrying in %d second(s)...",
                delay,
            )

            time.sleep(delay)

            delay *= 2