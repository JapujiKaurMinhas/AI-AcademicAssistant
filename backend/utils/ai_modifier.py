import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

import sys
# Ensure parent directory is in path for config imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from config import LLM_MODEL_VERSATILE
except ImportError:
    LLM_MODEL_VERSATILE = "groq/compound"

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def detect_plagiarism(text: str) -> dict:
    """Analyze text to check if it is AI-generated/Plagiarized."""
    try:
        prompt = f"""
You are an expert AI detector and plagiarism checker. Analyze the following text and determine the probability (0 to 100) that it is AI-generated or plagiarized.
Respond ONLY with a JSON object in the following format:
{{"score": 85, "analysis": "Detailed explanation of why it is flagged or not."}}

Text to analyze:
{text}
"""
        response = client.chat.completions.create(
            model=LLM_MODEL_VERSATILE,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        import json
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print("Plagiarism Check Error:", str(e))
        return {"score": 50, "analysis": "Could not determine due to an error."}

def humanize_text(text: str) -> str:
    """Rewrite text to sound authentically human."""
    try:
        prompt = f"""
You are an expert human copywriter. Your task is to take the following text, which might be AI-generated, and rewrite it completely so that it sounds like a normal human wrote it naturally. 
Remove any repetitive AI structures, overly formal robotic phrasing, and use a compelling, natural conversational academic tone. Return ONLY the rewritten text, without any additional comments or formatting.

Original Text:
{text}
"""
        response = client.chat.completions.create(
            model=LLM_MODEL_VERSATILE,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("Humanize Error:", str(e))
        return text
