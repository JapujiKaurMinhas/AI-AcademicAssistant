import re
import sys
import os

# Add parent directory of utils (backend/) to sys.path if not present, to ensure config can be imported.
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

try:
    from config import CHUNK_SIZE, CHUNK_OVERLAP
except ImportError:
    CHUNK_SIZE = 8000
    CHUNK_OVERLAP = 800

# Global cached embedding model for semantic chunking
_embedding_model = None

def get_embedding_model():
    """Lazy load and cache the sentence-transformers model to optimize startup time."""
    global _embedding_model
    if _embedding_model is None:
        print("--- Loading SentenceTransformer('all-MiniLM-L6-v2') for semantic chunking... ---")
        from sentence_transformers import SentenceTransformer
        # Disable tokenizers parallelism warning
        os.environ["TOKENIZERS_PARALLELISM"] = "false"
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        print("--- SentenceTransformer loaded successfully ---")
    return _embedding_model

def split_into_sentences(text: str, max_sentence_len: int = 3500) -> list:
    """
    Split text into sentences using regex boundary detection.
    If a sentence is longer than max_sentence_len (e.g. due to missing spacing in PDF extraction),
    it splits it into smaller sub-sentences to prevent embedding truncation and size limit issues.
    """
    if not text:
        return []
    # Normalize whitespace and carriage returns
    text = re.sub(r'\s+', ' ', text.replace("\r\n", "\n")).strip()
    
    # Split on sentence ending punctuation followed by spaces and an uppercase letter (or end of string)
    sentence_end = re.compile(r'(?<=[.!?])\s+(?=[A-Z0-9])')
    raw_sentences = sentence_end.split(text)
    
    sentences = []
    for s in raw_sentences:
        s = s.strip()
        if not s:
            continue
        
        # If the sentence itself is extremely long, split it by length boundary
        if len(s) > max_sentence_len:
            print(f"--- Sentence too long ({len(s)} chars). Splitting by character limit... ---")
            for i in range(0, len(s), max_sentence_len):
                sub_s = s[i:i + max_sentence_len].strip()
                if sub_s:
                    sentences.append(sub_s)
        else:
            sentences.append(s)
            
    return sentences

def semantic_chunk_text(text: str, max_chunk_size: int = 8000, min_chunk_size: int = 1200, k: float = 1.0) -> list:
    """
    Research-based Semantic Chunking algorithm for MTech:
    1. Splits input text into discrete sentences (pre-splitting long ones).
    2. Computes embedding vectors using a SentenceTransformer.
    3. Calculates Cosine Distance (1 - CosineSimilarity) between adjacent sentences.
    4. Computes a dynamic splitting threshold: Threshold = Mean(Distances) + k * StdDev(Distances).
    5. Splits text at boundaries where distance exceeds the threshold, respecting min/max character limits.
    6. Merges remaining micro-chunks in a post-processing pass.
    """
    if not text or not text.strip():
        return []
        
    sentences = split_into_sentences(text, max_sentence_len=max_chunk_size // 2)
    if not sentences:
        return []
    if len(sentences) == 1:
        return sentences

    # Load embedding model and encode sentences
    try:
        import numpy as np
        model = get_embedding_model()
        embeddings = model.encode(sentences, show_progress_bar=False)
    except Exception as e:
        print(f"!!! Semantic Chunking Error: {e}. Falling back to character chunking.")
        return split_text_into_chunks(text, max_chunk_size)

    # Calculate cosine distances (1 - cosine_similarity) between adjacent sentence embeddings
    distances = []
    for i in range(len(embeddings) - 1):
        v1 = embeddings[i]
        v2 = embeddings[i+1]
        dot = np.dot(v1, v2)
        n1 = np.linalg.norm(v1)
        n2 = np.linalg.norm(v2)
        similarity = dot / (n1 * n2) if n1 > 0 and n2 > 0 else 0.0
        distances.append(1.0 - similarity)

    # Calculate dynamic splitting threshold
    if distances:
        mean_dist = np.mean(distances)
        std_dist = np.std(distances)
        threshold = mean_dist + k * std_dist
        print(f"--- Semantic Chunking Stats: Sentences={len(sentences)}, Distances={len(distances)}, MeanDist={mean_dist:.4f}, StdDist={std_dist:.4f}, Threshold={threshold:.4f} ---")
    else:
        threshold = 0.5

    # Run linear split scan
    chunks = []
    current_chunk_sentences = [sentences[0]]
    current_len = len(sentences[0])

    for i in range(len(sentences) - 1):
        sentence = sentences[i+1]
        distance = distances[i]
        
        would_exceed_max = (current_len + len(sentence) + 1 > max_chunk_size)
        is_semantic_split = (distance > threshold)
        
        if would_exceed_max or is_semantic_split:
            # If the current chunk is long enough, split here.
            # If it would exceed max, we HAVE to split regardless of size.
            if would_exceed_max or (current_len >= min_chunk_size):
                chunks.append(" ".join(current_chunk_sentences))
                current_chunk_sentences = [sentence]
                current_len = len(sentence)
                continue
                
        current_chunk_sentences.append(sentence)
        current_len += len(sentence) + 1

    if current_chunk_sentences:
        chunks.append(" ".join(current_chunk_sentences))

    # Post-processing pass: merge micro-chunks that are below min_chunk_size
    merged_chunks = []
    temp_chunk = ""
    for chunk in chunks:
        if not temp_chunk:
            temp_chunk = chunk
        elif len(temp_chunk) + len(chunk) + 1 <= max_chunk_size:
            if len(temp_chunk) < min_chunk_size:
                temp_chunk += " " + chunk
            else:
                merged_chunks.append(temp_chunk)
                temp_chunk = chunk
        else:
            merged_chunks.append(temp_chunk)
            temp_chunk = chunk
            
    if temp_chunk:
        merged_chunks.append(temp_chunk)

    print(f"--- Semantic Chunking complete: Generated {len(merged_chunks)} chunks (reduced from raw sentences) ---")
    return merged_chunks

def split_text_into_chunks(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list:
    """
    Splits text into chunks of maximum size `chunk_size` characters, 
    preserving paragraph and sentence boundaries as much as possible,
    with an overlap of `overlap` characters.
    """
    if not text or not text.strip():
        return []
    
    # Normalize line endings
    text = text.replace("\r\n", "\n")
    
    # 1. Split into paragraphs
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = []
    current_length = 0
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
            
        # Check if adding this paragraph fits in the chunk size
        additional_len = 2 if current_chunk else 0
        if current_length + len(para) + additional_len <= chunk_size:
            current_chunk.append(para)
            current_length += len(para) + additional_len
        else:
            # If paragraph itself is larger than chunk_size, split by sentences
            if len(para) > chunk_size:
                # Flush existing chunk content first
                if current_chunk:
                    chunks.append("\n\n".join(current_chunk))
                    current_chunk = []
                    current_length = 0
                
                # Split paragraph by sentences
                sentences = re.split(r'(?<=[.!?])\s+', para)
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                        
                    additional_sent_len = 1 if current_chunk else 0
                    if current_length + len(sentence) + additional_sent_len <= chunk_size:
                        current_chunk.append(sentence)
                        current_length += len(sentence) + additional_sent_len
                    else:
                        # If a single sentence is larger than chunk_size, split by characters
                        if len(sentence) > chunk_size:
                            if current_chunk:
                                chunks.append(" ".join(current_chunk))
                                current_chunk = []
                                current_length = 0
                            
                            # Split by characters
                            for i in range(0, len(sentence), chunk_size - overlap):
                                chunk_slice = sentence[i:i + chunk_size]
                                if chunk_slice.strip():
                                    chunks.append(chunk_slice)
                        else:
                            # Save current chunk and start a new one with the sentence
                            chunks.append(" ".join(current_chunk))
                            current_chunk = [sentence]
                            current_length = len(sentence)
            else:
                # Save current chunk
                if current_chunk:
                    chunks.append("\n\n".join(current_chunk))
                
                # Setup next chunk with overlap from the end of the previous chunk if possible
                overlap_text = []
                overlap_len = 0
                if current_chunk:
                    # Collect previous paragraphs backwards to fill the overlap budget
                    for p in reversed(current_chunk):
                        if overlap_len + len(p) + (2 if overlap_text else 0) <= overlap:
                            overlap_text.insert(0, p)
                            overlap_len += len(p) + (2 if len(overlap_text) > 1 else 0)
                        else:
                            break
                
                current_chunk = overlap_text + [para]
                current_length = sum(len(p) for p in current_chunk) + (2 * (len(current_chunk) - 1))
                
    if current_chunk:
        chunks.append("\n\n".join(current_chunk))
        
    return chunks