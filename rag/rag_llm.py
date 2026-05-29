import os
from dotenv import load_dotenv
from cerebras.cloud.sdk import Cerebras
from rag_prompts import SCIENTIFIC_QUERY_VALIDATOR_SYSTEM, QUERY_REWRITER_SYSTEM

load_dotenv()

client = Cerebras(api_key=os.getenv("CEREBRAS_API_KEY"))


def validate_query(query: str) -> bool:
    try:
        response = client.chat.completions.create(
            model="qwen-3-235b-a22b-instruct-2507",
            messages=[
                {
                    "role": "system",
                    "content":  SCIENTIFIC_QUERY_VALIDATOR_SYSTEM
                },
                {"role": "user", "content": query}
            ],
            temperature=0,
            max_tokens=50
        )

        content = response.choices[0].message.content.strip().lower()
        print(content)
        if content.startswith("valid"):
            return True
        elif content.startswith("invalid"):
            return False
        else:
            print("Unexpected response format during query validation.")
            return False  # fallback for unexpected output

    except Exception:
        print("Error occurred while validating query.")
        return False


def rewrite_query(query: str):
    try:
        response = client.chat.completions.create(
            model="qwen-3-235b-a22b-instruct-2507",
            messages=[
                {"role": "system", "content": QUERY_REWRITER_SYSTEM},
                {"role": "user", "content": query}
            ],
            temperature=0.1,
            max_tokens=200
        )

        if response and response.choices and response.choices[0].message.content:
            return response.choices[0].message.content.strip()

        return query

    except Exception:
        return query



