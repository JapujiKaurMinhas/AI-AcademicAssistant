# Centralized Configuration for Document Intelligence Pipeline

# Conservative token budget for Groq models
MAX_INPUT_TOKENS = 3000       # Target budget for individual prompt input tokens
MAX_OUTPUT_TOKENS = 1000      # Target budget for individual LLM responses

# Text chunking specifications
CHUNK_SIZE = 8000             # Text chunk size in characters (approx. 2000-2300 tokens)
CHUNK_OVERLAP = 800           # Overlap in characters (approx. 200 tokens)
MAX_DOCUMENT_CHUNKS = 8       # Max chunks to process in order to control API load and rate limits

# API rate limit safeguards
REQUEST_DELAY = 1.5           # Time in seconds to pause between sequential API requests
MAX_RETRIES = 3               # Number of retries on Groq Rate Limit / transient errors

# Groq LLM model identifiers (adapted to account-specific active models)
LLM_MODEL_INTEL = "groq/compound-mini"       # Fast model for summarization/intel
LLM_MODEL_VERSATILE = "groq/compound"        # Strong model for detailed explanations, quizzes, etc.
