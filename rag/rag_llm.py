# import os
# from dotenv import load_dotenv
# from openai import OpenAI
# from rag_prompts import SCIENTIFIC_QUERY_VALIDATOR_SYSTEM, QUERY_REWRITER_SYSTEM

# load_dotenv()

# client = OpenAI(
#     base_url="https://api.groq.com/openai/v1",
#     api_key=os.getenv("GROQ_API_KEY"),
# )
# MODEL = "openai/gpt-oss-120b"


# def validate_query(query: str) -> bool:
#     try:
#         response = client.chat.completions.create(
#             model=MODEL,
#             messages=[
#                 {"role": "system", "content": SCIENTIFIC_QUERY_VALIDATOR_SYSTEM},
#                 {"role": "user", "content": query},
#             ],
#             temperature=0,
#             max_tokens=100,
#         )
#         content = (response.choices[0].message.content or "").strip().lower()
#         print("validator says:", repr(content))
#         if content.startswith("valid"):
#             return True
#         if content.startswith("invalid"):
#             return False
#         print("Unexpected response format during query validation.")
#         return False
#     except Exception as e:
#         print(f"Error validating query: {type(e).__name__}: {e}")
#         return False


# def rewrite_query(query: str):
#     try:
#         response = client.chat.completions.create(
#             model=MODEL,
#             messages=[
#                 {"role": "system", "content": QUERY_REWRITER_SYSTEM},
#                 {"role": "user", "content": query},
#             ],
#             temperature=0.1,
#             max_tokens=200,
#         )
#         text = response.choices[0].message.content
#         return text.strip() if text else query
#     except Exception as e:
#         print(f"Error rewriting query: {type(e).__name__}: {e}")
#         return query




import os
from dotenv import load_dotenv
from openai import OpenAI
from rag_prompts import SCIENTIFIC_QUERY_VALIDATOR_SYSTEM, QUERY_REWRITER_SYSTEM

load_dotenv()

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY"),
)
MODEL = "openai/gpt-oss-120b"


def validate_query(query: str) -> bool:
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SCIENTIFIC_QUERY_VALIDATOR_SYSTEM},
                {"role": "user", "content": query},
            ],
            temperature=0,
            max_tokens=500,
        )
        print("FULL RESPONSE:", response.choices[0].message)
        content = (response.choices[0].message.content or "").strip().lower()
        print("validator says:", repr(content))
        if content.startswith("valid"):
            return True
        if content.startswith("invalid"):
            return False
        print("Unexpected response format during query validation.")
        return False
    except Exception as e:
        print(f"Error validating query: {type(e).__name__}: {e}")
        return False


def rewrite_query(query: str):
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": QUERY_REWRITER_SYSTEM},
                {"role": "user", "content": query},
            ],
            temperature=0.1,
            max_tokens=200,
        )
        text = response.choices[0].message.content
        return text.strip() if text else query
    except Exception as e:
        print(f"Error rewriting query: {type(e).__name__}: {e}")
        return query