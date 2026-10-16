

from django.conf import settings
from groq import Groq


def generate_text(prompt):
    if not settings.GROQ_API_KEY:
        raise ValueError("Groq API key is not configured.")

    client = Groq(
        api_key=settings.GROQ_API_KEY
    )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.7
    )

    return response.choices[0].message.content