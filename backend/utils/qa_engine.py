from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

print("GROQ KEY:", os.environ.get("GROQ_API_KEY"))

import sys
import os
# Ensure parent directory is in path for config imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from config import LLM_MODEL_VERSATILE
except ImportError:
    LLM_MODEL_VERSATILE = "groq/compound"

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def generate_answer(context, question):

    try:

        prompt = f"""
You are an AI Academic Assistant. Use the context below to answer the question in a highly structured and readable format.

Rules:
1. Use **bolding** for key terms.
2. Use **bullet points** or **numbered lists** for lists.
3. Use **Markdown** headers (###) if the answer is long.
4. If the answer is not in the context, say "I could not find it in the document."

Context:
{context}

Question:
{question}

Answer:
"""

        response = client.chat.completions.create(
            model=LLM_MODEL_VERSATILE,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return response.choices[0].message.content

    except Exception as e:
        print("GROQ ERROR:", str(e))
        return "Error generating answer"