import os
from groq import Groq
import json

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def generate_quiz_from_context(context: str, num_questions: int = 5) -> list:
    """Uses Groq to generate a JSON array of quiz questions from the provided context."""
    if not context.strip():
        return []

    try:
        # Limit context to avoid token limits. Approx 10,000 chars should be plenty for 5 questions
        limited_context = context[:10000] 
        prompt = f"""
You are an educational AI assistant. Generate a multiple-choice quiz based on the following text context.
Return ONLY a strictly valid JSON object with a single key "questions" containing an array of objects.
Do not use any markdown formatting or extra text.
Each question object must have:
- "question": The question text
- "options": An array of exactly 4 possible strings as answers
- "answer": The exact string from "options" that is the correct answer
- "explanation": A brief explanation of why the answer is correct

Generate exactly {num_questions} questions.

Context:
{limited_context}
"""
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)
        return data.get("questions", [])
    except Exception as e:
        print("Quiz Generation Error:", str(e))
        return []
