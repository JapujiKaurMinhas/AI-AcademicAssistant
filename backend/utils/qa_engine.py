from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

print("GROQ KEY:", os.environ.get("GROQ_API_KEY"))

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
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return response.choices[0].message.content

    except Exception as e:
        print("GROQ ERROR:", str(e))
        return "Error generating answer"