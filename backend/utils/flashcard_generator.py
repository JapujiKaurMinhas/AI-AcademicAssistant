import os
from groq import Groq
import json

import sys
# Ensure parent directory is in path for config imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from config import LLM_MODEL_VERSATILE
except ImportError:
    LLM_MODEL_VERSATILE = "groq/compound"

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def generate_flashcards_from_context(context: str, num_cards: int = 10) -> list:
    """Uses Groq to generate a JSON array of flashcards from the provided context."""
    if not context.strip():
        return []
    try:
        # Limit context to avoid token limits
        limited_context = context[:10000]
        prompt = f"""
You are an educational AI assistant specialized in creating study flashcards.
Generate flashcards based on the following text context.
Return ONLY a strictly valid JSON object with a single key "flashcards" containing an array of objects.
Do not use any markdown formatting or extra text.
Each flashcard object must have:
- "front": The question, term, or concept (keep it concise and clear)
- "back": The answer, definition, or explanation (detailed but not too long)
- "category": A short category/topic label for the card (e.g., "Definition", "Concept", "Formula", "Key Fact")
- "difficulty": One of "easy", "medium", or "hard"

Guidelines:
- Focus on the most important concepts, definitions, and key facts
- Make flashcards that test understanding, not just memorization
- Vary the types: definitions, explanations, comparisons, applications
- Ensure front and back are distinct — don't repeat the same text

Generate exactly {num_cards} flashcards.

Context:
{limited_context}
"""
        response = client.chat.completions.create(
            model=LLM_MODEL_VERSATILE,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.4,
        )
        data = json.loads(response.choices[0].message.content)
        return data.get("flashcards", [])
    except Exception as e:
        print("Flashcard Generation Error:", str(e))
        return []
