
import os
from openai import OpenAI


def generate_text(prompt):
    api_key = os.getenv("GAPGPT_API_KEY")

    if not api_key:
        raise ValueError("GapGPT API key is not configured.")

    client = OpenAI(
        api_key=api_key,
        base_url="https://api.gapgpt.app/v1",
    )

    response = client.chat.completions.create(
        model="gapgpt-agent",
        messages=[
            {"role": "user", "content": prompt}
        ],
    )

    return response.choices[0].message.content