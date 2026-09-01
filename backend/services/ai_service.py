import os
import time
import json
import asyncio
from groq import Groq, AsyncGroq
from dotenv import load_dotenv
from sqlmodel import Session, select

from models.processed_document import ProcessedDocument
from utils.text_chunker import split_text_into_chunks, semantic_chunk_text
from config import (
    MAX_INPUT_TOKENS,
    MAX_OUTPUT_TOKENS,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    MAX_DOCUMENT_CHUNKS,
    REQUEST_DELAY,
    MAX_RETRIES,
    LLM_MODEL_INTEL,
    LLM_MODEL_VERSATILE
)

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable not set")

client = Groq(api_key=GROQ_API_KEY)
async_client = AsyncGroq(api_key=GROQ_API_KEY)

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

def estimate_tokens(text: str) -> int:
    """Conservative token estimator for English text (approx 3.5 chars per token + safety margin)."""
    return int(len(text) / 3.5) + 50

import re

def call_groq_with_retries(messages, model, temperature=0.3, max_tokens=None, response_format=None):
    """Wraps Groq API calls in a retry loop with exponential backoff on rate limits."""
    # Use 5 retries to ensure enough safety margin on free tiers
    retries_limit = max(MAX_RETRIES, 5)
    for attempt in range(retries_limit + 1):
        try:
            params = {
                "messages": messages,
                "model": model,
                "temperature": temperature,
            }
            if max_tokens:
                params["max_tokens"] = max_tokens
            if response_format:
                params["response_format"] = response_format
                
            response = client.chat.completions.create(**params)
            return response.choices[0].message.content
        except Exception as e:
            err_str = str(e).lower()
            is_rate_limit = any(term in err_str for term in ["rate_limit", "limit exceeded", "429", "413", "tpm"])
            if is_rate_limit and attempt < retries_limit:
                # Default backoff
                wait_time = (2 ** attempt) + REQUEST_DELAY + 2.0
                
                # Parse exact retry time if provided by Groq
                match = re.search(r'try again in (\d+(?:\.\d+)?)(s|ms)', err_str)
                if match:
                    val = float(match.group(1))
                    unit = match.group(2)
                    wait_time = (val / 1000.0) + 0.5 if unit == 'ms' else val + 0.5
                    
                print(f"Rate limit hit. Sleeping {wait_time:.3f}s (Attempt {attempt+1}/{retries_limit}). Error: {str(e)}")
                time.sleep(wait_time)
            else:
                raise e

async def call_groq_async_with_retries(messages, model, temperature=0.3, max_tokens=None, response_format=None, semaphore=None):
    """Async wrapper for Groq API calls in a retry loop with exponential backoff on rate limits."""
    retries_limit = max(MAX_RETRIES, 5)
    if semaphore is None:
        semaphore = asyncio.Semaphore(3)
        
    async with semaphore:
        for attempt in range(retries_limit + 1):
            try:
                params = {
                    "messages": messages,
                    "model": model,
                    "temperature": temperature,
                }
                if max_tokens:
                    params["max_tokens"] = max_tokens
                if response_format:
                    params["response_format"] = response_format
                    
                response = await async_client.chat.completions.create(**params)
                return response.choices[0].message.content
            except Exception as e:
                err_str = str(e).lower()
                is_rate_limit = any(term in err_str for term in ["rate_limit", "limit exceeded", "429", "413", "tpm"])
                if is_rate_limit and attempt < retries_limit:
                    # Default backoff
                    wait_time = (2 ** attempt) + REQUEST_DELAY + 2.0
                    
                    # Parse exact retry time if provided by Groq
                    match = re.search(r'try again in (\d+(?:\.\d+)?)(s|ms)', err_str)
                    if match:
                        val = float(match.group(1))
                        unit = match.group(2)
                        wait_time = (val / 1000.0) + 0.5 if unit == 'ms' else val + 0.5
                        
                    print(f"Async Rate limit hit. Sleeping {wait_time:.3f}s (Attempt {attempt+1}/{retries_limit}). Error: {str(e)}")
                    await asyncio.sleep(wait_time)
                else:
                    raise e

def generate_explanation(prompt: str, context: str = ""):
    """Generates an AI explanation using the Groq versatile model with advanced formatting."""
    system_prompt = get_system_prompt()
    
    user_content = f"Question: {prompt}\n\n"
    if context:
        user_content += f"Context from uploaded document:\n{context}"

    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        content = call_groq_with_retries(messages, model=LLM_MODEL_VERSATILE, temperature=0.3)
        return content
    except Exception as e:
        return f"Error communicating with AI service: {str(e)}"

def generate_document_intel(text: str, filename: str = None, session: Session = None):
    """
    Generates both summary and key points for a document (Synchronous Version).
    Uses database caching and the new semantic chunker.
    """
    # 1. Check database cache first
    if filename and session:
        try:
            statement = select(ProcessedDocument).where(ProcessedDocument.filename == filename)
            cached_doc = session.exec(statement).first()
            if cached_doc:
                print(f"--- Cache HIT for '{filename}'. Loading pre-processed intel. ---")
                return cached_doc.summary, cached_doc.key_points
        except Exception as e:
            print(f"!!! Database Cache Read Error: {str(e)}")

    print(f"--- Cache MISS or regeneration for '{filename or 'unknown'}'. Processing... ---")
    estimated_tokens = estimate_tokens(text)
    
    try:
        # 2. Short Document Processing (single LLM request)
        if estimated_tokens <= (MAX_INPUT_TOKENS - 500):
            print(f"--- Short document detected (~{estimated_tokens} tokens). Processing in a single call. ---")
            system_prompt = get_system_prompt()
            user_content = f"""Please analyze the following academic document and provide two specific sections:
1. **EXECUTIVE SUMMARY**: A concise overview of the core themes.
2. **CORE CONCEPT NOTES**: A detailed list of key study points and definitions.

Separate these two sections clearly with a delimiter like '---SECTION_BREAK---'.

Content:
{text}"""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ]
            
            full_text = call_groq_with_retries(messages, model=LLM_MODEL_INTEL, temperature=0.3)
            
            # Parse output
            if "---SECTION_BREAK---" in full_text:
                parts = full_text.split("---SECTION_BREAK---")
                final_summary, final_key_points = parts[0].strip(), parts[1].strip()
            elif "**CORE CONCEPT NOTES**" in full_text:
                parts = full_text.split("**CORE CONCEPT NOTES**")
                final_summary, final_key_points = parts[0].strip(), "**CORE CONCEPT NOTES**\n" + parts[1].strip()
            else:
                final_summary, final_key_points = full_text, "AI generated common study notes within the summary above."

        # 3. Long Document Processing (Sequential Map-Reduce)
        else:
            print(f"--- Long document detected (~{estimated_tokens} tokens). Starting chunked pipeline. ---")
            
            # Use Semantic Chunking
            chunks = semantic_chunk_text(text, max_chunk_size=CHUNK_SIZE)
            
            if len(chunks) > MAX_DOCUMENT_CHUNKS:
                print(f"--- Document requires {len(chunks)} chunks. Restricting to first {MAX_DOCUMENT_CHUNKS} chunks. ---")
                chunks = chunks[:MAX_DOCUMENT_CHUNKS]
            
            print(f"--- Splitting completed: {len(chunks)} semantic chunks. ---")
            
            chunk_summaries = []
            chunk_key_points = []
            
            system_prompt = get_system_prompt()
            
            # Process each chunk sequentially
            for idx, chunk in enumerate(chunks):
                print(f"--- Processing chunk {idx + 1}/{len(chunks)} ({len(chunk)} characters) ---")
                
                chunk_prompt = f"""Please analyze this section of an academic document and extract:
1. **SUMMARY**: A brief, concise overview of this section.
2. **KEY POINTS**: A detailed bulleted list of key study concepts, definitions, formulas, or key arguments.

Separate these sections with '---SECTION_BREAK---'.

Section Content:
{chunk}"""
                
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": chunk_prompt}
                ]
                
                chunk_resp = call_groq_with_retries(messages, model=LLM_MODEL_INTEL, temperature=0.3)
                
                if "---SECTION_BREAK---" in chunk_resp:
                    parts = chunk_resp.split("---SECTION_BREAK---")
                    cs, ck = parts[0].strip(), parts[1].strip()
                elif "**KEY POINTS**" in chunk_resp:
                    parts = chunk_resp.split("**KEY POINTS**")
                    cs, ck = parts[0].strip(), "**KEY POINTS**\n" + parts[1].strip()
                else:
                    cs, ck = chunk_resp, "Refer to the summary above."
                    
                chunk_summaries.append(cs)
                chunk_key_points.append(ck)
                
                if idx < len(chunks) - 1:
                    time.sleep(REQUEST_DELAY)
            
            # Step 3b: Synthesize final executive summary
            print("--- Synthesizing final Executive Summary ---")
            combined_summaries = "\n\n".join([f"### Section {i+1} Summary:\n{s}" for i, s in enumerate(chunk_summaries)])
            summary_synthesis_prompt = f"""You are a highly capable AI Academic Assistant.
Analyze the following section summaries of an academic document and write a single cohesive **EXECUTIVE SUMMARY** for the entire document.
Ensure it is professional, concise, structures the core themes logically, uses markdown, and highlights key facts and conclusions.

Summaries:
{combined_summaries}"""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": summary_synthesis_prompt}
            ]
            
            time.sleep(REQUEST_DELAY)
            final_summary = call_groq_with_retries(messages, model=LLM_MODEL_INTEL, temperature=0.3)
            
            # Step 3c: Synthesize final core concept notes
            print("--- Synthesizing final Core Concept Notes ---")
            combined_key_points = "\n\n".join([f"### Section {i+1} Study Notes:\n{k}" for i, k in enumerate(chunk_key_points)])
            points_synthesis_prompt = f"""You are a highly capable AI Academic Assistant.
Analyze the following study notes and key points from different sections of an academic document, and compile a single structured, comprehensive set of **CORE CONCEPT NOTES** for the entire document.
Ensure it:
1. Groups related concepts logically.
2. Preserves all definitions, formulas, technical terminology, and key study facts.
3. Uses clear markdown headers, bold terms, and bullet points.

Intermediate Study Notes:
{combined_key_points}"""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": points_synthesis_prompt}
            ]
            
            time.sleep(REQUEST_DELAY)
            final_key_points = call_groq_with_retries(messages, model=LLM_MODEL_INTEL, temperature=0.3)
            
        # 4. Save to database cache
        if filename and session:
            try:
                chunks_data = []
                if estimated_tokens > (MAX_INPUT_TOKENS - 500):
                    chunks_data = [{"summary": s, "key_points": k} for s, k in zip(chunk_summaries, chunk_key_points)]
                chunks_json = json.dumps(chunks_data)
                
                existing_doc = session.exec(select(ProcessedDocument).where(ProcessedDocument.filename == filename)).first()
                if existing_doc:
                    existing_doc.extracted_text = text
                    existing_doc.chunks_json = chunks_json
                    existing_doc.summary = final_summary
                    existing_doc.key_points = final_key_points
                    session.add(existing_doc)
                else:
                    new_doc = ProcessedDocument(
                        filename=filename,
                        extracted_text=text,
                        chunks_json=chunks_json,
                        summary=final_summary,
                        key_points=final_key_points
                    )
                    session.add(new_doc)
                session.commit()
                print(f"--- Successfully cached processed intel for '{filename}' in database ---")
            except Exception as cache_err:
                print(f"!!! Database Cache Write Error: {str(cache_err)}")
                
        return final_summary, final_key_points
        
    except Exception as e:
        err_str = str(e).lower()
        if "413" in err_str or "request too large" in err_str or "tpm" in err_str:
            raise ValueError("Document is too large to process in a single AI request.")
        else:
            raise e

async def async_generate_document_intel(text: str, filename: str = None, session: Session = None, progress_callback = None):
    """
    Generates both summary and key points for a document (Asynchronous, Optimized Version).
    Uses Semantic Chunking and Parallel Map-Reduce with a Rate Limiter Semaphore.
    
    `progress_callback` is an async function: `async def callback(percent: int, phase: str)`
    """
    # Helper to report progress
    async def update_progress(percent: int, phase: str):
        if progress_callback:
            await progress_callback(percent, phase)

    # 1. Check database cache first
    if filename and session:
        try:
            await update_progress(5, "Checking database cache...")
            statement = select(ProcessedDocument).where(ProcessedDocument.filename == filename)
            cached_doc = session.exec(statement).first()
            if cached_doc:
                print(f"--- Cache HIT for '{filename}'. Loading pre-processed intel. ---")
                await update_progress(100, "Completed (Cache Hit)")
                return cached_doc.summary, cached_doc.key_points
        except Exception as e:
            print(f"!!! Database Cache Read Error: {str(e)}")

    print(f"--- Cache MISS or regeneration for '{filename or 'unknown'}'. Async Processing... ---")
    estimated_tokens = estimate_tokens(text)
    
    try:
        # 2. Short Document Processing (single LLM request)
        if estimated_tokens <= (MAX_INPUT_TOKENS - 500):
            print(f"--- Short document detected (~{estimated_tokens} tokens). Processing in a single call. ---")
            await update_progress(20, "Analyzing document (Single-Call Pipeline)...")
            system_prompt = get_system_prompt()
            user_content = f"""Please analyze the following academic document and provide two specific sections:
1. **EXECUTIVE SUMMARY**: A concise overview of the core themes.
2. **CORE CONCEPT NOTES**: A detailed list of key study points and definitions.

Separate these two sections clearly with a delimiter like '---SECTION_BREAK---'.

Content:
{text}"""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ]
            
            full_text = await call_groq_async_with_retries(messages, model=LLM_MODEL_INTEL, temperature=0.3)
            await update_progress(80, "Parsing intelligence output...")
            
            # Parse output
            if "---SECTION_BREAK---" in full_text:
                parts = full_text.split("---SECTION_BREAK---")
                final_summary, final_key_points = parts[0].strip(), parts[1].strip()
            elif "**CORE CONCEPT NOTES**" in full_text:
                parts = full_text.split("**CORE CONCEPT NOTES**")
                final_summary, final_key_points = parts[0].strip(), "**CORE CONCEPT NOTES**\n" + parts[1].strip()
            else:
                final_summary, final_key_points = full_text, "AI generated common study notes within the summary above."

        # 3. Long Document Processing (Parallel Map-Reduce with Semaphore)
        else:
            print(f"--- Long document detected (~{estimated_tokens} tokens). Running Parallel Map-Reduce. ---")
            await update_progress(10, "Extracting semantic segments...")
            
            # Run CPU-heavy semantic chunking in thread pool to not block event loop
            chunks = await asyncio.to_thread(semantic_chunk_text, text, CHUNK_SIZE)
            
            if len(chunks) > MAX_DOCUMENT_CHUNKS:
                print(f"--- Document requires {len(chunks)} chunks. Restricting to first {MAX_DOCUMENT_CHUNKS} chunks. ---")
                chunks = chunks[:MAX_DOCUMENT_CHUNKS]
                
            num_chunks = len(chunks)
            await update_progress(15, f"Segmented into {num_chunks} thematic chunks. Launching concurrent summaries...")
            
            # Map Phase: process chunks in parallel using semaphore
            # Concurrency limit = 3 to respect Groq rate limits (RPM/TPM)
            sem = asyncio.Semaphore(3)
            completed_chunks = 0
            
            async def process_chunk_task(idx, chunk):
                nonlocal completed_chunks
                chunk_prompt = f"""Please analyze this section of an academic document and extract:
1. **SUMMARY**: A brief, concise overview of this section.
2. **KEY POINTS**: A detailed bulleted list of key study concepts, definitions, formulas, or key arguments.

Separate these sections with '---SECTION_BREAK---'.

Section Content:
{chunk}"""
                messages = [
                    {"role": "system", "content": get_system_prompt()},
                    {"role": "user", "content": chunk_prompt}
                ]
                
                resp = await call_groq_async_with_retries(messages, model=LLM_MODEL_INTEL, temperature=0.3, semaphore=sem)
                
                completed_chunks += 1
                # Progress ranges from 20% to 70% during chunk processing
                prog = 20 + int((completed_chunks / num_chunks) * 50)
                await update_progress(prog, f"Summarized segments: {completed_chunks}/{num_chunks}...")
                
                if "---SECTION_BREAK---" in resp:
                    parts = resp.split("---SECTION_BREAK---")
                    return parts[0].strip(), parts[1].strip()
                elif "**KEY POINTS**" in resp:
                    parts = resp.split("**KEY POINTS**")
                    return parts[0].strip(), "**KEY POINTS**\n" + parts[1].strip()
                else:
                    return resp, "Refer to the summary above."

            # Run parallel map tasks
            tasks = [process_chunk_task(i, chunk) for i, chunk in enumerate(chunks)]
            results = await asyncio.gather(*tasks)
            
            chunk_summaries = [r[0] for r in results]
            chunk_key_points = [r[1] for r in results]
            
            # Reduce Phase: Synthesize final outputs
            await update_progress(75, "Synthesizing final Executive Summary...")
            combined_summaries = "\n\n".join([f"### Section {i+1} Summary:\n{s}" for i, s in enumerate(chunk_summaries)])
            summary_synthesis_prompt = f"""You are a highly capable AI Academic Assistant.
Analyze the following section summaries of an academic document and write a single cohesive **EXECUTIVE SUMMARY** for the entire document.
Ensure it is professional, concise, structures the core themes logically, uses markdown, and highlights key facts and conclusions.

Summaries:
{combined_summaries}"""
            
            messages_sum = [
                {"role": "system", "content": get_system_prompt()},
                {"role": "user", "content": summary_synthesis_prompt}
            ]
            
            # Run summary synthesis
            final_summary = await call_groq_async_with_retries(messages_sum, model=LLM_MODEL_INTEL, temperature=0.3)
            
            await update_progress(85, "Synthesizing final Core Concept Notes...")
            combined_key_points = "\n\n".join([f"### Section {i+1} Study Notes:\n{k}" for i, k in enumerate(chunk_key_points)])
            points_synthesis_prompt = f"""You are a highly capable AI Academic Assistant.
Analyze the following study notes and key points from different sections of an academic document, and compile a single structured, comprehensive set of **CORE CONCEPT NOTES** for the entire document.
Ensure it:
1. Groups related concepts logically.
2. Preserves all definitions, formulas, technical terminology, and key study facts.
3. Uses clear markdown headers, bold terms, and bullet points.

Intermediate Study Notes:
{combined_key_points}"""
            
            messages_pts = [
                {"role": "system", "content": get_system_prompt()},
                {"role": "user", "content": points_synthesis_prompt}
            ]
            
            # Run key points synthesis
            final_key_points = await call_groq_async_with_retries(messages_pts, model=LLM_MODEL_INTEL, temperature=0.3)

        # 4. Save to database cache
        if filename and session:
            await update_progress(95, "Caching generated intelligence...")
            chunks_data = []
            if estimated_tokens > (MAX_INPUT_TOKENS - 500):
                chunks_data = [{"summary": s, "key_points": k} for s, k in zip(chunk_summaries, chunk_key_points)]
            chunks_json = json.dumps(chunks_data)
            
            existing_doc = session.exec(select(ProcessedDocument).where(ProcessedDocument.filename == filename)).first()
            if existing_doc:
                existing_doc.extracted_text = text
                existing_doc.chunks_json = chunks_json
                existing_doc.summary = final_summary
                existing_doc.key_points = final_key_points
                session.add(existing_doc)
            else:
                new_doc = ProcessedDocument(
                    filename=filename,
                    extracted_text=text,
                    chunks_json=chunks_json,
                    summary=final_summary,
                    key_points=final_key_points
                )
                session.add(new_doc)
            session.commit()
            print(f"--- Successfully cached async processed intel for '{filename}' ---")
            
        await update_progress(100, "Completed!")
        return final_summary, final_key_points
        
    except Exception as e:
        err_str = str(e).lower()
        if "413" in err_str or "request too large" in err_str or "tpm" in err_str:
            raise ValueError("Document is too large to process.")
        else:
            raise e

def extract_topics(text: str):
    """Simple keyword/topic extractor using LLM for analytics."""
    prompt = f"Extract the top 3-5 keywords or a general topic from this text. Reply with ONLY a comma-separated list of keywords. Text: {text}"
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=LLM_MODEL_VERSATILE,
            temperature=0,
            max_tokens=25
        )
        return response.choices[0].message.content.strip()
    except:
        return "General"
