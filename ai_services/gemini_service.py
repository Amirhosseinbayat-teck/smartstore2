from django.conf import settings
from google import genai


def generate_text(prompt):
    if not settings.GEMINI_API_KEY:
        raise ValueError("Gemini API key is not configured.")

    client = genai.Client(
        api_key=settings.GEMINI_API_KEY
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return response.text