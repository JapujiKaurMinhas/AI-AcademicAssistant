import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable not set")

client = Groq(api_key=GROQ_API_KEY)

def get_system_prompt():
    return """You are a highly capable AI Academic Assistant. Your role is to provide clear, concise, and structured educational explanations. 
Rules for your output:
1. Always use **Markdown** for formatting.
2. Use **bolding** for important terms and definitions.
3. Use structured **bullet points** or **numbered lists** for readability.
4. Use distinct **sections** with titles (e.g., using `###` or bold text).
5. Ensure the structure is logical, scanning-friendly, and easy to read.
6. Provide examples where relevant.
7. Be professional, academic, yet encouraging."""

def generate_explanation(prompt: str, context: str = ""):
    """Generates an AI explanation using the Groq Llama 3.3 model with advanced formatting."""
    system_prompt = get_system_prompt()
    
    user_content = f"Question: {prompt}\n\n"
    if context:
        user_content += f"Context from uploaded document:\n{context}"

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            model="llama-3.3-70b-versatile",
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Error communicating with AI service: {str(e)}"

def generate_document_intel(text: str):
    """Generates both summary and key points in a single AI call for efficiency."""
    system_prompt = get_system_prompt()
    user_content = f"""Please analyze the following academic document and provide two specific sections:
1. **EXECUTIVE SUMMARY**: A concise overview of the core themes.
2. **CORE CONCEPT NOTES**: A detailed list of key study points and definitions.

Separate these two sections clearly with a delimiter like '---SECTION_BREAK---'.

Content:
{text[:12000]}"""

    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            model="llama-3.1-8b-instant",  # Extremely fast, perfect for high-speed summaries
            temperature=0.3,
        )
        full_text = response.choices[0].message.content
        
        if "---SECTION_BREAK---" in full_text:
            parts = full_text.split("---SECTION_BREAK---")
            return parts[0].strip(), parts[1].strip()
            
        # Robust Fallback parsing
        if "**CORE CONCEPT NOTES**" in full_text:
            parts = full_text.split("**CORE CONCEPT NOTES**")
            return parts[0].strip(), "**CORE CONCEPT NOTES**\n" + parts[1].strip()
        
        return full_text, "AI generated common study notes within the summary above."
    except Exception as e:
        return f"Error generating intellect: {str(e)}", "Please try again later."

def extract_topics(text: str):
    """Simple keyword/topic extractor using LLM for analytics."""
    prompt = f"Extract the top 3-5 keywords or a general topic from this text. Reply with ONLY a comma-separated list of keywords. Text: {text}"
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0,
            max_tokens=25
        )
        return response.choices[0].message.content.strip()
    except:
        return "General"
